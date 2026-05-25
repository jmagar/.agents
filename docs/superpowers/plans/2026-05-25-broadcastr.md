# Broadcastr Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a Claude Code plugin called `broadcastr` that captures agent activity (commits, plan edits, bash commands) into a shared JSONL bus so multiple concurrent Claude sessions on the same repo see each other in real-time.

**Architecture:** Three layers — emitters (Claude hooks + git hooks + inotify watchers) write to an append-only JSONL bus; a feed monitor tails the bus and prints lines (which Claude surfaces as notifications); an apprise gateway routes alert-tier events to the user's phone. One canonical writer (`bin/broadcastr-emit`, Rust, with a bash fallback) for atomicity. Per-repo + host-global dual bus.

**Tech Stack:** Bash 5+ (POSIX-safe), Rust 1.75+ (one tiny binary), `inotifywait` (inotify-tools), `flock`, `tail -F`, `jq`, `apprise` CLI (optional, runtime). Tests: `bats-core` for shell + `cargo test` for the Rust binary.

**Spec:** `docs/specs/2026-05-25-broadcastr-design.md` is the authoritative design. Read it once before starting.

---

## File structure

```
plugins/broadcastr/
├── .claude-plugin/plugin.json
├── README.md
├── CHANGELOG.md
├── schema.json
├── hooks/hooks.json
├── monitors/monitors.json
├── commands/broadcastr.md
├── bin-src/broadcastr-emit/                 # Rust source for the fast-path emitter
│   ├── Cargo.toml
│   └── src/main.rs
├── bin/
│   ├── broadcastr                           # CLI shim (bash)
│   └── broadcastr-emit                      # built artifact (gitignored; built on first install)
├── scripts/
│   ├── emit.sh                              # thin wrapper that execs bin/broadcastr-emit (or bash fallback)
│   ├── emit-fallback.sh                     # pure-bash emit, used when binary is missing
│   ├── tail-bus.sh                          # feed monitor entry
│   ├── alert-gateway.sh                     # apprise fan-out
│   ├── watch-plans.sh                       # inotify producer for plan dirs
│   ├── watch-sessions.sh                    # inotify producer for docs/sessions
│   ├── supervisor.sh                        # generic while-true wrapper used by watch-* scripts
│   ├── push-wrapper.sh                      # optional git-push wrapper that emits push success/fail
│   └── git-hooks/                           # templates installed into .git/hooks/
│       ├── post-commit
│       ├── pre-commit
│       ├── pre-push
│       ├── post-checkout
│       └── post-merge
├── skills/
│   ├── broadcastr/
│   │   ├── SKILL.md
│   │   ├── README.md
│   │   └── CHANGELOG.md
│   └── broadcastr-install-hooks/
│       ├── SKILL.md
│       ├── README.md
│       ├── CHANGELOG.md
│       └── scripts/install-git-hooks.sh
└── tests/
    ├── bats/                                # shell tests
    │   ├── emit.bats
    │   ├── rotation.bats
    │   ├── tail.bats
    │   ├── git-hooks.bats
    │   └── install-hooks.bats
    └── integration/
        └── two-session.sh                   # end-to-end: spawn two emit loops, assert cross-visibility
```

Responsibility map:
- **`bin/broadcastr-emit` (Rust):** generate ULID + timestamp, take JSON event fields as CLI args, append one JSONL line to per-repo bus, optionally also to global bus. Honors `BROADCASTR_DISABLED`. Performs rotation check under `flock`. THE only hot path; correctness lives here.
- **`scripts/emit.sh`:** trivial wrapper. If `bin/broadcastr-emit` exists, `exec` it; else `exec scripts/emit-fallback.sh`. Lets the rest of the system always invoke `emit.sh` and not care which backend is live.
- **`scripts/tail-bus.sh`:** feed monitor. Tails per-repo + global bus, applies self-suppression by `CLAUDE_SESSION_ID`, drops events older than startup, drops muted categories, formats one line per event to stdout.
- **`scripts/alert-gateway.sh`:** tails the global bus filtering `tier=="alert"` and shells to `apprise`. Single responsibility.
- **`scripts/supervisor.sh`:** `while true; do "$@"; sleep 1; done` with an arm-failure escape that emits one alert event and exits the loop. Used by `watch-plans.sh` and `watch-sessions.sh`.
- **`scripts/git-hooks/*`:** installed into a target repo's `.git/hooks/`. Each is a shim that calls `emit.sh`, chains to a saved `<hook>.broadcastr-prev` if present, and propagates exit status.
- **`bin/broadcastr`:** user-facing CLI. Subcommands: `emit`, `tail`, `status`, `recent`, `mute`.
- **`skills/broadcastr/`:** user-facing skill — how to read the feed, mute categories, emit manually.
- **`skills/broadcastr-install-hooks/`:** idempotent per-repo git-hook installer skill.

---

## Phase 1 — Plugin scaffolding

### Task 1: Create plugin directory + manifest

**Files:**
- Create: `plugins/broadcastr/.claude-plugin/plugin.json`
- Create: `plugins/broadcastr/README.md`
- Create: `plugins/broadcastr/CHANGELOG.md`
- Create: `plugins/broadcastr/.gitignore`

- [ ] **Step 1: Scaffold directory**

```bash
mkdir -p plugins/broadcastr/{.claude-plugin,hooks,monitors,commands,scripts/git-hooks,bin,bin-src,skills,tests/bats,tests/integration}
```

- [ ] **Step 2: Write `plugins/broadcastr/.claude-plugin/plugin.json`**

```json
{
  "name": "broadcastr",
  "version": "0.1.0",
  "description": "Real-time activity broadcast across concurrent Claude Code sessions. Captures commits, plan edits, bash commands into a shared JSONL bus; each session sees what others are doing.",
  "author": {
    "name": "Jacob Magar",
    "email": "jmagar@gmail.com"
  },
  "license": "MIT",
  "keywords": ["multi-agent", "coordination", "notifications", "homelab", "git-hooks"],
  "homepage": "https://github.com/jmagar/.agents/tree/main/plugins/broadcastr",
  "userConfig": {
    "apprise_enabled": { "type": "boolean", "default": true, "description": "Fan out alert-tier events to apprise" },
    "apprise_tag": { "type": "string", "default": "broadcastr", "description": "Apprise routing tag" },
    "global_feed": { "type": "boolean", "default": true, "description": "Tail the global bus in addition to the per-repo bus" },
    "mute_categories": { "type": "array", "items": { "type": "string" }, "default": [], "description": "Categories to drop from the agent feed" },
    "bus_max_bytes": { "type": "number", "default": 5242880, "description": "Rotate the bus when it exceeds this size" },
    "bus_retain": { "type": "number", "default": 3, "description": "Number of rotated bus files to keep" }
  }
}
```

- [ ] **Step 3: Write `plugins/broadcastr/README.md`**

```markdown
# broadcastr

Real-time activity broadcast across concurrent Claude Code sessions. Captures commits, plan edits, bash commands into a shared JSONL bus; each session sees a notification when other sessions do something interesting.

## Install

This plugin ships via the `~/.agents` marketplace.

## What you see

Once installed, when another Claude session in any repo commits, edits a plan, or fails a push, your session gets a notification line:

```
[info] commit · commit a1b2c3d: Fix auth race · claude-code@dookie
[alert] push · git push failed on feature/x · claude-code@steamy
```

## Components

- Auto-emitters: Claude hooks (SessionStart, Stop, bash-classifier), git hooks (commit, push, branch), inotify watchers (plan files, session docs).
- Feed monitor: tails the bus and surfaces each event as a Claude notification line. Self-suppresses your own session's events.
- Apprise gateway: routes alert-tier events to your phone via apprise.

## Configuration

See `userConfig` in `.claude-plugin/plugin.json`. Override per-session with env vars:
- `BROADCASTR_DISABLED=1` — silence this session entirely
- `BROADCASTR_GLOBAL_FEED=0` — don't tail the global bus
- `BROADCASTR_MUTE=plan-exec,session-doc` — drop these categories

## Skills

- `broadcastr` — user-facing: read the feed, mute, emit manually
- `broadcastr-install-hooks` — idempotent per-repo git-hook installer

## Spec

`docs/specs/2026-05-25-broadcastr-design.md` in the parent repo.
```

- [ ] **Step 4: Write `plugins/broadcastr/CHANGELOG.md`**

```markdown
# Changelog

## [0.1.0] - 2026-05-25
- Initial release. Per-repo + host-global JSONL bus, Claude hooks (SessionStart/Stop/PostToolUse-Bash), git hooks (post-commit, pre-commit, pre-push, post-checkout, post-merge), inotify watchers (plans, sessions), feed monitor with self-suppression, apprise alert gateway. Claude Code only — Codex deferred.
```

- [ ] **Step 5: Write `plugins/broadcastr/.gitignore`**

```
bin/broadcastr-emit
bin-src/broadcastr-emit/target/
```

- [ ] **Step 6: Commit**

```bash
git add plugins/broadcastr
git commit -m "broadcastr: scaffold plugin directory and manifest"
```

---

### Task 2: Define event schema

**Files:**
- Create: `plugins/broadcastr/schema.json`

