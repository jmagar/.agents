# claude-in-mobile — Research for an Android APK Live-Testing Skill

> Research target: author a future Claude Code skill that drives a built Android APK on an
> emulator end-to-end (install → launch → exercise every feature → review UI/UX → produce a
> works/doesn't-work report). This document is the understanding layer, NOT the skill.
>
> Sources studied: cloned repo `~/workspace/claude-in-mobile/` (README.md @ 603 lines,
> package.json v3.10.2, CLAUDE.md, full `src/` TS tree of 153 files), existing local skill
> `~/.agents/src/skills/claude-in-mobile/` (SKILL.md, README.md, references/tooling.md).
>
> **Verification status:** Tool parameter schemas, action names, the gateway registration, and
> the ADB wiring were all confirmed against source (`src/tools/*.ts`, `src/tools/meta/*.ts`) and
> the live `~/.lab/config.toml`. The README documents the v3.8.0 tool surface while the package
> is v3.10.2 — **source has MORE than the README** (extra screenshot modes, `app_restart`,
> 5 autopilot actions, log-wait/pid/is_running system tools). The one genuine remaining unknown
> is whether an emulator/ADB endpoint is actually live at the configured `172.19.0.1:5037` right
> now (see §4/§7) — that is a runtime fact, not a code fact, and must be probed at skill-run time.

---

## 1. What it is, architecturally

**claude-in-mobile** (npm package name; product name "Claude Mobile"; author Alex Gladkov,
MIT) is an **MCP server for mobile / desktop / browser automation** — "like Claude in Chrome,
but for devices, apps, and browsers."

Two distributable artifacts ship from one repo:

| Artifact | Language/runtime | Entry | Use |
|---|---|---|---|
| **MCP server** | TypeScript / Node.js (≥18), ESM | `dist/index.js` (also the `bin`) | interactive agent automation over MCP stdio |
| **Native CLI** | Rust (Cargo) + Swift helpers, ~2 MB binary | `claude-in-mobile` (Homebrew/release) | scripts, CI smoke tests, terminal use; no Node needed |

MCP server runtime deps: `@modelcontextprotocol/sdk ^1`, `chrome-launcher`,
`chrome-remote-interface` (CDP), `google-auth-library` (Play store), `jimp` (image
processing), optional `sharp`. Tests via `vitest`.

**Platform adapters (what it controls):**

| Platform | Backend it drives | Notes |
|---|---|---|
| **Android** | **ADB** (`adb`, `uiautomator`, `screencap`, `logcat`) | the relevant target for APK testing |
| iOS | `simctl` + **WebDriverAgent** (via Appium xcuitest) | Simulator only; no physical device |
| Desktop | macOS-only companion (JDK 17+, Accessibility perm) | any SwiftUI/AppKit/Electron/Compose app |
| Aurora OS | `audb` / `audb-client` over SSH | Russian mobile OS; niche |
| Browser | Chrome/Chromium via **CDP** | loads on demand |

**It does NOT spin up its own emulator/AVD.** It attaches to whatever ADB already sees
(emulator or USB device). The agent/operator must boot the AVD (`emulator -avd ...`) and have
`adb` reachable first. ADB is auto-discovered in this order: `ADB_PATH` env →
`$ANDROID_HOME/platform-tools/adb` → `$ANDROID_SDK_ROOT/platform-tools/adb` → OS default
(`~/Android/Sdk` on Linux, `~/Library/Android/sdk` on macOS, `%LOCALAPPDATA%\Android\Sdk` on
Windows) → `adb` on `PATH`. Missing → `[ADB_NOT_INSTALLED]` error listing probed paths.

**Design philosophy:** token-optimized **meta-tools**. Instead of ~81 individual MCP tools, it
exposes **8 core meta-tools + 3 optional on-demand modules**, each routed by an `action`
parameter (`device(action:'list')`, `input(action:'tap', ...)`). Optional modules
(`browser`, `desktop`, `store`) load on demand (auto-enable on first call or
`device(action:'enable_module', module:'…')`) so the default schema stays lean. Claimed ~85%
token reduction. Old flat tool names (`tap`, `screenshot`, `launch_app`) still work as
**aliases**.

---

## 2. Complete capability surface

### 2.1 Core meta-tools (always present)

| Meta-tool | Actions | What it does for Android testing |
|---|---|---|
| `device` | `list`, `set`, `set_target`, `get_target`, `enable_module`, `disable_module`, `list_modules` | enumerate adb devices, pick the active target, toggle optional modules |
| `input` | `tap`, `double_tap`, `long_press`, `swipe`, `text`, `key` | touch + keyboard; the core "do something" verbs |
| `screen` | `capture`, `annotate` | `capture`: screenshot, params `compress`(true), `maxWidth`(540)/`maxHeight`(960)/`quality`(55), presets low/medium/high, `diff:true` (returns only changed region: <5%=text "unchanged", 5–80%=cropped, >80%=full), `waitForStable:true` (settles after animation). Returns base64 image + text; stores scale for coord auto-correct. `annotate`: numbered bounding boxes + clickable flags + center coords (Android/iOS; falls back to plain shot if no UI elements) |
| `ui` | `tree`, `find`, `find_tap`, `tap_text`, `analyze`, `wait`, `assert_visible`, `assert_gone` | `tree`: uiautomator hierarchy (params `showAll`, `compact`, `format:'semantic'` for ~3x fewer tokens, `fresh:true` to bypass 2s dedup cache). `find`(text/resourceId/className/clickable). `find_tap`(description NL, minConfidence 30, walkToClickable true → walks up to clickable ancestor; **Android only**). `tap_text` is **Desktop/macOS only — not Android**. `analyze`: buttons/inputs/scrollables/dialogs + current activity. `wait`/`assert_visible`/`assert_gone` return PASS/FAIL (isError on fail) |
| `app` | `launch`, `stop`, `install`, **`restart`**, `list` | `install`(path → APK, `adb install`), `launch`(package), `stop`(package force-stop), `restart`(package, delayMs 500 → stop+launch to clear in-memory state without uninstall), `list` (Aurora only — NOT a general installed-apps lister on Android; use `system shell pm list packages` for that) |
| `system` | `activity`, `shell`, `wait`, `open_url`, `logs`, **`wait_log`**, `clear_logs`, **`pid_of`**, **`is_running`**, `info`, `webview`, `clipboard_*`, `permission_*`, `file_*`, `metrics`, `reset_metrics` | adb shell; **logcat read/clear**; `wait_log`(regex pattern, clearFirst) blocks until a marker (crash detection); `pid_of`/`is_running`(package) for liveness; deep links (`open_url`); current `activity`; device `info`; `webview` CDP bridge; clipboard; **grant/revoke/reset permissions**; file push/pull (Aurora); telemetry. (Note: `pid_of`/`is_running`/`wait_log` are v3.10 source additions not in the README — purpose-built for crash detection.) |
| `flow_batch` | (single tool) | run up to **50** commands sequentially in one round-trip |
| `flow_run` | (single tool) | up to **20**-step flow with conditionals (`if_not_found`), loops (`repeat`), and `on_error` |

A third flow primitive, **`flow_parallel`**, runs the same action across up to 10 devices via
`Promise.allSettled`.

**Confirmed action/param details from source (the load-bearing ones for testing):**
- **Meta-dispatch mechanism** (`create-meta-tool.ts`): every meta-tool requires `action`
  (string enum); all underlying tools' params are merged into one flat schema, so you pass
  `action` + whatever fields that action needs. Unknown action → `UnknownActionError` listing
  valid actions. Old flat names are registered as aliases that just set the `action` default.
- **`device`**: `list`, `set` (`deviceId`), `set_target`/`get_target` (`target` platform),
  `enable_module`/`disable_module` (`module` string|array, or `category`:
  core/platform/testing/automation), `list_modules`.
- **`input`** params (flat): `x,y` / `x1,y1,x2,y2` (swipe), `text`, `resourceId`, `label`,
  `index` (from annotate/tree), `key` (BACK/HOME/ENTER/TAB/DELETE…), `direction`
  (up/down/left/right), `duration`, `interval` (double_tap), `hints` (default true: returns
  what changed after the action). Actions: tap/double_tap/long_press/swipe/text/key.
- **`app`**: `launch`(package), `stop`(package), `install`(path), `restart`(package,delayMs),
  `list`(Aurora only). Package names are whitelist-validated; install path is validated against
  traversal.
- **`system`** confirmed actions: activity, shell(command), wait(ms≤30000), open_url(url),
  logs(level,tag,lines≤500,package), **wait_log**(pattern regex, timeoutMs≤30000, clearFirst,
  contextLines), clear_logs, **pid_of**(package), **is_running**(package), info, webview,
  clipboard_select/copy/paste/get, permission_grant/revoke/reset(package,permission),
  file_push/pull(localPath,remotePath — Aurora), metrics, reset_metrics.

### 2.2 Optional modules (load on demand)

| Module | Actions | Relevance |
|---|---|---|
| `browser` | `open`, `navigate`, `click`, `fill`, `fill_form`, `press_key`, `snapshot`, `screenshot`, `evaluate`, `wait_for_selector`, `close`, `list_sessions`, `clear_session` | for hybrid/web-content apps; CDP |
| `desktop` | `launch`, `stop`, `windows`, `focus`, `resize`, `clipboard_get`, `clipboard_set`, `performance`, `monitors` | macOS only; not for Android |
| `store` | `upload`, `set_notes`, `submit`, `get_releases`, `discard`, `promote`, `halt_rollout`, `get_versions` | Play / Huawei / RuStore publishing — **destructive, out of scope for testing** |

### 2.3 Quality-engineering tools (the gold for a testing skill)

The repo has dedicated `src/tools/*.ts` and `src/{a11y,autopilot,perf}/` modules powering
these (confirmed by file tree: `accessibility-tools.ts`, `visual-tools.ts`, `recorder-tools.ts`,
`sync-tools.ts`, `autopilot-tools.ts`, `performance-tools.ts`):

| Tool | Actions (per README) | What it produces |
|---|---|---|
| `accessibility` | `audit` | **WCAG 2.2 audit**: missing labels, touch targets < 48px, focus order, duplicate labels. Scored output (`src/a11y/score.ts`, `formatter.ts`, `rules/`). |
| `visual` | `baseline_save`, `compare` | baseline screenshots + pixel-diff regression (`src/utils/baseline-store.ts`) |
| `recorder` | `start`, `stop`?, `play` | record taps/swipes/input, replay without code (`src/utils/scenario-store.ts`) |
| `sync` | `create`, `barrier` | barrier-based multi-device coordination |
| `autopilot` | **`explore`, `generate`, `heal`, `status`, `tests`** (confirmed) | `explore`(package, strategy bfs/dfs/smart [def smart], maxScreens [20,≤100], maxActions [100,≤500], dryRun) → autonomous crawl building a nav graph via screen fingerprinting; `generate`(explorationId, format flow_run/steps) → emits flow_run-compatible test steps; `heal`(originalSelector, confidence) → fuzzy-rematch a broken selector; `status`/`tests` inspect saved runs. This is the closest built-in to "exercise every feature." |
| `performance` | `start`, `snapshot`, `stop`? | real-time memory/CPU/FPS, snapshots, perf baselines (`src/perf/collector.ts`, `formatter.ts`) |

Other source-tree tool files (sensor, intent, network, sandbox) suggest **additional v3.9/3.10
actions not in the v3.8 README** — e.g. `sensor-tools.ts` (GPS/sensor injection),
`intent-tools.ts` (Android intents), `network-tools.ts` (network conditioning),
`sandbox-tools.ts`. **[VERIFY]** their exact action/param names against source + live
`tools/list`.

### 2.4 What inputs/outputs an LLM gets

- **Screenshots:** `screen(action:'capture')` returns an auto-compressed image (presets like
  `low`/`high`; `preset='low'` ≈ 270×480). `screen(action:'annotate')` overlays numbered
  labels + colored boxes so the model can tap by index.
- **UI hierarchy / accessibility tree:** `ui(action:'tree')` (uiautomator XML → structured
  tree) and `ui(action:'find')` return device-space coordinates, `text`, `resourceId`,
  `class`, `label`, bounds. This is the text-based alternative to vision.
- **Logs:** `system(action:'logs')` = logcat (read), `clear_logs` to reset before a flow —
  the crash/exception detection channel.
- **Telemetry:** `system(action:'metrics')` per-tool call metrics.
- **Inputs:** tap/double_tap/long_press/swipe/text/key (`input`), plus `app install/launch/stop`,
  `system open_url` (deep links), `permission_*`, `file_*`.

---

## 3. The interaction loop for live APK testing

The canonical agent loop (confirmed against source `src/tools/*.ts`):

1. **Pre-flight:** `claude-in-mobile doctor` (CLI) or `device(action:'list')` (MCP) to confirm
   ADB sees the emulator. `device(action:'set'/'set_target', deviceId:…)` to pin the active
   device (also `get_target`, `list_modules`).
2. **Install:** `app(action:'install', path:'/abs/app.apk')` — confirmed: param is `path`
   (string, required); Android runs `adb install`.
3. **Clear baseline state:** `system(action:'clear_logs')` so logcat only shows this run.
4. **Launch:** `app(action:'launch', package:'com.example.app')` — confirmed: param `package`
   (required). Also `app(action:'restart', package:…, delayMs:500)` to clear in-memory state
   without uninstall, and `app(action:'stop', package:…)`.
   `system(action:'wait', ms:…)` / `ui(action:'wait', text|resourceId|className, timeout, interval)`
   for first screen. Screenshots support `waitForStable:true` (auto-settles after animations).
5. **Observe:** `screen(action:'capture')` — confirmed params: `compress`(def true),
   `maxWidth`(540)/`maxHeight`(960)/`quality`(55), presets `low`(270×480)/`medium`/`high`,
   `diff:true` (returns only changed region: <5% = text "unchanged", 5-80% = cropped, >80% =
   full), `waitForStable:true`. Returns a base64 JPEG/PNG image + a text note (and stores the
   scale factor for coordinate auto-correction). `ui(action:'tree')` for the text hierarchy
   (supports `format:'semantic'` for ~3x token reduction, `showAll`, `compact`; output is
   dedup-cached for 2s — pass `fresh:true` to bypass). For reliable tapping prefer
   `screen(action:'annotate')` → tap by numbered `index`, or `ui` semantic locators.
6. **Act:** `ui(action:'find_tap', description:'submit button', minConfidence:30)` (Android
   fuzzy NL tap, walks up to clickable ancestor by default), or
   `input(action:'tap', x|y | text | resourceId | label | index)`. (`ui_tap_text` is
   Desktop/macOS-only — NOT for Android.) Type with `input(action:'text', text:…)`; keys with
   `input(action:'key', key:'BACK'/'HOME'/'ENTER'/…)`; gestures with
   `input(action:'swipe', direction|x1,y1,x2,y2)`, `double_tap`, `long_press`. Deep links via
   `system(action:'open_url', url:'myapp://…')` (Android: `am start -a VIEW -d`).
7. **Assert:** `ui(action:'assert_visible' / 'assert_gone', text|resourceId)` — returns
   `PASS:`/`FAIL:` and sets `isError:true` on failure (machine-checkable pass/fail).
8. **Detect failure (confirmed primitives):** `system(action:'logs', level:'E'|'F', package, lines)`
   then grep for `FATAL EXCEPTION` / `ANR` / `Force Close`; OR
   `system(action:'wait_log', pattern:'FATAL EXCEPTION|ANR in', timeoutMs, clearFirst)` to block
   until a crash marker appears; verify the app is alive with
   `system(action:'is_running', package)` → `true/false` or `system(action:'pid_of', package)`
   → PID/0; check `system(action:'activity')` didn't bounce to launcher/crash dialog.
9. **Batch/flow:** wrap repeatable sequences in `flow_batch` (≤50) or `flow_run` (≤20 steps,
   `if_not_found`/`repeat`/`on_error`) to cut round-trips.
10. **Autonomous coverage:** `autopilot(action:'explore')` to BFS/DFS-crawl the whole app and
    auto-build a nav graph + generated tests — the closest built-in primitive to "exercise
    every feature."
11. **Quality signals:** `accessibility(action:'audit')`, `visual(action:'compare')`,
    `performance(action:'snapshot')` per screen.

**Crucial coordinate gotcha (must encode in the skill):** raw `x`/`y` passed to
`input(tap/swipe/long_press)` are interpreted in **the most recent screenshot's pixel space**
and auto-scaled to device coords using the last `screen(capture)` scale. But `ui_find`/`ui_tree`
coords are **device coordinates**. Mixing them over-scales. Rule: **prefer semantic locators
(`index`, `text`, `resourceId`, `label`) over raw coords.** If no screenshot was taken yet,
raw coords pass through 1:1.

---

## 4. Prerequisites & setup — homelab reality vs. user-provided

**Required for Android testing:**
- `adb` installed and on PATH (or `ADB_PATH`); a **booted emulator/AVD** or USB device that
  `adb devices` lists. **The tool does not create the AVD or boot the emulator.**
- The MCP server itself: Node ≥18 + `npx claude-in-mobile@latest`, OR the Rust CLI via brew.
- The **APK file path** (the build artifact) — user/CI must produce it.

**Confirmed homelab wiring (from `~/.lab/config.toml`):** the server IS registered on the Lab
MCP gateway under the upstream name **`claude-in-mobile`**, stdio transport, launched as:
```toml
[[upstream]]
name = "claude-in-mobile"
enabled = true
priority = 1.0
command = "env"
args = ["ANDROID_ADB_SERVER_ADDRESS=172.19.0.1", "ANDROID_ADB_SERVER_PORT=5037", "npx", "-y", "claude-in-mobile"]
proxy_resources = true
proxy_prompts = true
```
(stdio MCP server, spawned via `env` to inject the two ADB vars before `npx -y claude-in-mobile`.)
This is the decisive fact about colocation: the server is told (via `ANDROID_ADB_SERVER_ADDRESS`/
`ANDROID_ADB_SERVER_PORT`) to talk to an **ADB server over TCP at `172.19.0.1:5037`** — a Docker
bridge-gateway IP. So the design intent is that adb (and behind it, an emulator) is reachable on
the Docker network at that address, NOT via the gateway host's local default adb. Concretely,
*something* must be listening at `172.19.0.1:5037` — either an Android-emulator container that
exposes an adb TCP server there, or an `adb -a -P 5037 nodaemon server` bridge — and an AVD must
be booted and visible to it.

**Runtime probe from THIS session's host (2026-05-29, read-only) — the infra is REAL:**
- `which adb emulator` → **both present**: `~/Android/Sdk/platform-tools/adb`,
  `~/Android/Sdk/emulator/emulator`. A full Android SDK is installed on this host.
- An **adb server IS running and listening on `*:5037`** (pid 597586) — and `172.19.0.1:5037`
  (the address the gateway wires the server to) is **OPEN**. So the configured ADB endpoint is
  live; the gateway's claude-in-mobile server can reach it.
- `adb devices` → **empty list** (`List of devices attached` with no entries). `172.19.0.1:5555`
  (emulator console/adb) → connection refused.

Interpretation: **the host, SDK, and adb server are all in place and correctly wired to
`172.19.0.1:5037`** — but **no emulator/AVD is currently booted**, so adb sees zero devices.
Every Android command would fail at `device(action:'list')` until an AVD is launched. This
confirms the design: claude-in-mobile attaches to a running emulator but never boots one. The
skill's **step 0 must boot an AVD** (`emulator -avd <name> [-no-window -no-audio]` &
`adb wait-for-device`) and then verify `device(action:'list')` returns the device before
proceeding.

