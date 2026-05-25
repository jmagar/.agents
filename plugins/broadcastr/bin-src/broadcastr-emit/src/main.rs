use chrono::Utc;
use clap::Parser;
use fs2::FileExt;
use serde::Serialize;
use serde_json::{Value, json};
use std::fs::{OpenOptions, create_dir_all};
use std::io::Write;
use std::path::{Path, PathBuf};
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

    let home = std::env::var("BROADCASTR_HOME")
        .ok()
        .map(PathBuf::from)
        .or_else(|| std::env::var("HOME").ok().map(|h| PathBuf::from(h).join(".claude/broadcastr")));
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

fn build_event(args: &Args, repo: &str) -> Value {
    let session_id = std::env::var("CLAUDE_SESSION_ID").ok();
    let agent = if session_id.is_some() { "claude-code" } else { "user" };
    let host = std::env::var("HOSTNAME").unwrap_or_else(|_| "unknown".to_string());
    let user = std::env::var("USER").unwrap_or_else(|_| "unknown".to_string());
    let ulid = Ulid::new().to_string();
    let ts = Utc::now().format("%Y-%m-%dT%H:%M:%S%.3fZ").to_string();
    let data: Value = args
        .data
        .as_deref()
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

fn append_line(bus: &Path, line: &str) {
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

fn maybe_rotate(bus: &Path) {
    let max_bytes: u64 = std::env::var("BROADCASTR_BUS_MAX_BYTES")
        .ok()
        .and_then(|s| s.parse().ok())
        .unwrap_or(5 * 1024 * 1024);
    let retain: u32 = std::env::var("BROADCASTR_BUS_RETAIN")
        .ok()
        .and_then(|s| s.parse().ok())
        .unwrap_or(3);

    let size = match std::fs::metadata(bus) {
        Ok(m) => m.len(),
        Err(_) => return,
    };
    if size < max_bytes {
        return;
    }

    let lock_path = bus.with_extension("jsonl.rotate.lock");
    let lock_file = match OpenOptions::new().create(true).write(true).truncate(false).open(&lock_path) {
        Ok(f) => f,
        Err(_) => return,
    };
    if FileExt::try_lock_exclusive(&lock_file).is_err() {
        return;
    }

    // Re-check size under lock (TOCTOU)
    let size = match std::fs::metadata(bus) {
        Ok(m) => m.len(),
        Err(_) => {
            let _ = FileExt::unlock(&lock_file);
            return;
        }
    };
    if size < max_bytes {
        let _ = FileExt::unlock(&lock_file);
        return;
    }

    let base_name = bus.file_name().unwrap().to_string_lossy().to_string();

    // Shift rotations: .N-1 -> .N for N from retain down to 1
    for i in (1..retain).rev() {
        let from = bus.with_file_name(format!("{}.{}", base_name, i));
        let to = bus.with_file_name(format!("{}.{}", base_name, i + 1));
        if from.exists() {
            let _ = std::fs::rename(&from, &to);
        }
    }
    let dot1 = bus.with_file_name(format!("{}.1", base_name));
    let _ = std::fs::rename(bus, &dot1);
    let _ = OpenOptions::new().create(true).write(true).truncate(true).open(bus);

    let _ = FileExt::unlock(&lock_file);
}