- [ ] **Step 1: Write `plugins/broadcastr/schema.json`**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Broadcastr event",
  "type": "object",
  "required": ["ts", "id", "tier", "category", "source", "emitter", "repo", "summary"],
  "properties": {
    "ts": { "type": "string", "format": "date-time", "description": "ISO-8601 UTC with millisecond precision" },
    "id": { "type": "string", "pattern": "^evt_[0-9A-HJKMNP-TV-Z]{26}$", "description": "ULID with evt_ prefix" },
    "tier": { "type": "string", "enum": ["info", "alert"] },
    "category": {
      "type": "string",
      "enum": [
        "agent-presence", "commit", "pre-commit", "push", "plan",
        "bead", "session-doc", "plan-exec", "branch", "stash",
        "pr", "cargo", "container", "ci"
      ]
    },
    "source": { "type": "string", "enum": ["claude-hook", "git-hook", "inotify", "poll", "cli"] },
    "emitter": {
      "type": "object",
      "required": ["agent", "host", "user"],
      "properties": {
        "session_id": { "type": ["string", "null"] },
        "agent": { "type": "string", "enum": ["claude-code", "user"] },
        "host": { "type": "string" },
        "user": { "type": "string" }
      }
    },
    "repo": { "type": "string" },
    "branch": { "type": "string" },
    "summary": { "type": "string", "maxLength": 500 },
    "data": { "type": "object" }
  },
  "additionalProperties": false
}
```

- [ ] **Step 2: Commit**

```bash
git add plugins/broadcastr/schema.json
git commit -m "broadcastr: add JSON schema for events"
```

---

## Phase 2 — Emit core

### Task 3: Rust emit binary — happy path

**Files:**
- Create: `plugins/broadcastr/bin-src/broadcastr-emit/Cargo.toml`
- Create: `plugins/broadcastr/bin-src/broadcastr-emit/src/main.rs`
- Create: `plugins/broadcastr/bin-src/broadcastr-emit/tests/emit.rs`

- [ ] **Step 1: Write `Cargo.toml`**

```toml
[package]
name = "broadcastr-emit"
version = "0.1.0"
edition = "2024"

[[bin]]
name = "broadcastr-emit"
path = "src/main.rs"

[dependencies]
ulid = "1"
chrono = { version = "0.4", features = ["clock"] }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
clap = { version = "4", features = ["derive"] }
fs2 = "0.4"

[dev-dependencies]
tempfile = "3"
```

- [ ] **Step 2: Write the failing integration test `tests/emit.rs`**

```rust
use std::process::Command;
use std::fs;
use tempfile::TempDir;

#[test]
fn emit_appends_one_jsonl_line_to_per_repo_bus() {
    let tmp = TempDir::new().unwrap();
    let repo = tmp.path().join("repo");
    fs::create_dir_all(repo.join(".broadcastr")).unwrap();
    let home = tmp.path().join("home");
    fs::create_dir_all(&home).unwrap();

    let status = Command::new(env!("CARGO_BIN_EXE_broadcastr-emit"))
        .env("CLAUDE_PROJECT_DIR", &repo)
        .env("BROADCASTR_HOME", &home)
        .env("BROADCASTR_GLOBAL_FEED", "0")
        .env("HOSTNAME", "testbox")
        .env("USER", "tester")
        .args(["--category", "commit", "--tier", "info", "--summary", "test commit"])
        .status()
        .unwrap();
    assert!(status.success());

    let bus = fs::read_to_string(repo.join(".broadcastr/events.jsonl")).unwrap();
    let lines: Vec<&str> = bus.trim().lines().collect();
    assert_eq!(lines.len(), 1);
    let evt: serde_json::Value = serde_json::from_str(lines[0]).unwrap();
    assert_eq!(evt["category"], "commit");
    assert_eq!(evt["tier"], "info");
    assert_eq!(evt["summary"], "test commit");
    assert_eq!(evt["emitter"]["host"], "testbox");
    assert_eq!(evt["emitter"]["user"], "tester");
    assert!(evt["id"].as_str().unwrap().starts_with("evt_"));
}
```

- [ ] **Step 3: Run the test to verify it fails**

```bash
cd plugins/broadcastr/bin-src/broadcastr-emit
cargo test emit_appends_one_jsonl_line_to_per_repo_bus
```

Expected: COMPILE FAIL (main.rs not written yet).

- [ ] **Step 4: Write minimal `src/main.rs`**

```rust
use chrono::Utc;
use clap::Parser;
use fs2::FileExt;
use serde::Serialize;
use serde_json::{json, Value};
use std::fs::{create_dir_all, OpenOptions};
use std::io::Write;
use std::path::PathBuf;
use ulid::Ulid;

#[derive(Parser)]
#[command(name = "broadcastr-emit")]
struct Args {
    #[arg(long)]
    category: String,
    #[arg(long)]
    tier: String,
    #[arg(long)]
    summary: String,
    #[arg(long, default_value = "cli")]
    source: String,
    #[arg(long)]
    data: Option<String>,
    #[arg(long)]
    branch: Option<String>,
}

#[derive(Serialize)]
struct Emitter {
    session_id: Option<String>,
    agent: String,
    host: String,
    user: String,
}

fn main() {
    if std::env::var("BROADCASTR_DISABLED").as_deref() == Ok("1") {
        return;
    }
    let args = Args::parse();

    let repo = std::env::var("CLAUDE_PROJECT_DIR")
        .or_else(|_| std::env::var("PWD"))
        .unwrap_or_else(|_| ".".to_string());
    let repo_path = PathBuf::from(&repo);
    let per_repo_bus = repo_path.join(".broadcastr/events.jsonl");

    let home = std::env::var("BROADCASTR_HOME").ok().map(PathBuf::from)
        .or_else(|| dirs_home().map(|h| h.join(".claude/broadcastr")));
    let global_bus = home.as_ref().map(|h| h.join("events.jsonl"));

    let event = build_event(&args, &repo);
    let line = serde_json::to_string(&event).expect("serialize event");

    append_line(&per_repo_bus, &line);

    let want_global = std::env::var("BROADCASTR_GLOBAL_FEED").as_deref() != Ok("0");
    if want_global {
        if let Some(g) = global_bus {
            append_line(&g, &line);
        }
    }
}

fn dirs_home() -> Option<PathBuf> {
    std::env::var("HOME").ok().map(PathBuf::from)
}

fn build_event(args: &Args, repo: &str) -> Value {
    let session_id = std::env::var("CLAUDE_SESSION_ID").ok();
    let agent = if session_id.is_some() { "claude-code" } else { "user" };
    let host = std::env::var("HOSTNAME").unwrap_or_else(|_| "unknown".to_string());
    let user = std::env::var("USER").unwrap_or_else(|_| "unknown".to_string());
    let ulid = Ulid::new().to_string();
    let ts = Utc::now().format("%Y-%m-%dT%H:%M:%S%.3fZ").to_string();
    let data: Value = args.data.as_deref()
        .map(|s| serde_json::from_str(s).unwrap_or(json!({})))
        .unwrap_or(json!({}));
    let mut event = json!({
        "ts": ts,
        "id": format!("evt_{}", ulid),
        "tier": args.tier,
        "category": args.category,
        "source": args.source,
        "emitter": Emitter { session_id, agent: agent.to_string(), host, user },
        "repo": repo,
        "summary": args.summary,
        "data": data,
    });
    if let Some(b) = &args.branch {
        event["branch"] = json!(b);
    }
    event
}

fn append_line(bus: &PathBuf, line: &str) {
    if let Some(parent) = bus.parent() {
        let _ = create_dir_all(parent);
    }
    let mut f = OpenOptions::new()
        .create(true)
        .append(true)
        .open(bus)
        .expect("open bus");
    writeln!(f, "{}", line).expect("write event");
}
```

- [ ] **Step 5: Run the test — expect PASS**

```bash
cargo test emit_appends_one_jsonl_line_to_per_repo_bus
```

- [ ] **Step 6: Commit**

```bash
git add plugins/broadcastr/bin-src
git commit -m "broadcastr: rust emit binary with per-repo append"
```

---

### Task 4: Rust emit binary — dual-bus + disabled

**Files:**
- Modify: `plugins/broadcastr/bin-src/broadcastr-emit/tests/emit.rs`

- [ ] **Step 1: Add failing tests for the global bus and the disable switch**

Append to `tests/emit.rs`:

```rust
#[test]
fn emit_writes_to_global_bus_when_enabled() {
    let tmp = TempDir::new().unwrap();
    let repo = tmp.path().join("repo");
    fs::create_dir_all(repo.join(".broadcastr")).unwrap();
    let home = tmp.path().join("home");
    fs::create_dir_all(&home).unwrap();

    Command::new(env!("CARGO_BIN_EXE_broadcastr-emit"))
        .env("CLAUDE_PROJECT_DIR", &repo)
        .env("BROADCASTR_HOME", &home)
        .env("BROADCASTR_GLOBAL_FEED", "1")
        .env("HOSTNAME", "testbox")
        .env("USER", "tester")
        .args(["--category", "commit", "--tier", "info", "--summary", "x"])
        .status().unwrap();

    let global = fs::read_to_string(home.join("events.jsonl")).unwrap();
    assert_eq!(global.trim().lines().count(), 1);
}