**Further probe — an AVD already exists:** `emulator -list-avds` → **`axon_test`**
(`~/.android/avd/axon_test.avd/` + `axon_test.ini`). So the host is essentially turnkey: SDK +
adb (on `*:5037`, reachable at `172.19.0.1:5037`) + a created AVD named `axon_test`. The ONLY
missing runtime step is **booting that AVD** — it is not currently running (adb device list is
empty). So the skill's step 0 reduces to: `emulator -avd axon_test -no-window -no-audio &` →
`adb wait-for-device` → poll `adb shell getprop sys.boot_completed` → verify
`device(action:'list')`. (If a future host has no AVD, fall back to
`avdmanager create avd` + `sdkmanager` system image as a one-time bootstrap.)

**Not present / user-must-provide:** the AVD image + emulator boot (the tool never creates/boots
an AVD), and the APK build artifact (path passed to `app install`).

---

## 5. Capturing evidence for a works/doesn't-work report

- **Screenshots to disk:** CLI `claude-in-mobile screenshot android -o result.png`. Via MCP,
  `screen(action:'capture')` returns an image the agent can save; `annotate` gives labeled
  evidence. Save one per screen/step into a run dir.
- **Logs:** `system(action:'clear_logs')` before, `system(action:'logs')` after each step;
  archive the full logcat. CLI: pipe `ui-dump` / logs to files.