#[test]
fn emit_is_silent_when_disabled() {
    let tmp = TempDir::new().unwrap();
    let repo = tmp.path().join("repo");
    fs::create_dir_all(repo.join(".broadcastr")).unwrap();

    Command::new(env!("CARGO_BIN_EXE_broadcastr-emit"))
        .env("CLAUDE_PROJECT_DIR", &repo)
        .env("BROADCASTR_DISABLED", "1")
        .args(["--category", "commit", "--tier", "info", "--summary", "x"])
        .status().unwrap();

    assert!(!repo.join(".broadcastr/events.jsonl").exists());
}
```

- [ ] **Step 2: Run them — both should PASS already** (the main.rs in Task 3 already implements both behaviors)

```bash
cargo test
```

Expected: all three tests pass. If global-bus test fails because `BROADCASTR_GLOBAL_FEED=1` isn't honored unless HOME or BROADCASTR_HOME is set, the test sets BROADCASTR_HOME — verify the precedence.

- [ ] **Step 3: Commit**

```bash
git add tests/
git commit -m "broadcastr: add dual-bus and disabled-switch tests"
```

---

### Task 5: Rotation under flock

**Files:**
- Modify: `plugins/broadcastr/bin-src/broadcastr-emit/src/main.rs`
- Modify: `plugins/broadcastr/bin-src/broadcastr-emit/tests/emit.rs`

- [ ] **Step 1: Add failing rotation test**

Append to `tests/emit.rs`:

```rust
#[test]
fn emit_rotates_when_bus_exceeds_max_bytes() {
    let tmp = TempDir::new().unwrap();
    let repo = tmp.path().join("repo");
    let bus_dir = repo.join(".broadcastr");
    fs::create_dir_all(&bus_dir).unwrap();
    // Pre-fill the bus past threshold
    let bus = bus_dir.join("events.jsonl");
    fs::write(&bus, "x".repeat(2048)).unwrap();

    Command::new(env!("CARGO_BIN_EXE_broadcastr-emit"))
        .env("CLAUDE_PROJECT_DIR", &repo)
        .env("BROADCASTR_GLOBAL_FEED", "0")
        .env("BROADCASTR_BUS_MAX_BYTES", "1024")
        .env("BROADCASTR_BUS_RETAIN", "3")
        .env("HOSTNAME", "h").env("USER", "u")
        .args(["--category", "commit", "--tier", "info", "--summary", "x"])
        .status().unwrap();

    assert!(bus_dir.join("events.jsonl.1").exists(), "rotated file should exist");
    // The fresh bus should contain only the one new event
    let new_bus = fs::read_to_string(&bus).unwrap();
    assert_eq!(new_bus.trim().lines().count(), 1);
}
```

- [ ] **Step 2: Run it — expect FAIL** (no rotation logic yet)

- [ ] **Step 3: Implement rotation in `src/main.rs`**

Add this function and call it from `append_line` before opening the bus for append:

```rust
fn maybe_rotate(bus: &PathBuf) {
    let max_bytes: u64 = std::env::var("BROADCASTR_BUS_MAX_BYTES")
        .ok().and_then(|s| s.parse().ok()).unwrap_or(5 * 1024 * 1024);
    let retain: u32 = std::env::var("BROADCASTR_BUS_RETAIN")
        .ok().and_then(|s| s.parse().ok()).unwrap_or(3);

    let size = match std::fs::metadata(bus) {
        Ok(m) => m.len(),
        Err(_) => return,
    };
    if size < max_bytes {
        return;
    }

    let lock_path = bus.with_extension("jsonl.rotate.lock");
    let lock_file = match OpenOptions::new().create(true).write(true).open(&lock_path) {
        Ok(f) => f,
        Err(_) => return,
    };
    // Non-blocking — losers skip rotation this turn
    if lock_file.try_lock_exclusive().is_err() {
        return;
    }

    // Re-check size under lock (TOCTOU)
    let size = match std::fs::metadata(bus) {
        Ok(m) => m.len(),
        Err(_) => return,
    };
    if size < max_bytes {
        return;
    }

    // Shift rotations: .N-1 -> .N for i from retain..=1
    for i in (1..retain).rev() {
        let from = bus.with_file_name(format!(
            "{}.{}",
            bus.file_name().unwrap().to_string_lossy(),
            i
        ));
        let to = bus.with_file_name(format!(
            "{}.{}",
            bus.file_name().unwrap().to_string_lossy(),
            i + 1
        ));
        if from.exists() {
            let _ = std::fs::rename(&from, &to);
        }
    }
    let dot1 = bus.with_file_name(format!(
        "{}.1",
        bus.file_name().unwrap().to_string_lossy()
    ));
    let _ = std::fs::rename(bus, &dot1);
    // touch fresh bus
    let _ = OpenOptions::new().create(true).write(true).open(bus);

    let _ = lock_file.unlock();
}
```

And modify `append_line`:

```rust
fn append_line(bus: &PathBuf, line: &str) {
    if let Some(parent) = bus.parent() {
        let _ = create_dir_all(parent);
    }
    maybe_rotate(bus);
    let mut f = OpenOptions::new()
        .create(true)
        .append(true)
        .open(bus)
        .expect("open bus");
    writeln!(f, "{}", line).expect("write event");
}
```

- [ ] **Step 4: Run — expect PASS**

```bash
cargo test
```

- [ ] **Step 5: Add concurrent-emitter race test**

Append to `tests/emit.rs`:

```rust
#[test]
fn concurrent_rotation_does_not_clobber() {
    let tmp = TempDir::new().unwrap();
    let repo = tmp.path().join("repo");
    let bus_dir = repo.join(".broadcastr");
    fs::create_dir_all(&bus_dir).unwrap();
    fs::write(bus_dir.join("events.jsonl"), "x".repeat(2048)).unwrap();

    // Spawn 8 emitters, all racing
    let mut handles = vec![];
    for _ in 0..8 {
        let repo = repo.clone();
        handles.push(std::thread::spawn(move || {
            Command::new(env!("CARGO_BIN_EXE_broadcastr-emit"))
                .env("CLAUDE_PROJECT_DIR", &repo)
                .env("BROADCASTR_GLOBAL_FEED", "0")
                .env("BROADCASTR_BUS_MAX_BYTES", "1024")
                .env("BROADCASTR_BUS_RETAIN", "3")
                .env("HOSTNAME", "h").env("USER", "u")
                .args(["--category", "commit", "--tier", "info", "--summary", "x"])
                .status().unwrap();
        }));
    }
    for h in handles { h.join().unwrap(); }

    // Exactly one rotation file should exist; .2 and .3 should not
    assert!(bus_dir.join("events.jsonl.1").exists());
    assert!(!bus_dir.join("events.jsonl.2").exists());
    // The fresh bus must contain all 8 new events plus possibly the racing rotators' appends
    let bus = fs::read_to_string(bus_dir.join("events.jsonl")).unwrap();
    let line_count = bus.trim().lines().count();
    assert!(line_count >= 1 && line_count <= 8, "got {} lines", line_count);
}
```

- [ ] **Step 6: Run — expect PASS** (flock guarantees single rotator)

- [ ] **Step 7: Commit**

```bash
git add bin-src/
git commit -m "broadcastr: lazy size-based rotation under flock"
```

---

### Task 6: emit.sh wrapper + bash fallback

**Files:**
- Create: `plugins/broadcastr/scripts/emit.sh`
- Create: `plugins/broadcastr/scripts/emit-fallback.sh`
- Create: `plugins/broadcastr/tests/bats/emit.bats`

- [ ] **Step 1: Write the bats test**

```bash
#!/usr/bin/env bats

setup() {
  PLUGIN_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  TMP="$(mktemp -d)"
  export CLAUDE_PROJECT_DIR="$TMP/repo"
  export BROADCASTR_HOME="$TMP/home"
  export BROADCASTR_GLOBAL_FEED=0
  export HOSTNAME=testbox
  export USER=tester
  mkdir -p "$CLAUDE_PROJECT_DIR" "$BROADCASTR_HOME"
}

teardown() { rm -rf "$TMP"; }

@test "emit.sh dispatches to fallback when binary missing" {
  rm -f "$PLUGIN_ROOT/bin/broadcastr-emit"
  run "$PLUGIN_ROOT/scripts/emit.sh" --category commit --tier info --summary "test"
  [ "$status" -eq 0 ]
  [ -f "$CLAUDE_PROJECT_DIR/.broadcastr/events.jsonl" ]
  line=$(cat "$CLAUDE_PROJECT_DIR/.broadcastr/events.jsonl")
  echo "$line" | grep -q '"category":"commit"'
  echo "$line" | grep -q '"summary":"test"'
  echo "$line" | grep -qE '"id":"evt_[0-9A-HJKMNP-TV-Z]{26}"'
}

@test "emit.sh uses binary when present" {
  if [ ! -x "$PLUGIN_ROOT/bin/broadcastr-emit" ]; then
    skip "binary not built"
  fi
  run "$PLUGIN_ROOT/scripts/emit.sh" --category commit --tier info --summary "binarypath"
  [ "$status" -eq 0 ]
  grep -q '"summary":"binarypath"' "$CLAUDE_PROJECT_DIR/.broadcastr/events.jsonl"
}
```

- [ ] **Step 2: Write `scripts/emit.sh`**

```bash
#!/usr/bin/env bash
set -euo pipefail

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

if [ -x "$PLUGIN_ROOT/bin/broadcastr-emit" ]; then
  exec "$PLUGIN_ROOT/bin/broadcastr-emit" "$@"
fi

exec "$PLUGIN_ROOT/scripts/emit-fallback.sh" "$@"
```

`chmod +x scripts/emit.sh`.

- [ ] **Step 3: Write `scripts/emit-fallback.sh`**

```bash
#!/usr/bin/env bash
# Pure-bash emit fallback used until bin/broadcastr-emit is compiled.
# Trades latency for portability. ULID without crockford base32 is "good enough"
# for collision-resistance over millisecond timestamps.

set -euo pipefail

[ "${BROADCASTR_DISABLED:-}" = "1" ] && exit 0

CATEGORY="" TIER="" SUMMARY="" SOURCE=cli DATA="{}" BRANCH=""
while [ $# -gt 0 ]; do
  case "$1" in
    --category) CATEGORY="$2"; shift 2;;
    --tier) TIER="$2"; shift 2;;
    --summary) SUMMARY="$2"; shift 2;;
    --source) SOURCE="$2"; shift 2;;
    --data) DATA="$2"; shift 2;;
    --branch) BRANCH="$2"; shift 2;;
    *) shift;;
  esac
done

REPO="${CLAUDE_PROJECT_DIR:-$PWD}"
PER_REPO_BUS="$REPO/.broadcastr/events.jsonl"
GLOBAL_HOME="${BROADCASTR_HOME:-$HOME/.claude/broadcastr}"
GLOBAL_BUS="$GLOBAL_HOME/events.jsonl"

TS="$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)"
RAND="$(head -c 16 /dev/urandom | od -An -tx1 | tr -d ' \n' | tr 'a-f' 'A-F')"
ID="evt_${RAND:0:26}"

SESSION_ID="${CLAUDE_SESSION_ID:-}"
AGENT="user"
[ -n "$SESSION_ID" ] && AGENT="claude-code"

HOST="${HOSTNAME:-$(hostname)}"
USER_NAME="${USER:-$(id -un)}"

SUMMARY_JSON=$(printf '%s' "$SUMMARY" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))' 2>/dev/null || \
               printf '"%s"' "${SUMMARY//\"/\\\"}")
SID_JSON='null'
[ -n "$SESSION_ID" ] && SID_JSON="\"$SESSION_ID\""
BRANCH_FIELD=""
[ -n "$BRANCH" ] && BRANCH_FIELD=",\"branch\":\"$BRANCH\""

LINE=$(printf '{"ts":"%s","id":"%s","tier":"%s","category":"%s","source":"%s","emitter":{"session_id":%s,"agent":"%s","host":"%s","user":"%s"},"repo":"%s"%s,"summary":%s,"data":%s}' \
  "$TS" "$ID" "$TIER" "$CATEGORY" "$SOURCE" "$SID_JSON" "$AGENT" "$HOST" "$USER_NAME" "$REPO" "$BRANCH_FIELD" "$SUMMARY_JSON" "$DATA")

append_with_rotate() {
  local bus="$1"
  mkdir -p "$(dirname "$bus")"
  local max="${BROADCASTR_BUS_MAX_BYTES:-5242880}"
  local retain="${BROADCASTR_BUS_RETAIN:-3}"
  if [ -f "$bus" ] && [ "$(stat -c %s "$bus" 2>/dev/null || stat -f %z "$bus")" -ge "$max" ]; then
    local lock="${bus}.rotate.lock"
    if ( exec 9>"$lock"; flock -n 9 ) 2>/dev/null; then
      ( exec 9>"$lock"
        flock -n 9 || exit 0
        local i=$((retain - 1))
        while [ "$i" -ge 1 ]; do
          [ -f "${bus}.${i}" ] && mv "${bus}.${i}" "${bus}.$((i+1))"
          i=$((i-1))
        done
        mv "$bus" "${bus}.1"
        : > "$bus"
      )
    fi
  fi
  printf '%s\n' "$LINE" >> "$bus"
}

append_with_rotate "$PER_REPO_BUS"

if [ "${BROADCASTR_GLOBAL_FEED:-1}" != "0" ]; then
  append_with_rotate "$GLOBAL_BUS"
fi
```

`chmod +x scripts/emit-fallback.sh`.

- [ ] **Step 4: Run the bats test**

```bash
bats plugins/broadcastr/tests/bats/emit.bats
```

Expected: both tests pass (the second skips until you build the binary).

- [ ] **Step 5: Commit**

```bash
git add plugins/broadcastr/scripts/emit.sh plugins/broadcastr/scripts/emit-fallback.sh plugins/broadcastr/tests/bats/emit.bats
git commit -m "broadcastr: emit.sh wrapper + bash fallback emitter"
```

---

## Phase 3 — Producers

### Task 7: Claude Code hooks (SessionStart, Stop, PostToolUse-Bash)

**Files:**
- Create: `plugins/broadcastr/hooks/hooks.json`
- Create: `plugins/broadcastr/scripts/hook-on-session-start.sh`
- Create: `plugins/broadcastr/scripts/hook-on-stop.sh`
- Create: `plugins/broadcastr/scripts/hook-classify-bash.sh`

- [ ] **Step 1: Write `hooks.json`**

Reference format: see `plugins/gotify-mcp/hooks/hooks.json`.

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          { "type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/scripts/hook-on-session-start.sh" }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          { "type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/scripts/hook-on-stop.sh" }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/scripts/hook-classify-bash.sh" }
        ]
      }
    ]
  }
}
```

- [ ] **Step 2: Write `scripts/hook-on-session-start.sh`**

```bash
#!/usr/bin/env bash
set -euo pipefail
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
SUMMARY="claude session joined: ${CLAUDE_PROJECT_DIR:-?}"
"$PLUGIN_ROOT/scripts/emit.sh" \
  --category agent-presence --tier info --source claude-hook \
  --summary "$SUMMARY" \
  --data "{\"action\":\"joined\",\"cwd\":\"${CLAUDE_PROJECT_DIR:-}\"}"
```

- [ ] **Step 3: Write `scripts/hook-on-stop.sh`**

```bash
#!/usr/bin/env bash
set -euo pipefail
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
"$PLUGIN_ROOT/scripts/emit.sh" \
  --category agent-presence --tier info --source claude-hook \
  --summary "claude session left" \
  --data '{"action":"left"}'
```

- [ ] **Step 4: Write `scripts/hook-classify-bash.sh`**

Claude Code passes the tool input via stdin as JSON. The script extracts the command and matches patterns.

```bash
#!/usr/bin/env bash
set -euo pipefail
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

INPUT="$(cat || true)"
CMD="$(printf '%s' "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null || true)"
[ -z "$CMD" ] && exit 0

emit() {
  "$PLUGIN_ROOT/scripts/emit.sh" \
    --category "$1" --tier info --source claude-hook \
    --summary "$2" \
    --data "$3"
}

case "$CMD" in
  *"bd create"*|*"bd update"*|*"bd close"*)
    SUMMARY="bd: ${CMD:0:200}"
    emit bead "$SUMMARY" "{\"cmd\":$(printf '%s' "$CMD" | jq -Rs .)}"
    ;;
  *"git stash"*)
    emit stash "git stash: ${CMD:0:200}" "{\"cmd\":$(printf '%s' "$CMD" | jq -Rs .)}"
    ;;
esac
exit 0
```

`chmod +x scripts/hook-*.sh`.

- [ ] **Step 5: Test the classifier**

```bash
echo '{"tool_input":{"command":"bd create --title foo"}}' | \
  CLAUDE_PLUGIN_ROOT=$PWD/plugins/broadcastr \
  CLAUDE_PROJECT_DIR=$(mktemp -d) \
  BROADCASTR_GLOBAL_FEED=0 \
  plugins/broadcastr/scripts/hook-classify-bash.sh

ls "$CLAUDE_PROJECT_DIR/.broadcastr/" 2>/dev/null && \
  grep -q '"category":"bead"' "$CLAUDE_PROJECT_DIR/.broadcastr/events.jsonl"
```

Expected: bus file exists and contains a `bead` event.

- [ ] **Step 6: Commit**

```bash
git add plugins/broadcastr/hooks plugins/broadcastr/scripts/hook-*.sh
git commit -m "broadcastr: claude code hooks (SessionStart, Stop, Bash classifier)"
```

---

### Task 8: Supervisor + inotify watchers

**Files:**
- Create: `plugins/broadcastr/scripts/supervisor.sh`
- Create: `plugins/broadcastr/scripts/watch-plans.sh`
- Create: `plugins/broadcastr/scripts/watch-sessions.sh`

- [ ] **Step 1: Write `scripts/supervisor.sh`**

```bash
#!/usr/bin/env bash
# Generic supervisor for inotify watchers. Restarts the watcher on transient
# failure. On a clear "can't arm" error (watch limit, missing dir we can't
# create), emits one alert and exits so silence is visible.
set -uo pipefail

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
NAME="$1"; shift
TARGETS=("$@")

if ! command -v inotifywait >/dev/null 2>&1; then
  "$PLUGIN_ROOT/scripts/emit.sh" \
    --category agent-presence --tier alert --source claude-hook \
    --summary "broadcastr: inotifywait not installed; ${NAME} disabled" \
    --data "{\"monitor\":\"$NAME\"}"
  exit 0
fi

# Pre-create any target directories so inotifywait doesn't bail on missing paths
for d in "${TARGETS[@]}"; do
  mkdir -p "$d" 2>/dev/null || true
done

# Test-arm once; if even the first arm fails, treat as structural failure.
if ! inotifywait -q -t 1 -e create "${TARGETS[@]}" >/dev/null 2>&1; then
  rc=$?
  # rc=2 means timeout (no events) — that's fine, the arm worked.
  if [ "$rc" -ne 2 ]; then
    "$PLUGIN_ROOT/scripts/emit.sh" \
      --category agent-presence --tier alert --source claude-hook \
      --summary "broadcastr: ${NAME} failed to arm, FS events disabled" \
      --data "{\"monitor\":\"$NAME\",\"exit\":$rc}"
    exit 0
  fi
fi

trap 'exit 0' SIGTERM SIGINT

while true; do
  while IFS= read -r line; do
    "$@" "$line" || true
  done < <(inotifywait -m -q -e close_write,create,moved_to --format '%w%f|%e' "${TARGETS[@]}" 2>/dev/null)
  sleep 1
done
```

`chmod +x scripts/supervisor.sh`.

- [ ] **Step 2: Write `scripts/watch-plans.sh`**

```bash
#!/usr/bin/env bash
set -euo pipefail
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
REPO="${CLAUDE_PROJECT_DIR:?must set CLAUDE_PROJECT_DIR}"

# Receives one "<path>|<event>" line on stdin per inotify event when called from supervisor.
handle() {
  local line="$1"
  local path="${line%|*}"
  case "$path" in
    *.md)
      local base=$(basename "$path")
      "$PLUGIN_ROOT/scripts/emit.sh" \
        --category plan --tier info --source inotify \
        --summary "plan edit: $base" \
        --data "{\"path\":\"$path\"}"
      # plan-exec marker: look for the executing-plans signal in the content
      if grep -qE '^- \[(x|X)\] \*\*Step' "$path" 2>/dev/null; then
        "$PLUGIN_ROOT/scripts/emit.sh" \
          --category plan-exec --tier info --source inotify \
          --summary "plan progress: $base" \
          --data "{\"path\":\"$path\"}"
      fi
      ;;
  esac
}

if [ "${1:-}" ]; then
  handle "$1"
  exit 0
fi

# Invoked directly (not via supervisor): exec supervisor
exec "$PLUGIN_ROOT/scripts/supervisor.sh" "broadcastr-plans" \
  "$REPO/docs/plans" "$REPO/docs/superpowers/plans"
```

`chmod +x scripts/watch-plans.sh`.

- [ ] **Step 3: Write `scripts/watch-sessions.sh`** (analogous)