- **UX/accessibility signals:** `accessibility(action:'audit')` → WCAG findings + score;
  `visual(action:'compare')` → pixel-diff vs baseline; `performance(action:'snapshot')` →
  memory/CPU/FPS per screen. `ui(action:'tree')` dumps give text evidence of what was on screen.
- **Pass/fail encoding:** `ui assert_visible/assert_gone` produce structured results;
  `system(action:'activity')` confirms you're still in the app (not a crash dialog).
- **Coverage trace:** `autopilot` emits a nav graph of visited screens.

---

## 6. How to invoke it from THIS environment

This Claude Code environment exposes upstream MCP servers via the **Lab gateway**. Two possible
surfaces (per `~/.claude/CLAUDE.md`):

**Confirmed: the gateway upstream name is `claude-in-mobile`** (from `~/.lab/config.toml`). So
tool ids are namespaced under that.

**A) Tool-search / tool-execute pair.** The gateway's hybrid semantic search + execute:
```
tool_search("android emulator screenshot tap app")      # finds the claude-in-mobile tools
tool_execute("claude-in-mobile", { "action": "...", ... })
```
In *this* sandbox the gateway also appears as Code-Mode helpers:
`mcp__plugin_lab_lab__search` (filter the upstream catalog) and
`mcp__plugin_lab_lab__execute` (run `callTool("upstream::claude-in-mobile::<tool>", params)`):
```js
await callTool("upstream::claude-in-mobile::device", { action: "list" });
await callTool("upstream::claude-in-mobile::screen", { action: "capture", preset: "low" });
await callTool("upstream::claude-in-mobile::app",    { action: "launch", package: "com.example.app" });
```

**B) Direct `mcp__*` tools.** If the gateway re-exports flat, tools appear as
`mcp__claude-in-mobile__device`, `mcp__claude-in-mobile__screen`, etc.

**Still to confirm at authoring time** (cheap, one call): whether the gateway exposes the 8
**meta-tools** (`device`, `input`, `screen`, `ui`, `app`, `system`, `flow_*`) or only the
`tool_search`/`tool_execute` pair, and which tool-id form (`upstream::…` vs `mcp__…`) this
client actually presents. The server *name* is solid; only the surface form needs a quick probe.

**Local alternative (most reliable for an actual test harness):** ignore the gateway and run
the server/CLI directly on the host that has the emulator — `npx claude-in-mobile` (MCP stdio)
or the brew CLI for scripted runs. The CLI is explicitly the recommended CI/smoke-test surface
(exit codes, stdout/stderr).

---

## 7. Gaps & gotchas (what blocks fully-autonomous APK testing)

1. **No emulator lifecycle management.** It attaches to an existing device; it won't create or
   boot an AVD, nor cold-boot/wipe. The skill must own emulator boot (`emulator -avd`,
   `adb wait-for-device`) separately.
2. **Host/adb colocation — resolved by config, but runtime-dependent.** The gateway server is
   wired to adb at `172.19.0.1:5037` (Docker bridge). It can only see emulators that this adb
   endpoint sees. If nothing is listening there, or no AVD is booted, every Android call fails
   at `device(action:'list')`. This is the chief homelab risk — probe it first.