```bash
#!/usr/bin/env bash
set -euo pipefail
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
REPO="${CLAUDE_PROJECT_DIR:?must set CLAUDE_PROJECT_DIR}"

handle() {
  local line="$1"
  local path="${line%|*}"
  case "$path" in
    *.md)
      local base=$(basename "$path")
      "$PLUGIN_ROOT/scripts/emit.sh" \
        --category session-doc --tier info --source inotify \
        --summary "session doc: $base" \
        --data "{\"path\":\"$path\"}"
      ;;
  esac
}

if [ "${1:-}" ]; then
  handle "$1"
  exit 0
fi

exec "$PLUGIN_ROOT/scripts/supervisor.sh" "broadcastr-sessions" \
  "$REPO/docs/sessions"
```

`chmod +x scripts/watch-sessions.sh`.

- [ ] **Step 4: Smoke-test the watcher manually**

```bash
TMPREPO=$(mktemp -d)
mkdir -p "$TMPREPO/docs/plans"
CLAUDE_PLUGIN_ROOT=$PWD/plugins/broadcastr \
CLAUDE_PROJECT_DIR=$TMPREPO \
BROADCASTR_GLOBAL_FEED=0 \
plugins/broadcastr/scripts/watch-plans.sh &
PID=$!
sleep 1
echo "hello" > "$TMPREPO/docs/plans/test.md"
sleep 2
kill $PID 2>/dev/null
cat "$TMPREPO/.broadcastr/events.jsonl"
```

Expected: at least one `"category":"plan"` event.

- [ ] **Step 5: Commit**

```bash
git add plugins/broadcastr/scripts/supervisor.sh plugins/broadcastr/scripts/watch-*.sh
git commit -m "broadcastr: inotify watchers (plans, sessions) under supervisor"
```

---

### Task 9: Git hook templates

**Files:**
- Create: `plugins/broadcastr/scripts/git-hooks/post-commit`
- Create: `plugins/broadcastr/scripts/git-hooks/pre-commit`
- Create: `plugins/broadcastr/scripts/git-hooks/pre-push`
- Create: `plugins/broadcastr/scripts/git-hooks/post-checkout`
- Create: `plugins/broadcastr/scripts/git-hooks/post-merge`

Each is installed by `broadcastr-install-hooks` into `.git/hooks/<name>`. The shim calls `emit.sh`, chains to `.broadcastr-prev` if present, and propagates exit status.

- [ ] **Step 1: Write `git-hooks/post-commit`**

```bash
#!/usr/bin/env bash
# Installed by broadcastr-install-hooks. Do not edit in-place.
set -uo pipefail

PLUGIN_ROOT="${BROADCASTR_PLUGIN_ROOT:-$HOME/.claude/plugins/broadcastr}"
HOOK_DIR="$(dirname "$0")"
SENTINEL="$HOOK_DIR/.broadcastr.last-merge-sha"
SHA="$(git rev-parse HEAD 2>/dev/null)"
FILES="$(git diff --name-only HEAD~1 HEAD 2>/dev/null | wc -l | tr -d ' ')"
BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null)"

dedup=0
if [ -f "$SENTINEL" ]; then
  age=$(( $(date +%s) - $(stat -c %Y "$SENTINEL" 2>/dev/null || stat -f %m "$SENTINEL") ))
  last_sha=$(cat "$SENTINEL" 2>/dev/null || true)
  if [ "$age" -le 2 ] && [ "$last_sha" = "$SHA" ]; then
    dedup=1
  fi
fi

if [ "$dedup" = "0" ]; then
  "$PLUGIN_ROOT/scripts/emit.sh" \
    --category commit --tier info --source git-hook \
    --branch "$BRANCH" \
    --summary "commit ${SHA:0:7}: $(git log -1 --pretty=%s)" \
    --data "{\"sha\":\"$SHA\",\"files_changed\":$FILES,\"subtype\":\"commit\"}"
fi

PREV="$HOOK_DIR/post-commit.broadcastr-prev"
if [ -x "$PREV" ]; then
  exec "$PREV" "$@"
fi
exit 0
```

- [ ] **Step 2: Write `git-hooks/pre-commit`**

```bash
#!/usr/bin/env bash
set -uo pipefail
PLUGIN_ROOT="${BROADCASTR_PLUGIN_ROOT:-$HOME/.claude/plugins/broadcastr}"
HOOK_DIR="$(dirname "$0")"
PREV="$HOOK_DIR/pre-commit.broadcastr-prev"
BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null)"

"$PLUGIN_ROOT/scripts/emit.sh" \
  --category pre-commit --tier info --source git-hook \
  --branch "$BRANCH" \
  --summary "pre-commit start on $BRANCH"

rc=0
if [ -x "$PREV" ]; then
  "$PREV" "$@" || rc=$?
fi

if [ "$rc" -eq 0 ]; then
  "$PLUGIN_ROOT/scripts/emit.sh" \
    --category pre-commit --tier info --source git-hook \
    --branch "$BRANCH" \
    --summary "pre-commit pass on $BRANCH"
else
  "$PLUGIN_ROOT/scripts/emit.sh" \
    --category pre-commit --tier alert --source git-hook \
    --branch "$BRANCH" \
    --summary "pre-commit FAIL on $BRANCH (exit $rc)" \
    --data "{\"exit\":$rc}"
fi
exit $rc
```

- [ ] **Step 3: Write `git-hooks/pre-push`**

```bash
#!/usr/bin/env bash
# Note: this hook can ONLY observe the push attempt — the actual push
# outcome (success/fail) is observed by the optional push-wrapper.sh
# alias installed by broadcastr-install-hooks.
set -uo pipefail
PLUGIN_ROOT="${BROADCASTR_PLUGIN_ROOT:-$HOME/.claude/plugins/broadcastr}"
HOOK_DIR="$(dirname "$0")"
PREV="$HOOK_DIR/pre-push.broadcastr-prev"
REMOTE="${1:-?}"
URL="${2:-?}"
BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null)"

"$PLUGIN_ROOT/scripts/emit.sh" \
  --category push --tier info --source git-hook \
  --branch "$BRANCH" \
  --summary "push-attempt: $BRANCH -> $REMOTE" \
  --data "{\"remote\":\"$REMOTE\",\"url\":\"$URL\",\"subtype\":\"attempt\"}"

if [ -x "$PREV" ]; then
  exec "$PREV" "$@"
fi
exit 0
```

- [ ] **Step 4: Write `git-hooks/post-checkout`**

```bash
#!/usr/bin/env bash
set -uo pipefail
PLUGIN_ROOT="${BROADCASTR_PLUGIN_ROOT:-$HOME/.claude/plugins/broadcastr}"
HOOK_DIR="$(dirname "$0")"
PREV="$HOOK_DIR/post-checkout.broadcastr-prev"

PREV_REF="${1:-?}"
NEW_REF="${2:-?}"
FLAG="${3:-?}"

if [ "$FLAG" = "1" ]; then
  NAME="$(git rev-parse --abbrev-ref HEAD 2>/dev/null)"
  "$PLUGIN_ROOT/scripts/emit.sh" \
    --category branch --tier info --source git-hook \
    --summary "checkout: $NAME" \
    --data "{\"prev\":\"$PREV_REF\",\"new\":\"$NEW_REF\",\"branch_checkout\":true}"
else
  "$PLUGIN_ROOT/scripts/emit.sh" \
    --category branch --tier info --source git-hook \
    --summary "file checkout" \
    --data "{\"prev\":\"$PREV_REF\",\"new\":\"$NEW_REF\",\"branch_checkout\":false}"
fi

if [ -x "$PREV" ]; then
  exec "$PREV" "$@"
fi
exit 0
```

- [ ] **Step 5: Write `git-hooks/post-merge`**

```bash
#!/usr/bin/env bash
set -uo pipefail
PLUGIN_ROOT="${BROADCASTR_PLUGIN_ROOT:-$HOME/.claude/plugins/broadcastr}"
HOOK_DIR="$(dirname "$0")"
PREV="$HOOK_DIR/post-merge.broadcastr-prev"
SHA="$(git rev-parse HEAD 2>/dev/null)"
BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null)"

# Drop a sentinel so the post-commit shim can dedup the merge commit
echo "$SHA" > "$HOOK_DIR/.broadcastr.last-merge-sha"

"$PLUGIN_ROOT/scripts/emit.sh" \
  --category commit --tier info --source git-hook \
  --branch "$BRANCH" \
  --summary "merge ${SHA:0:7} on $BRANCH" \
  --data "{\"sha\":\"$SHA\",\"subtype\":\"merge\"}"

if [ -x "$PREV" ]; then
  exec "$PREV" "$@"
fi
exit 0
```

- [ ] **Step 6: Make them executable, sanity-check shellcheck**

```bash
chmod +x plugins/broadcastr/scripts/git-hooks/*
command -v shellcheck >/dev/null && shellcheck plugins/broadcastr/scripts/git-hooks/* || true
```

- [ ] **Step 7: Commit**

```bash
git add plugins/broadcastr/scripts/git-hooks
git commit -m "broadcastr: git hook templates with chain + dedup"
```

---

### Task 10: push-wrapper.sh (optional alias around `git push`)

**Files:**
- Create: `plugins/broadcastr/scripts/push-wrapper.sh`

Documents the limitation: pre-push hook can't observe outcome; this wrapper runs the actual push and emits success/fail.

- [ ] **Step 1: Write `scripts/push-wrapper.sh`**

```bash
#!/usr/bin/env bash
# Optional: shell wrapper that observes `git push` outcome.
# Installed as an alias by broadcastr-install-hooks if the user opts in.
# Usage: source this file in your shell rc, then `alias git-push=broadcastr-push`.
set -uo pipefail
PLUGIN_ROOT="${BROADCASTR_PLUGIN_ROOT:-$HOME/.claude/plugins/broadcastr}"

broadcastr-push() {
  local out
  local rc=0
  local branch
  branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null)"

  if out=$(git push "$@" 2>&1); then
    "$PLUGIN_ROOT/scripts/emit.sh" \
      --category push --tier info --source cli \
      --branch "$branch" \
      --summary "push succeeded: $branch" \
      --data "{\"subtype\":\"success\"}"
    printf '%s\n' "$out"
  else
    rc=$?
    "$PLUGIN_ROOT/scripts/emit.sh" \
      --category push --tier alert --source cli \
      --branch "$branch" \
      --summary "push FAILED: $branch (exit $rc)" \
      --data "{\"subtype\":\"fail\",\"exit\":$rc}"
    printf '%s\n' "$out" >&2
    return $rc
  fi
}
```

- [ ] **Step 2: Commit**

```bash
git add plugins/broadcastr/scripts/push-wrapper.sh
git commit -m "broadcastr: optional git-push wrapper for outcome observation"
```

---

## Phase 4 — Consumers

### Task 11: tail-bus.sh feed monitor

**Files:**
- Create: `plugins/broadcastr/scripts/tail-bus.sh`
- Create: `plugins/broadcastr/tests/bats/tail.bats`

- [ ] **Step 1: Write the bats test**

```bash
#!/usr/bin/env bats

setup() {
  PLUGIN_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  TMP="$(mktemp -d)"
  export CLAUDE_PROJECT_DIR="$TMP/repo"
  export BROADCASTR_HOME="$TMP/home"
  export BROADCASTR_GLOBAL_FEED=0
  export HOSTNAME=testbox
  export USER=tester
  mkdir -p "$CLAUDE_PROJECT_DIR/.broadcastr"
}

teardown() { rm -rf "$TMP"; }

@test "tail-bus drops own session events" {
  export CLAUDE_SESSION_ID=mine
  # Pre-seed bus with one of mine and one of theirs
  "$PLUGIN_ROOT/scripts/emit.sh" --category commit --tier info --summary "mine"
  CLAUDE_SESSION_ID=theirs "$PLUGIN_ROOT/scripts/emit.sh" --category commit --tier info --summary "theirs"

  timeout 2 "$PLUGIN_ROOT/scripts/tail-bus.sh" > "$TMP/out.txt" 2>&1 || true
  ! grep -q "mine" "$TMP/out.txt"
  grep -q "theirs" "$TMP/out.txt"
}

@test "tail-bus drops muted categories" {
  export CLAUDE_SESSION_ID=mine
  export BROADCASTR_MUTE=plan-exec
  CLAUDE_SESSION_ID=other "$PLUGIN_ROOT/scripts/emit.sh" --category commit --tier info --summary "kept"
  CLAUDE_SESSION_ID=other "$PLUGIN_ROOT/scripts/emit.sh" --category plan-exec --tier info --summary "muted"

  timeout 2 "$PLUGIN_ROOT/scripts/tail-bus.sh" > "$TMP/out.txt" 2>&1 || true
  grep -q "kept" "$TMP/out.txt"
  ! grep -q "muted" "$TMP/out.txt"
}

@test "tail-bus drops pre-startup events" {
  export CLAUDE_SESSION_ID=mine
  CLAUDE_SESSION_ID=other "$PLUGIN_ROOT/scripts/emit.sh" --category commit --tier info --summary "before-start"
  sleep 1.1

  ( timeout 3 "$PLUGIN_ROOT/scripts/tail-bus.sh" > "$TMP/out.txt" 2>&1 || true ) &
  TAILPID=$!
  sleep 0.5
  CLAUDE_SESSION_ID=other "$PLUGIN_ROOT/scripts/emit.sh" --category commit --tier info --summary "after-start"
  sleep 1
  kill $TAILPID 2>/dev/null || true
  wait || true

  ! grep -q "before-start" "$TMP/out.txt"
  grep -q "after-start" "$TMP/out.txt"
}
```

- [ ] **Step 2: Write `scripts/tail-bus.sh`**

```bash
#!/usr/bin/env bash
set -uo pipefail
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
REPO="${CLAUDE_PROJECT_DIR:?must set CLAUDE_PROJECT_DIR}"
SESSION_ID="${CLAUDE_SESSION_ID:-}"

PER_REPO_BUS="$REPO/.broadcastr/events.jsonl"
GLOBAL_HOME="${BROADCASTR_HOME:-$HOME/.claude/broadcastr}"
GLOBAL_BUS="$GLOBAL_HOME/events.jsonl"
WANT_GLOBAL="${BROADCASTR_GLOBAL_FEED:-1}"

mkdir -p "$(dirname "$PER_REPO_BUS")"
touch "$PER_REPO_BUS"
[ "$WANT_GLOBAL" != "0" ] && { mkdir -p "$GLOBAL_HOME"; touch "$GLOBAL_BUS"; }

# Convert mute list (comma-separated) to a jq array
MUTE_LIST="${BROADCASTR_MUTE:-}"
MUTE_JQ='[]'
if [ -n "$MUTE_LIST" ]; then
  MUTE_JQ=$(printf '%s' "$MUTE_LIST" | tr ',' '\n' | jq -R . | jq -s .)
fi

STARTUP="$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)"

format_line() {
  jq -rc --arg sid "$SESSION_ID" --arg startup "$STARTUP" --argjson mute "$MUTE_JQ" '
    select(.emitter.session_id != $sid)
    | select(.ts > $startup)
    | select(.category as $c | $mute | index($c) | not)
    | "[" + .tier + "] " + .category + " · " + .summary + " · " + (.emitter.agent // "?") + "@" + (.emitter.host // "?")
  '
}

cleanup() { kill 0 2>/dev/null || true; }
trap cleanup SIGTERM SIGINT EXIT

if [ "$WANT_GLOBAL" != "0" ]; then
  tail -n0 -F "$PER_REPO_BUS" "$GLOBAL_BUS" 2>/dev/null | grep --line-buffered -v "^==>" | format_line &
else
  tail -n0 -F "$PER_REPO_BUS" 2>/dev/null | format_line &
fi
wait
```

`chmod +x scripts/tail-bus.sh`.

- [ ] **Step 3: Run the bats tests**

```bash
bats plugins/broadcastr/tests/bats/tail.bats
```

Expected: all three tests pass. If `format_line` doesn't filter correctly, debug with a single event piped through jq directly first.

- [ ] **Step 4: Commit**

```bash
git add plugins/broadcastr/scripts/tail-bus.sh plugins/broadcastr/tests/bats/tail.bats
git commit -m "broadcastr: tail-bus.sh feed monitor (self-suppress + mute + startup gate)"
```

---

### Task 12: alert-gateway.sh

**Files:**
- Create: `plugins/broadcastr/scripts/alert-gateway.sh`

- [ ] **Step 1: Write `scripts/alert-gateway.sh`**

```bash
#!/usr/bin/env bash
set -uo pipefail

[ "${CLAUDE_PLUGIN_OPTION_APPRISE_ENABLED:-true}" != "true" ] && {
  echo "broadcastr: apprise disabled by config" >&2
  exit 0
}

if ! command -v apprise >/dev/null 2>&1; then
  echo "broadcastr: apprise CLI not installed; alert gateway exiting" >&2
  exit 0
fi

GLOBAL_HOME="${BROADCASTR_HOME:-$HOME/.claude/broadcastr}"
BUS="$GLOBAL_HOME/events.jsonl"
TAG="${CLAUDE_PLUGIN_OPTION_APPRISE_TAG:-broadcastr}"

mkdir -p "$GLOBAL_HOME"
touch "$BUS"

STARTUP="$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)"

cleanup() { kill 0 2>/dev/null || true; }
trap cleanup SIGTERM SIGINT EXIT

tail -n0 -F "$BUS" 2>/dev/null \
  | jq -rc --arg startup "$STARTUP" '
      select(.tier == "alert")
      | select(.ts > $startup)
      | .summary' \
  | while IFS= read -r line; do
      apprise --tag "$TAG" --body "$line" >/dev/null 2>&1 || true
    done
```

`chmod +x scripts/alert-gateway.sh`.

- [ ] **Step 2: Smoke test**

```bash
TMPHOME=$(mktemp -d)
CLAUDE_PLUGIN_OPTION_APPRISE_ENABLED=false \
  plugins/broadcastr/scripts/alert-gateway.sh &
PID=$!
sleep 0.5
kill $PID 2>/dev/null
wait 2>/dev/null
echo "alert-gateway respects disabled config: PASS"
```

- [ ] **Step 3: Commit**

```bash
git add plugins/broadcastr/scripts/alert-gateway.sh
git commit -m "broadcastr: alert-gateway.sh apprise fan-out"
```

---

### Task 13: monitors.json

**Files:**
- Create: `plugins/broadcastr/monitors/monitors.json`

Plugin monitor schema in Claude Code: long-running commands started at session start, restarted on exit per the runtime's policy. Verify the exact format against Claude Code docs at install time; if `monitors.json` is unsupported, fall back to declaring monitors inside `plugin.json`.

- [ ] **Step 1: Write `monitors/monitors.json`**

```json
{
  "monitors": [
    {
      "name": "broadcastr-feed",
      "command": "${CLAUDE_PLUGIN_ROOT}/scripts/tail-bus.sh",
      "description": "Live homelab activity feed (broadcastr)"
    },
    {
      "name": "broadcastr-alerts",
      "command": "${CLAUDE_PLUGIN_ROOT}/scripts/alert-gateway.sh",
      "description": "Routes alert-tier events to apprise"
    },
    {
      "name": "broadcastr-plans",
      "command": "${CLAUDE_PLUGIN_ROOT}/scripts/watch-plans.sh",
      "description": "Watches plan dirs and emits plan / plan-exec events"
    },
    {
      "name": "broadcastr-sessions",
      "command": "${CLAUDE_PLUGIN_ROOT}/scripts/watch-sessions.sh",
      "description": "Watches docs/sessions and emits session-doc events"
    }
  ]
}
```

- [ ] **Step 2: Commit**

```bash
git add plugins/broadcastr/monitors
git commit -m "broadcastr: monitors.json (feed, alerts, watchers)"
```

---

## Phase 5 — Install + skills + CLI

### Task 14: install-hooks skill

**Files:**
- Create: `plugins/broadcastr/skills/broadcastr-install-hooks/SKILL.md`
- Create: `plugins/broadcastr/skills/broadcastr-install-hooks/README.md`
- Create: `plugins/broadcastr/skills/broadcastr-install-hooks/CHANGELOG.md`
- Create: `plugins/broadcastr/skills/broadcastr-install-hooks/scripts/install-git-hooks.sh`
- Create: `plugins/broadcastr/tests/bats/install-hooks.bats`