3. **Coordinate-space trap** (Section 3) — raw coords vs device coords. Must default to semantic
   locators.
4. **UI tree depends on uiautomator** — Compose/custom-canvas apps and WebViews often expose a
   thin/empty tree; the agent then has to fall back to vision (`screen capture`/`annotate`) and
   the `webview` CDP bridge. Games/canvas UIs are largely vision-only.
5. **Flakiness/timing** — needs explicit `ui(action:'wait')`/`assert` between steps; animations
   and async loads break naive screenshot-then-tap.
6. **No physical-iOS / Android-only-on-the-host caveats** are irrelevant here but Desktop is
   macOS-only — not usable from a Linux gateway host.
7. **Version drift (in the skill author's favor)** — README is v3.8.0, package v3.10.2; source
   has MORE than the README: `app_restart`; screenshot `diff`/`waitForStable`/preset modes;
   `ui_tree format:'semantic'`; `system` `wait_log`/`pid_of`/`is_running` (purpose-built for
   crash detection); autopilot's full 5 actions (`explore`/`generate`/`heal`/`status`/`tests`).
   Under-documented modules (sensor/intent/network/sandbox) exist in `src/tools/` — confirm their
   action names against source + a live `tools/list` only if the skill needs them.
8. **Destructive surfaces** (`store`, `system shell`, `permission_*`, `file_*`) must be guarded;
   never invoke store ops during testing.
9. **Existing local skill is generic, not testing-focused** (see §8).

---

## 8. Assessment of the existing local skill

`~/.agents/src/skills/claude-in-mobile/` (SKILL.md ~152 lines + references/tooling.md) is a
solid **general operator** skill: it documents config, requirements, the tool families, generic
workflows (device discovery, visual inspection, cross-platform smoke test, QA pass, desktop,
browser, store), CLI examples, and good guardrails (coordinate space, semantic locators,
evidence-before-state-change, destructive-op confirmation).

**What's MISSING for an Android-APK live-testing workflow:**
- No emulator boot/AVD lifecycle steps.
- No structured **"exercise every feature"** strategy (feature inventory → systematic crawl →
  `autopilot` usage) — `autopilot` is named but no recipe.
- No **crash-detection loop** (clear_logs → act → grep logcat for FATAL/ANR → activity check).
- No **report format / artifact layout** (where screenshots/logs/assertions go; pass-fail
  schema).
- No concrete **gateway invocation** for this environment (it documents stdio `npx`/`codex`
  config, not `tool_execute`/`mcp__*`).
- No exact parameter schemas (it stays at the family level).
- No deep-link / permission-priming patterns for reaching gated features.

---

## 9. Recommendation: shape of a future `android-app-testing` skill

**Trigger:** "test this APK on the emulator", "run an end-to-end test of the Android build",
"exercise every feature and tell me what's broken", "UX review of the app on Android".

**HIGHEST-RISK AUTHORING ASSUMPTION — do not skip:** Do NOT assume the 8 meta-tools
(`device`/`input`/`screen`/`ui`/`app`/`system`/`flow_*`) are exposed directly in this
environment. Per the homelab CLAUDE.md, the Lab gateway may surface ONLY a
`tool_search` + `tool_execute` pair, with the real `claude-in-mobile` tools hidden behind them.
The skill's **very first action must be a capability probe**: discover how the tools are
reachable (direct `mcp__claude-in-mobile__*`, `tool_execute("claude-in-mobile", …)`, or
`callTool("upstream::claude-in-mobile::…")`) before doing anything else, and branch accordingly.
Treat "which surface" as a runtime discovery, never a hardcoded assumption.

**Prerequisite resolution (skill step 0):**
1. Decide invocation surface via the capability probe above. Prefer **local CLI/stdio on the
   emulator host** when available; otherwise use the confirmed gateway route.
2. Ensure emulator: boot AVD if none (`emulator -avd … -no-window` acceptable for headless),
   `adb wait-for-device`, then `device(action:'list')` to confirm.
3. `claude-in-mobile doctor` to validate deps.

**Core workflow:**
1. **Install & launch** the APK; capture package name (`app list` / aapt). Clear logcat.
2. **Map the app:** first screenshot + `ui tree`; build a feature/screen inventory. Optionally
   kick off `autopilot(action:'explore')` for breadth, then targeted manual flows for depth.
3. **Per-feature loop** (encode as `flow_run` where possible): navigate (semantic locators /
   deep links) → act → `assert_visible/gone` → screenshot (annotated) → read+grep logcat for
   `FATAL EXCEPTION|ANR|Crash` → confirm activity still in-app. On crash: capture full logcat +
   screenshot, mark feature FAIL, attempt relaunch, continue.
4. **Quality pass per key screen:** `accessibility(action:'audit')`, optional
   `visual(action:'compare')` against a baseline, `performance(action:'snapshot')`.
5. **Prime gated features:** grant runtime permissions (`system permission_grant`) and use deep
   links to reach hard-to-navigate flows.

**What it automates:** emulator readiness, install/launch, systematic feature traversal,
crash/ANR detection, accessibility + visual + perf capture, evidence collection, and report
generation.

**Report format it should emit** (markdown + an artifacts dir):
- Header: app/package, version, APK path, device/emulator, server version, run timestamp.
- **Per-feature table:** Feature | Steps taken | Result (PASS/FAIL/BLOCKED) | Evidence
  (screenshot paths) | Crash/log excerpt.
- **Crash log** section (logcat excerpts for each failure).
- **UX/accessibility findings** (WCAG audit summary + score, visual diffs, perf outliers).
- **Coverage summary** (screens visited vs. inventory; what couldn't be reached).
- **Verdict:** overall works/doesn't-work + prioritized issue list.
- Artifacts saved under a run dir: `screenshots/`, `logs/`, `ui-trees/`, `report.md`.

**Guardrails to carry over:** semantic locators over raw coords; clear_logs before each run;
never touch `store`; confirm active target before destructive shell/permission/file ops;
collect evidence before mutating state.