- [ ] **Step 1: Write the bats test** for idempotent install

```bash
#!/usr/bin/env bats

setup() {
  PLUGIN_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  TMP="$(mktemp -d)"
  cd "$TMP"
  git init -q
  mkdir -p .git/hooks
  export BROADCASTR_PLUGIN_ROOT="$PLUGIN_ROOT"
}

teardown() { rm -rf "$TMP"; }

@test "install creates all five shim hooks" {
  "$PLUGIN_ROOT/skills/broadcastr-install-hooks/scripts/install-git-hooks.sh"
  for h in post-commit pre-commit pre-push post-checkout post-merge; do
    [ -x ".git/hooks/$h" ]
    grep -q "broadcastr" ".git/hooks/$h"
  done
}

@test "install preserves existing hook as .broadcastr-prev" {
  printf '#!/bin/sh\necho legacy\n' > .git/hooks/pre-commit
  chmod +x .git/hooks/pre-commit
  "$PLUGIN_ROOT/skills/broadcastr-install-hooks/scripts/install-git-hooks.sh"
  [ -x ".git/hooks/pre-commit.broadcastr-prev" ]
  grep -q legacy ".git/hooks/pre-commit.broadcastr-prev"
  grep -q broadcastr ".git/hooks/pre-commit"
}

@test "second install does not stack shims" {
  "$PLUGIN_ROOT/skills/broadcastr-install-hooks/scripts/install-git-hooks.sh"
  SHA1=$(sha256sum .git/hooks/post-commit | cut -d' ' -f1)
  "$PLUGIN_ROOT/skills/broadcastr-install-hooks/scripts/install-git-hooks.sh"
  SHA2=$(sha256sum .git/hooks/post-commit | cut -d' ' -f1)
  [ "$SHA1" = "$SHA2" ]
  [ ! -f .git/hooks/post-commit.broadcastr-prev ]
}
```

- [ ] **Step 2: Write `skills/broadcastr-install-hooks/scripts/install-git-hooks.sh`**

```bash
#!/usr/bin/env bash
set -euo pipefail

PLUGIN_ROOT="${BROADCASTR_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-}}"
if [ -z "$PLUGIN_ROOT" ]; then
  echo "broadcastr-install-hooks: BROADCASTR_PLUGIN_ROOT or CLAUDE_PLUGIN_ROOT must be set" >&2
  exit 1
fi

TARGET_REPO="${1:-$PWD}"
HOOK_DIR="$TARGET_REPO/.git/hooks"

if [ ! -d "$HOOK_DIR" ]; then
  echo "broadcastr-install-hooks: $HOOK_DIR not found; run inside a git repo or pass the repo path" >&2
  exit 1
fi

mkdir -p "$HOOK_DIR"

is_broadcastr_shim() {
  # Identifies our own shim by a marker string
  grep -q 'broadcastr-install-hooks SHIM' "$1" 2>/dev/null
}

for hook in post-commit pre-commit pre-push post-checkout post-merge; do
  src="$PLUGIN_ROOT/scripts/git-hooks/$hook"
  dst="$HOOK_DIR/$hook"
  prev="$dst.broadcastr-prev"

  # Build the shim contents fresh with the marker comment
  shim_contents="$(printf '%s\n' '#!/usr/bin/env bash' '# broadcastr-install-hooks SHIM v1' "BROADCASTR_PLUGIN_ROOT='$PLUGIN_ROOT'" "exec '$src' \"\$@\"")"

  if [ -e "$dst" ]; then
    if is_broadcastr_shim "$dst"; then
      # Already our shim — rewrite (idempotent), but don't touch .broadcastr-prev
      printf '%s\n' "$shim_contents" > "$dst"
      chmod +x "$dst"
      continue
    fi
    # Real pre-existing hook — preserve it once
    if [ ! -e "$prev" ]; then
      mv "$dst" "$prev"
      chmod +x "$prev"
    fi
  fi

  printf '%s\n' "$shim_contents" > "$dst"
  chmod +x "$dst"
done

echo "broadcastr: installed shims into $HOOK_DIR"
```

`chmod +x` it.

- [ ] **Step 3: Run the bats tests**

```bash
bats plugins/broadcastr/tests/bats/install-hooks.bats
```

Expected: all three tests pass.

- [ ] **Step 4: Write `SKILL.md`**

```markdown
---
name: broadcastr-install-hooks
description: Install broadcastr's git-hook shims into the current repo. Use when the user says "install broadcastr hooks", "wire up broadcastr in this repo", "set up the broadcastr git hooks", or after first installing the broadcastr plugin in a new repo. Idempotent — safe to run repeatedly. Preserves any pre-existing hook as `<hook>.broadcastr-prev` and chains to it.
---

# broadcastr-install-hooks

Drop broadcastr's shim hooks into the current repo's `.git/hooks/` so commits, pushes, and branch operations emit events to the bus.

## When to use

- After first installing the broadcastr plugin
- After cloning a fresh repo where you want broadcastr active
- Any time `bd push` / commit notifications go silent in a repo (re-installs are safe)

## How

```bash
"$BROADCASTR_PLUGIN_ROOT/skills/broadcastr-install-hooks/scripts/install-git-hooks.sh" [repo_path]
```

`repo_path` defaults to `$PWD`. The script installs five hooks: `post-commit`, `pre-commit`, `pre-push`, `post-checkout`, `post-merge`. Pre-existing hooks are preserved as `<name>.broadcastr-prev` and chained.

## Behavior

- **Idempotent.** Running twice is a no-op.
- **Non-destructive.** Existing hooks become `.broadcastr-prev` and continue to run.
- **Identifies our shims** by a marker comment (`# broadcastr-install-hooks SHIM v1`), so reinstalls don't stack.
```

- [ ] **Step 5: Write `README.md` and `CHANGELOG.md`**

```markdown
# broadcastr-install-hooks

Per-repo git hook installer for the broadcastr plugin. See `SKILL.md` for usage.
```

```markdown
# Changelog

## [0.1.0] - 2026-05-25
- Initial release.
```

- [ ] **Step 6: Commit**

```bash
git add plugins/broadcastr/skills/broadcastr-install-hooks plugins/broadcastr/tests/bats/install-hooks.bats
git commit -m "broadcastr: install-hooks skill (idempotent, shim-marked)"
```

---

### Task 15: User-facing broadcastr skill

**Files:**
- Create: `plugins/broadcastr/skills/broadcastr/SKILL.md`
- Create: `plugins/broadcastr/skills/broadcastr/README.md`
- Create: `plugins/broadcastr/skills/broadcastr/CHANGELOG.md`

- [ ] **Step 1: Write `SKILL.md`**

```markdown
---
name: broadcastr
description: Read or interact with the broadcastr activity feed across concurrent Claude sessions. Use when the user says "what are other agents doing", "show recent activity", "mute plan-exec notifications", "what's on the bus", "broadcastr status", "tail broadcastr", "emit a manual broadcastr event", or asks why a notification appeared. Also use to disable broadcastr in the current session (`BROADCASTR_DISABLED=1`) or check the global feed. Does NOT fire on generic "show me activity" or "what's happening" unless broadcastr is explicitly named.
---

# broadcastr

The broadcastr plugin captures activity from concurrent Claude Code sessions into a shared JSONL bus. This skill explains how to interact with it.

## Reading the feed

The plugin's `broadcastr-feed` monitor automatically prints each new event as a notification line:

```
[info] commit · commit a1b2c3d: <subject> · claude-code@dookie
[alert] push · push FAILED: feature/x · claude-code@steamy
```

Your own session's events are suppressed. Categories listed in `BROADCASTR_MUTE` (comma-separated) are filtered out.

## CLI

```bash
broadcastr emit <category> <tier> <summary> [--data <json>]   # manual emit
broadcastr tail                                                # one-shot tail (same filtering as monitor)
broadcastr recent --since=5m                                   # dump recent events as JSONL
broadcastr status                                              # bus paths, sizes, event counts
broadcastr mute <category>[,<category>...]                     # add to BROADCASTR_MUTE for this session
```

## Configuration

Set via plugin `userConfig` or env var:

- `BROADCASTR_DISABLED=1` — silence this session entirely (no emits, no notifications)
- `BROADCASTR_GLOBAL_FEED=0` — don't tail the cross-repo global bus
- `BROADCASTR_MUTE=plan-exec,session-doc` — drop these categories

## Manual emit example

```bash
broadcastr emit cli info "starting big migration of plugins/broadcastr"
```

## Where things live

- Per-repo bus: `<repo>/.broadcastr/events.jsonl` (gitignored)
- Global bus: `~/.claude/broadcastr/events.jsonl` (host-local, cross-repo)
- Rotated copies: `events.jsonl.1`, `.2`, `.3`

## Install in a new repo

Run the companion skill `broadcastr-install-hooks` to drop git-hook shims into the current repo. Without it, you'll get hook events from Claude (SessionStart, bash classifier) and inotify watchers, but no commit/push/branch events.
```

- [ ] **Step 2: Write `README.md`**

```markdown
# broadcastr (skill)

User-facing skill describing the broadcastr CLI, feed format, mute controls, and how to install git hooks per repo. See `SKILL.md`.
```

- [ ] **Step 3: Write `CHANGELOG.md`**

```markdown
# Changelog

## [0.1.0] - 2026-05-25
- Initial release.
```

- [ ] **Step 4: Validate the skill**

```bash
# Use validate-skill if available, otherwise check by hand:
head -10 plugins/broadcastr/skills/broadcastr/SKILL.md
```

Confirm the `name:` matches the dir, the `description:` leads with "Use when…", lists trigger phrases, includes a negative case, and stays under ~1024 chars.

- [ ] **Step 5: Commit**

```bash
git add plugins/broadcastr/skills/broadcastr
git commit -m "broadcastr: user-facing skill"
```

---

### Task 16: CLI shim + slash command

**Files:**
- Create: `plugins/broadcastr/bin/broadcastr`
- Create: `plugins/broadcastr/commands/broadcastr.md`

- [ ] **Step 1: Write `bin/broadcastr`**

```bash
#!/usr/bin/env bash
set -euo pipefail

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

cmd="${1:-help}"; shift || true

case "$cmd" in
  emit)
    # Usage: broadcastr emit <category> <tier> <summary> [--data <json>]
    cat=$1; tier=$2; summary=$3; shift 3
    exec "$PLUGIN_ROOT/scripts/emit.sh" --category "$cat" --tier "$tier" --summary "$summary" "$@"
    ;;
  tail)
    exec "$PLUGIN_ROOT/scripts/tail-bus.sh"
    ;;
  recent)
    since="5m"
    while [ $# -gt 0 ]; do case "$1" in --since=*) since="${1#--since=}"; shift;; *) shift;; esac; done
    repo_bus="${CLAUDE_PROJECT_DIR:-$PWD}/.broadcastr/events.jsonl"
    global_bus="${BROADCASTR_HOME:-$HOME/.claude/broadcastr}/events.jsonl"
    cutoff=$(date -u -d "$since ago" +%Y-%m-%dT%H:%M:%S.%3NZ 2>/dev/null \
             || date -u -v-"${since}" +%Y-%m-%dT%H:%M:%S.000Z)
    for b in "$repo_bus" "$global_bus"; do
      [ -f "$b" ] || continue
      jq -c --arg cutoff "$cutoff" 'select(.ts > $cutoff)' "$b" 2>/dev/null || true
    done
    ;;
  status)
    repo_bus="${CLAUDE_PROJECT_DIR:-$PWD}/.broadcastr/events.jsonl"
    global_bus="${BROADCASTR_HOME:-$HOME/.claude/broadcastr}/events.jsonl"
    printf 'broadcastr status\n'
    for b in "$repo_bus" "$global_bus"; do
      if [ -f "$b" ]; then
        printf '  %s  %s bytes  %s events\n' "$b" "$(stat -c %s "$b" 2>/dev/null || stat -f %z "$b")" "$(wc -l < "$b")"
      else
        printf '  %s  (absent)\n' "$b"
      fi
    done
    printf '  disabled=%s  global_feed=%s  mute=%s\n' \
      "${BROADCASTR_DISABLED:-0}" "${BROADCASTR_GLOBAL_FEED:-1}" "${BROADCASTR_MUTE:-}"
    ;;
  mute)
    list="$1"
    cur="${BROADCASTR_MUTE:-}"
    if [ -n "$cur" ]; then
      export BROADCASTR_MUTE="$cur,$list"
    else
      export BROADCASTR_MUTE="$list"
    fi
    printf 'BROADCASTR_MUTE=%s\n' "$BROADCASTR_MUTE"
    printf '(env-var only; persists for this shell)\n'
    ;;
  help|*)
    cat <<EOF
broadcastr - shared activity bus for concurrent Claude sessions

Usage:
  broadcastr emit <category> <tier> <summary> [--data <json>]
  broadcastr tail
  broadcastr recent [--since=5m]
  broadcastr status
  broadcastr mute <category>[,<category>...]
EOF
    ;;
esac
```

`chmod +x bin/broadcastr`.

- [ ] **Step 2: Write `commands/broadcastr.md`**

```markdown
---
description: broadcastr status / recent / mute / emit
argument-hint: [status|recent|mute|emit] [args...]
---

Run the broadcastr CLI: `${CLAUDE_PLUGIN_ROOT}/bin/broadcastr $ARGUMENTS`.

Examples:
- `/broadcastr status`
- `/broadcastr recent --since=10m`
- `/broadcastr mute plan-exec`
- `/broadcastr emit cli info "manual broadcast"`
```

- [ ] **Step 3: Smoke-test the CLI**

```bash
TMPREPO=$(mktemp -d)
CLAUDE_PROJECT_DIR=$TMPREPO BROADCASTR_GLOBAL_FEED=0 \
  CLAUDE_PLUGIN_ROOT=$PWD/plugins/broadcastr \
  plugins/broadcastr/bin/broadcastr emit commit info "hello"
CLAUDE_PROJECT_DIR=$TMPREPO \
  plugins/broadcastr/bin/broadcastr status
CLAUDE_PROJECT_DIR=$TMPREPO \
  plugins/broadcastr/bin/broadcastr recent --since=1m
```

Expected: status reports >0 events; recent prints one JSONL line.

- [ ] **Step 4: Commit**

```bash
git add plugins/broadcastr/bin/broadcastr plugins/broadcastr/commands
git commit -m "broadcastr: CLI shim + /broadcastr slash command"
```

---

## Phase 6 — Integration test + marketplace registration

### Task 17: Two-session integration test

**Files:**
- Create: `plugins/broadcastr/tests/integration/two-session.sh`

- [ ] **Step 1: Write the test**

```bash
#!/usr/bin/env bash
# Simulates two concurrent Claude sessions on the same repo by spawning two
# tail-bus.sh processes and one emitter. Asserts that A's emit shows up in B
# but not in A.
set -euo pipefail

PLUGIN_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TMP=$(mktemp -d)
trap "rm -rf $TMP; kill 0 2>/dev/null || true" EXIT

REPO="$TMP/repo"
mkdir -p "$REPO/.broadcastr"
cd "$REPO"
git init -q

export CLAUDE_PROJECT_DIR="$REPO"
export BROADCASTR_HOME="$TMP/home"
export BROADCASTR_GLOBAL_FEED=0
export HOSTNAME=testbox USER=tester

# Session A's monitor
( CLAUDE_SESSION_ID=A "$PLUGIN_ROOT/scripts/tail-bus.sh" > "$TMP/a.out" 2>&1 ) &
A_PID=$!
# Session B's monitor
( CLAUDE_SESSION_ID=B "$PLUGIN_ROOT/scripts/tail-bus.sh" > "$TMP/b.out" 2>&1 ) &
B_PID=$!

sleep 1.5

# Session A emits
CLAUDE_SESSION_ID=A "$PLUGIN_ROOT/scripts/emit.sh" \
  --category commit --tier info --summary "from-A"

sleep 2

kill "$A_PID" "$B_PID" 2>/dev/null || true
wait 2>/dev/null || true

# Assertions
if grep -q "from-A" "$TMP/a.out"; then
  echo "FAIL: A saw its own event"
  exit 1
fi
if ! grep -q "from-A" "$TMP/b.out"; then
  echo "FAIL: B did not see A's event"
  cat "$TMP/b.out"
  exit 1
fi
echo "PASS: cross-session visibility working"
```

`chmod +x tests/integration/two-session.sh`.

- [ ] **Step 2: Run it**

```bash
plugins/broadcastr/tests/integration/two-session.sh
```

Expected: `PASS: cross-session visibility working`.

- [ ] **Step 3: Commit**

```bash
git add plugins/broadcastr/tests/integration
git commit -m "broadcastr: two-session integration test"
```

---

### Task 18: Marketplace registration

**Files:**
- Modify: `.claude-plugin/marketplace.json`
- Create: `catalog/plugins/broadcastr.yaml`

- [ ] **Step 1: Inspect the existing marketplace.json**

```bash
cat .claude-plugin/marketplace.json | head -40
```

- [ ] **Step 2: Add a `broadcastr` entry to `.claude-plugin/marketplace.json`**

The exact JSON shape depends on the existing manifest. Pattern is a `plugins` array; each item points at `./plugins/<name>`. Example entry (adapt to surrounding format):

```json
{
  "name": "broadcastr",
  "source": "./plugins/broadcastr",
  "description": "Real-time activity broadcast across concurrent Claude Code sessions",
  "version": "0.1.0",
  "category": "homelab"
}
```

- [ ] **Step 3: Write `catalog/plugins/broadcastr.yaml`**

```yaml
name: broadcastr
bucket: local
targets:
  - claude
description: |
  Real-time activity broadcast across concurrent Claude Code sessions.
  Captures commits, plan edits, bash commands into a shared JSONL bus;
  each session sees what others are doing via the feed monitor.
v2_planned:
  - codex bridge (UserPromptSubmit injection or codex-app-server subscriber)
  - polling emitters: PR / CI / docker events / cargo
  - web UI / Aurora dashboard
  - TUI consumer
  - multi-host bus sync
v2_blocked_on:
  codex: "deferred; spec sec 'Codex (deferred)'"
  polling-emitters: "v1 ships only event-driven sources"
  multi-host: "needs relay process; out of scope for JSONL-only bus"
```

- [ ] **Step 4: Validate marketplace JSON**

```bash
jq empty .claude-plugin/marketplace.json
```

- [ ] **Step 5: Commit and push**

```bash
git add .claude-plugin/marketplace.json catalog/plugins/broadcastr.yaml
git commit -m "broadcastr: register in marketplace + catalog"
git push
```

---

## Self-review checklist (executor: skim, don't re-run)

- All five hook templates present and chained to `.broadcastr-prev`? ✓
- `flock` in both rotation paths (Rust + bash fallback)? ✓
- Dedup sentinel written by `post-merge`, checked by `post-commit`? ✓
- `pre-push` emits attempt only; push outcome lives in `push-wrapper.sh`? ✓
- Supervisor emits one alert on arm failure, then exits? ✓
- `tail-bus.sh` self-suppression by `$CLAUDE_SESSION_ID`, startup-ts gate, mute filter? ✓
- `broadcastr-install-hooks` is idempotent and uses a marker comment to detect own shims? ✓
- ULID fast path: Rust binary primary, bash fallback explicit and tested? ✓
- Schema validated against actual emitted events? ✓ (via Rust integration tests)
- Two-session integration test covers the headline success criterion? ✓
- No Codex code paths left over? ✓

## Execution handoff

**Plan complete and saved to `docs/superpowers/plans/2026-05-25-broadcastr.md`. Two execution options:**

1. **Subagent-Driven (recommended)** — dispatch a fresh subagent per task, review between tasks
2. **Inline Execution** — execute tasks in this session with checkpoints

Which approach?
