# Desktop App Testing via Windows-MCP + dockur/windows — Research Report

> Research for a future Claude Code SKILL that drives live, end-to-end testing of a built
> Windows desktop application (`.exe`) inside a Windows 11 VM: launch the real binary, exercise
> every feature, review UI/UX, and produce a works / doesn't-work report.
>
> Sources studied: `~/workspace/Windows-MCP/` (README.md, manifest.json v0.8.1, src tree),
> `~/workspace/dockur-windows/`, `~/.agents/src/skills/agent-os/`, and the homelab
> integration reality in `~/.claude/CLAUDE.md`. Date: 2026-05-29.

---

## ⚠️ Current reality (verified live this session — read first)

The task framing assumes a running VM whose Windows-MCP tools are auto-connected. **Both are false
right now:**
1. **The Windows VM is NOT running.** `ssh dookie 'docker ps -a'` lists 44 containers; **none** is
   `agent-os-win11` / `win*` / `dockur`. `:8006` and `:2222` refuse connections. The container is
   absent, not merely stopped.
2. **`windows-mcp` is NOT registered in this Claude environment.** No entry in `~/.claude.json`
   (top-level or any project `mcpServers`) or `~/.claude/settings.json`; the `mcp__windows-mcp__*`
   tools were not loadable this session.

So the future skill's **first job is provisioning, not testing**: start the VM
(`docker compose -f /home/jmagar/compose/windows/docker-compose.yml up -d` on `dookie`; `/storage`
persists so installed software + the in-guest Windows-MCP server survive), wait for boot, then
establish/confirm the `windows-mcp` MCP registration (URL + bearer) so the tools exist. Only after
that does the §4 testing loop apply. (The authoritative compose config is in §3; full probe details
in "Live-environment probe".)

---

## 1. What Windows-MCP is (architecture)

**Windows-MCP** (CursorTouch, MIT, Python 3.13+) is an MCP server that runs **natively on the
Windows machine** and exposes desktop automation as MCP tools. It is the bridge between an LLM
agent and the Windows OS: file navigation, application control, UI interaction, and **QA testing**
are explicitly listed as intended uses. Repo identity: `io.github.CursorTouch/Windows-MCP`,
manifest version **0.8.1**, ~2M users via the Claude Desktop extension directory.

### Runtime
- Pure Python (3.13+), launched with `uv` / `uvx`. Entry point `src/windows_mcp/__main__.py`,
  CLI verb `windows-mcp serve`.
- **Runs inside the Windows guest** — it needs Windows APIs (UI Automation), so it cannot run on
  the Linux host. (The README's WSL section confirms: the server must execute on the Windows side.)
- Transports: `stdio` (default), `sse`, and `streamable-http`. For our VM scenario the server is
  reached over the network via HTTP + Bearer token (see §5/§7).

### How it observes the desktop — two complementary surfaces
1. **UI Automation accessibility tree (primary).** Built on Microsoft UI Automation via the
   `uiautomation` Python library (`src/windows_mcp/uia/`, `tree/`). `Snapshot` walks the control
   tree and returns **interactive elements with ids/labels and coordinates** (buttons, text
   fields, links, menus) plus scrollable regions and system language. This means the agent can
   target controls **by name/label**, not just by guessing pixels. **No computer vision required**
   — "Use Any LLM (Vision Optional)."
2. **Screenshots (visual context).** `Screenshot` grabs a fast PNG (cursor pos + active/open
   windows) and skips tree extraction for speed. Capture backends, in `auto` order:
   **dxcam (DXGI) → mss → pillow** (`WINDOWS_MCP_SCREENSHOT_BACKEND`). High-DPI images may be
   downscaled (`WINDOWS_MCP_SCREENSHOT_SCALE`, 0.1–1.0) to fit client image limits — when
   downscaled, multiply image coords by `original/displayed` to get real screen coords.

### How it sends input
Synthetic mouse/keyboard at the OS level (coordinate- or element-targeted), keyboard shortcuts,
plus a full **PowerShell** execution channel and direct **FileSystem / Registry / Process /
Clipboard / Notification** services. Typical action latency 0.2–0.9 s.

### DOM mode for browsers
`Snapshot(use_dom=True)` focuses on web-page content and filters out browser chrome. Supports
Chrome, Edge, Firefox (Firefox via an IAccessible2 fallback — `tree/ia2.py`). Not central to
desktop-`.exe` testing but useful if the app embeds a webview.

### Source layout (confirms the capability map)
```
src/windows_mcp/
  __main__.py, config.py, paths.py
  tools/        input.py snapshot.py shell.py filesystem.py app.py process.py
                clipboard.py registry.py notification.py scrape.py multi.py
  uia/          core.py controls.py patterns.py events.py enums.py   # UI Automation engine
  tree/         service.py views.py ia2.py cache_utils.py            # a11y tree extraction + DOM
  desktop/      service.py screenshot.py flash_overlay.py views.py   # capture + post-capture flash
  powershell/   service.py utils.py                                  # PS execution
  filesystem/, registry/, process/, notifications/                   # backing services
  watchdog/     service.py event_handlers.py                         # UI/file event watching
  infrastructure/ oauth.py security.py analytics.py                  # auth, IP allowlist, telemetry
  vdm/core.py                                                        # virtual desktop mgmt
```

---

## 2. Complete capability surface (19 tools in source; manifest lists 18)

**Exact count:** the source registers **19** tools across `src/windows_mcp/tools/*.py` —
`input.py`: Click, Type, Scroll, Move, Shortcut, Wait, **WaitFor** (7); `snapshot.py`: Snapshot,
Screenshot (2); plus App, PowerShell, FileSystem, Process, Clipboard, Registry, Notification (7),
and `multi.py`: MultiSelect, MultiEdit (2), and Scrape (1). The **manifest.json `tools` array lists
18** — it omits **WaitFor** (WaitFor exists only in source/PyPI v0.8.1, not the bundled manifest).
A skill author should treat **19** as the live surface but expect manifest-driven clients to show 18.

All tools are namespaced **`mcp__windows-mcp__<Name>`** when reached from Claude Code. Parameter
names and types below are taken **directly from the v0.8.1 source** (`src/windows_mcp/tools/*.py`),
verified against the manifest. Every tool returns a **plain text string** (FastMCP `@mcp.tool`);
Screenshot/Snapshot additionally return an **image content block** when vision is on. There is no
structured JSON return — the agent parses the text. Booleans are accepted as real bools or the
strings `"true"`/`"false"`.

### Confirmed exact signatures (from source)
```python
Click(loc:[int,int]|None=None, label:int|None=None,
      button:"left"|"right"|"middle"="left", clicks:int=1)            # 0=hover 1=single 2=double
Type(text:str, loc=None, label=None, clear:bool=False,
     caret_position:"start"|"idle"|"end"="idle", press_enter:bool=False)
Scroll(loc=None, label=None, type:"horizontal"|"vertical"="vertical",
       direction:"up"|"down"|"left"|"right"="down", wheel_times:int=1)
Move(loc=None, label=None, drag:bool=False)                          # drag=True => drag-and-drop
Shortcut(shortcut:str)                                               # NOTE: param is `shortcut`, e.g. "ctrl+s"
Wait(duration:int)                                                   # NOTE: param is `duration` (seconds)
WaitFor(condition:str, text:str|None=None, window_name:str|None=None,
        timeout:float=10.0, interval:float=0.25, use_dom:bool=False) # see conditions below
App(mode:"launch"|"resize"|"switch"="launch", name:str|None=None,
    window_loc:[int,int]|None=None, window_size:[int,int]|None=None)
PowerShell(command:str, timeout:int=30)                             # tool default 30s; executor default 10s. returns "Response: <stdout>\nStatus Code: <n>". UTF-8 forced; prefers pwsh, falls back to powershell 5.1. Adds an "elevated terminal" HINT on "Access is denied" when not running as admin.
Registry(mode:"get"|"set"|"delete"|"list", path:str, name=None, value=None, type:RegistryType="String")  # path in PowerShell format e.g. HKCU:\Software\MyApp
MultiSelect(locs:[[x,y],...]|None=None, labels:[int,...]|None=None, press_ctrl:bool=True)  # labels need prior Snapshot
MultiEdit(locs:[[x,y,text],...]|None=None, labels:[[int_id,text],...]|None=None)            # labels need prior Snapshot
Notification(title:str, message:str, app_id:str)   # app_id = AUMID, REQUIRED for the toast to render
Scrape(url:str, query:str|None=None, use_dom:bool=False, use_sampling:bool=True)  # LLM-summarizes by default
FileSystem(mode:"read"|"write"|"copy"|"move"|"delete"|"list"|"search"|"info",
           path:str, destination=None, content=None, pattern=None,
           recursive=False, append=False, overwrite=False,
           offset=None, limit=None, encoding="utf-8", show_hidden=False)
Snapshot(use_vision:bool=False, use_dom:bool=False, use_annotation:bool=True,
         use_ui_tree:bool=True, width_reference_line=None,
         height_reference_line=None, display:[int]|None=None)
Screenshot(use_annotation:bool=False, width_reference_line=None,
           height_reference_line=None, display:[int]|None=None)      # always vision, never UI tree
Process(mode:"list"|"kill", name=None, pid=None,
        sort_by:"memory"|"cpu"|"name"="memory", limit:int=20, force=False)
Clipboard(mode:"get"|"set", text:str|None=None)                     # CF_UNICODETEXT (full Unicode)
```

**`WaitFor` conditions** (canonical, with accepted aliases):
`text_exists` (alias `text`), `active_window` (alias `window`), `element_exists` (alias `element`),
`element_enabled` (alias `enabled`), `focused_element` (alias `focused`). Validation rules:
`timeout` must be 0–120 s; `interval` 0–5 s; `text_exists` requires `text`; the element/window
conditions require `text` or `window_name`. It polls the a11y tree internally (no repeated Snapshot
calls) and raises `TimeoutError` on miss. This is the right "app is ready / dialog appeared /
control became enabled" primitive — strongly prefer over `Wait`.

**WaitFor timeout vs. transport timeout (avoid this bug):** `WaitFor`'s own `timeout` is capped at
120 s, but the **outer MCP call layer can also cut off near ~120 s** — so a single
`WaitFor {"timeout": 120}` risks the transport killing the call *before* WaitFor returns its own
clean `TimeoutError`, giving you an ambiguous failure. **Recommended pattern:** use a **short
WaitFor (e.g. 20–30 s) inside an agent-level retry loop** (call it N times) rather than one long
WaitFor. Each short call returns well within the transport budget, and the agent decides whether to
keep waiting — this also lets you interleave a `Screenshot` for visual progress between attempts.

For **Registry / MultiSelect / MultiEdit / Notification / Scrape**, signatures are per the manifest
descriptions in the table below (params confirmed by reading their modules: Registry uses
`mode`+path/name/type/value; Multi tools take `locs`/`labels`; Notification takes title/message;
Scrape takes a URL with SSRF guard).

### Observation
| Tool | Purpose | Key params | Returns |
|---|---|---|---|
| **Screenshot** | Fast visual capture; default first call for visual context. Skips tree extraction. | `display=[0]` or `[0,1]` (which monitors) | PNG image + cursor position + active/open windows. Image may be downscaled (scale ratio matters for clicks). |
| **Snapshot** | Full desktop state: focused/open windows, **interactive elements with ids + coordinates**, scrollable regions, system language. | `use_vision=True` (include screenshot), `use_dom=True` (browser DOM extraction), `display=[0]/[0,1]` | Structured element list with labels/ids/coords; optionally an image. This is what you click *by name* against. |

### Mouse / pointer
| Tool | Purpose | Key params |
|---|---|---|
| **Click** | Mouse click by coordinate **or** by element label/id. | `loc=[x,y]` OR `label`; `button` = left/right/middle; `clicks` = 0 hover / 1 single / 2 double. |
| **Move** | Move pointer, or drag-and-drop. | `loc=[x,y]` OR `label`; `drag=True` for drag from current pos to target. |
| **Scroll** | Scroll window/region/element. | `loc=[x,y]` or `label` or None(=mouse pos); `type` vertical/horizontal; `direction` up/down/left/right; `wheel_times` (1 wheel ≈ 3–5 lines). |
| **MultiSelect** | Select multiple files/folders/checkboxes (Ctrl-held) or multi-click. | `locs=[[x,y],...]` OR `labels=[...]`; `press_ctrl` bool. |

### Keyboard / text
| Tool | Purpose | Key params |
|---|---|---|
| **Type** | Type text into a field by coord or element. | `loc=[x,y]` OR `label`; `text`; `clear=True` (clear first) vs append; `press_enter=True` (submit); `caret_position` = start/end/idle. |
| **Shortcut** | Keyboard combos. | `shortcut` (param name is literally `shortcut`) like `"ctrl+c"`, `"alt+tab"`, `"win+r"`, `"win"`, `"ctrl+shift+esc"`. |
| **MultiEdit** | Fill several inputs at once. | `locs=[[x,y,text],...]` OR `labels=[[label,text],...]`. |

### Application & process control
| Tool | Purpose | Modes / params |
|---|---|---|
| **App** | Manage Windows apps. | `mode`: **launch** (open app from Start menu by `name`), **resize** (`window_loc=[x,y]`, `window_size=[w,h]` of named/active window), **switch** (focus window by `name`). NOTE: `launch` resolves via the **Start menu**, so it's reliable for installed apps but NOT for an arbitrary `.exe` path — use the PowerShell/`WScript.Shell` launch for raw build binaries. |
| **Process** | Process management. | `mode="list"` (filter/sort running processes) / `mode="kill"` (terminate by PID or name). |
| **PowerShell** | Execute arbitrary PowerShell. | `command` (string), `timeout:int=30` (seconds). Returns `"Response: <stdout>\nStatus Code: <n>"`. **The default 30 s timeout is a real constraint** — bump it for installers/long ops, and remember the outer MCP call layer can still cut off near ~120 s (chunk long work). The workhorse for headless ops, installs, queries, event-log/crash probes, and build ingestion. |

### Filesystem / clipboard / system
| Tool | Purpose | Modes / params |
|---|---|---|
| **FileSystem** | File ops; relative paths resolve from **Desktop**, absolute paths anywhere. | 8 modes: `read`, `write` (create/overwrite/append), `copy`, `move`, `delete`, `list`, `search` (glob), `info` (size/dates/type). |
| **Clipboard** | Windows clipboard. | `mode="get"` / `mode="set"` (text). |
| **Registry** | Windows Registry. | `mode`: `get`/`set`/`delete`/`list`; `path` in **PowerShell format** (`HKCU:\Software\MyApp`), `name`, `value`, `type` (default `'String'`). |
| **Notification** | Toast notification. | `title`, `message`, **`app_id` (required)** — a valid Application User Model ID (AUMID). Without a real AUMID the toast won't display, so a "task done" cue must pass a known app id (e.g. an installed app's AUMID). The agent-os skill's `Notification {"title","message"}` example is incomplete. |

### Timing / web
| Tool | Purpose | Key params |
|---|---|---|
| **Wait** | Pause N seconds. | `duration` (int seconds). Use sparingly; prefer `WaitFor`/polling. |
| **WaitFor** | Poll the a11y tree until a condition appears, inside one call. | `condition` ∈ {`text_exists`,`active_window`,`element_exists`,`element_enabled`,`focused_element`} (+ aliases text/window/element/enabled/focused); `text`, `window_name`, `timeout`≤120, `interval`≤5, `use_dom`. Raises TimeoutError on miss. The correct "app ready / dialog appeared / control enabled" primitive. |
| **Scrape** | Fetch content from a URL (HTTP) or active browser tab DOM. | `url`, `query` (focus extraction), `use_dom=False` (set True for active-tab DOM), `use_sampling=True`. **By default it LLM-summarizes** the page (via MCP client sampling) to avoid context bloat; `use_sampling=False` returns raw. Not central to `.exe` testing. |

> Note: `WaitFor` appears in the README tool list but not the manifest's `tools` array (manifest
> lists 18 incl. the others; treat `WaitFor` as present in current source/PyPI). Confirm exact
> param names against the live `/mcp` tool schema once connected.

### Tool gating (server-side)
The server can whitelist/exclude tools: `--tools "Screenshot,Click,Snapshot"` /
`--exclude-tools "PowerShell,Registry"` (env: `WINDOWS_MCP_TOOLS`, `WINDOWS_MCP_EXCLUDE_TOOLS`).
**Implication for a testing skill:** the target VM must NOT exclude `App`, `PowerShell`,
`FileSystem`, `Process`, `Snapshot`, `Screenshot`, or input tools, or the workflow breaks.

---

## 3. dockur/windows — the VM target

`dockur/windows` runs **Windows in a Docker container** (QEMU/KVM under the hood) with a web
viewer. Relevant facts for provisioning the desktop-test target:

- **Compose** (`compose.yml`): image `dockurr/windows`, `VERSION` env selects the Windows edition
  (e.g. `"11"`). Needs `/dev/kvm` (and `/dev/net/tun`), `cap_add: NET_ADMIN`, and a `data` volume
  mounted at `/storage` (the persisted disk). Ports: **8006** (noVNC web viewer / HTTP),
  **3389** TCP+UDP (RDP).
- **KVM acceleration required** for reasonable speed (host must expose `/dev/kvm`).
- **Persistence:** everything under `/storage` survives container restarts — installed software,
  registry, files. So a once-installed app + Windows-MCP server persist.
- **First-boot provisioning hooks:** dockur supports an **`/oem`** folder mounted into the guest
  during install, and an `install.bat` that auto-runs at first boot — the intended way to
  pre-install tooling (this is how Windows-MCP/uv would get baked in). Also supports unattended
  install, custom username/password, RAM/CPU/disk sizing env vars.
- **File-transfer caveat (critical, from CLAUDE.md):** dockur exposes the host folder as the SMB
  share **`\\host.lan\Data` only during install/OOBE**. Once Windows finishes setup, that share
  disappears — you cannot rely on it to push a freshly built `.exe` later. See §5 for the
  post-install transfer options.

### Authoritative compose config (read live from `dookie` this session)
Compose file: **`/home/jmagar/compose/windows/docker-compose.yml`** on `dookie` (verified present).
The real, current definition:
```yaml
services:
  windows:
    image: dockurr/windows
    container_name: agent-os-win11
    environment:
      VERSION: "11"
      RAM_SIZE: "8G"
      CPU_CORES: "4"
      DISK_SIZE: "256G"
      GPU_ENABLED: "Y"
    devices: [/dev/kvm, /dev/net/tun, /dev/dri, /dev/nvidia0, /dev/nvidiactl,
              /dev/nvidia-modeset, /dev/nvidia-uvm, /dev/nvidia-uvm-tools]   # GPU passthrough
    cap_add: [NET_ADMIN]
    ports:
      - 8006:8006          # noVNC web viewer
      - 33890:3389/tcp     # RDP (host 33890 -> guest 3389)
      - 33890:3389/udp
      - 2222:22            # guest SSH (host 2222 -> guest 22)
    volumes:
      - ./storage:/storage  # PERSISTED disk: installed sw, registry, Windows-MCP server survive
      - ./oem:/oem          # install-time provisioning (\\host.lan\Data during OOBE only)
    dns: [1.1.1.1, 8.8.8.8]
    networks: [app]
    restart: unless-stopped
    stop_grace_period: 2m
    # deploy.resources.reservations.devices: nvidia all (gpu, compute, video)
networks:
  app: { name: ${DOCKER_NETWORK:-windows}, external: true }   # external net "windows"
```
The `./oem/` folder already contains provisioning scripts (`fix_auth.ps1`, `inject_keys*.py`, etc.)
— this is how the SSH keys / Windows-MCP are injected at first boot. To bring the VM up the skill
runs `docker compose -f /home/jmagar/compose/windows/docker-compose.yml up -d` on `dookie` (the
external network `windows` must exist). **CLAUDE.md's `/home/jmagar/compose/windows/oem` path is
correct; its filename "compose.yml" is actually `docker-compose.yml`.**

### The concrete homelab instance: `agent-os`
> **Live status (this session): this VM is NOT running** — see the "Live-environment probe" section.
> The bullets below describe the *intended* topology when the container is up; treat ports/endpoints
> as available only after the skill starts the container and waits for boot.
- VM name **`agent-os`**, container **`agent-os-win11`**, image `dockur/windows`, on host
  **`dookie`**, over Tailscale.
- **noVNC** web desktop: `http://dookie:8006` (`/vnc.html?autoconnect=1&resize=remote`).
- **RDP**: `dookie:33890` (container-forwarded; no agent-side RDP client installed by default).
- **SSH to the guest**: `dookie:2222` → guest `:22` (`docker@100.88.16.79`). Forwarded by the
  container; whether sshd actually runs inside the guest depends on first-boot provisioning.
- **`/oem` drop folder** on host: `/home/jmagar/compose/windows/oem` → `\\host.lan\Data` at
  install time only.
- Per the agent-os SKILL.md, Windows-MCP is installed **inside** agent-os and exposed over
  **HTTP + Bearer token**, registered as the `windows-mcp` server (Tailscale URL). **Reconciliation
  (important):** the SKILL.md says "Claude Code reaches it automatically — nothing to start," but
  that assumes a *running* VM. In this session **(a) the VM container is absent (not running), and
  (b) I found NO `windows-mcp` entry in `~/.claude.json`** (searched top-level `mcpServers` and all
  project-scoped `mcpServers` — zero matches), nor in `~/.claude/settings.json`. So the "nothing to
  start / auto-connected" claim is **not currently true**: the registration is either gone, lives in
  a config not present here, or was only ever added in the environment where the VM ran. **The future
  testing-skill must NOT inherit the "auto-connected" assumption** — it must (1) start the VM, then
  (2) register/confirm the `windows-mcp` MCP server (URL+bearer) before the `mcp__windows-mcp__*`
  tools exist. The `mcp__windows-mcp__*` namespace is the expected shape *once registered*, but it
  was not loadable this session.

> **Open item — where the bearer/URL comes from when the VM is up.** I proved the `windows-mcp`
> registration is **not** in `~/.claude.json` (top-level or any project) or `~/.claude/settings.json`
> in *this* environment. So the skill author must answer "where does the token+URL come from at
> runtime?" Candidates, unconfirmed: (a) injected into the guest by the `./oem/*.ps1`/`inject_keys*.py`
> provisioning scripts (present in `/home/jmagar/compose/windows/oem/`) and surfaced from inside the
> VM; (b) added to a Claude config in the original environment where the VM ran (not this one);
> (c) generated by Windows-MCP's own `auth` helper inside the guest (`~/.windows-mcp/config.toml`).
> **The skill must establish/retrieve this credential as an explicit step, not assume it pre-exists.**

---

## 4. The interaction loop for testing a `.exe`

The LLM testing loop, end to end:

1. **Confirm environment.** Ensure the `windows-mcp` MCP server is reachable (the tools appear) and
   the VM is up. Optional sanity: `PowerShell {"command":"$PSVersionTable.OS"}` or `Screenshot`.
2. **Get the build onto the VM** (see §5). Land the `.exe`/installer at a known guest path, e.g.
   `C:\Users\<user>\Desktop\build\app.exe`.
3. **Un-quarantine.** Downloaded/copied binaries carry the MOTW zone flag → publisher/SmartScreen
   prompts. `PowerShell {"command":"Unblock-File -Path 'C:\\...\\app.exe'"}` and, when shelling
   into child exes, set `SEE_MASK_NOZONECHECKS=1`. Pre-create a Windows Firewall allow rule if the
   app listens on a port (else first-bind raises a desktop prompt that stalls unattended runs).
4. **Install (if it's an installer).** Run silently via PowerShell where possible
   (`Start-Process ... -Wait -ArgumentList '/S'` / MSI `msiexec /i app.msi /qn`), or drive the
   installer GUI with `App`+`Snapshot`+`Click`/`Type`.
5. **Launch the real binary.** Prefer the desktop-attached launch pattern (see gotchas in §8):
   `App {"mode":"launch","name":"App"}` for Start-menu apps, OR a `WScript.Shell` harness through
   `PowerShell` for arbitrary exes:
   ```powershell
   $ws = New-Object -ComObject WScript.Shell
   $null = $ws.Run('"C:\...\app.exe"', 1, $false)
   ```
6. **Wait for ready, not for time.** `WaitFor` on the app's main-window title / a known element,
   instead of fixed `Wait`. Confirm with `Snapshot`.
7. **Enumerate features from the control tree.** `Snapshot` → list every menu, button, tab, field.
   Build the feature checklist from the actual a11y tree (and/or a user-supplied feature list).
8. **Exercise each feature.** For each: `Click`/`Type`/`Scroll`/`Move` by **element label**
   (robust) falling back to coordinates; `Shortcut` for keyboard ops; `MultiEdit`/`MultiSelect`
   for forms/lists. **Critical mechanic:** `label` is the **integer id** from the *most recent*
   `Snapshot` (the server resolves it against the cached `desktop_state` and errors "call Snapshot
   first" if none exists). So the loop is: `Snapshot` → pick the target element's id → act by
   `label` → `Snapshot` again (the UI changed, ids are now stale) → repeat. After each action,
   capture state and check expected vs error UI.
9. **Detect failures.**
   - **Crashes/exits:** `Process {"mode":"list"}` — did the PID vanish? Check Windows Application
     event log via PowerShell: `Get-WinEvent -LogName Application -MaxEvents 50 | ? {$_.LevelDisplayName -in 'Error','Critical'}`.
   - **Hangs:** window stops responding / `WaitFor` times out / `Snapshot` shows "(Not Responding)".
   - **Error dialogs:** `Snapshot` surfaces dialog text/elements; screenshot for evidence.
   - **App stderr/stdout/logs:** if launched so output is redirected, `FileSystem read` the log.
10. **Capture evidence** continuously (see §6): screenshots + tree dumps + PowerShell-collected
    logs, keyed per feature/step.
11. **Reset between operations.** Kill/relaunch (`Process kill` → relaunch) between independent
    feature tests to avoid input/mode-state leaking across steps (a documented agent-os gotcha).
12. **Synthesize the report** (see §9): per-feature works / partial / broken + UX observations +
    evidence links.

---

## 5. Getting a built `.exe` into the VM (post-install)

The install-time SMB share is gone after OOBE, so use one of:

1. **SSH/SCP to the guest (cleanest if sshd runs).** `scp -P 2222 ./app.exe docker@100.88.16.79:` —
   container forwards `dookie:2222 → guest:22`. Verify sshd is actually up inside the guest first;
   not guaranteed unless provisioned.
2. **Pull from the host/network via PowerShell (most reliable, no extra setup).** Serve the build
   over HTTP from the host (e.g. a one-shot `python -m http.server` on `dookie`, or an existing
   homelab URL) and have the guest fetch it:
   `PowerShell {"command":"Invoke-WebRequest -Uri 'http://dookie:PORT/app.exe' -OutFile 'C:\\Users\\...\\Desktop\\app.exe'"}`.
   Works through Tailscale; no share needed. (Mind `Scrape`'s SSRF block does NOT apply here —
   that's the `Scrape` tool, not `Invoke-WebRequest` inside PowerShell.)
3. **`FileSystem write` (small/base64).** For small artifacts, write bytes directly via the
   `FileSystem` tool. Impractical for large binaries.
4. **Clipboard** for tiny text artifacts only — not binaries.
5. **RDP drive redirection** (`dookie:33890`) if a real RDP client is installed agent-side
   (freerdp) — heavier, not currently set up.
6. **Re-provision via `/oem`** only if you're willing to rebuild the VM (install-time only).

**Recommendation for the skill (all three transfer paths are UNVERIFIED in this research session —
see probe note below):** prefer **HTTP pull via PowerShell** (option 2) *if a preflight confirms the
guest can reach `dookie` over Tailscale* — i.e. the skill must first run
`PowerShell {"command":"Test-NetConnection dookie -Port <port>"}` (or a trial `Invoke-WebRequest`)
and only then commit to this path. It needs an HTTP source on `dookie`; no standing convention was
confirmed, so the skill should stand up an ephemeral server (`python -m http.server` on a chosen
port, opened in the host firewall) or reuse a known homelab URL. Fall back to **SSH/SCP** (option 1)
**only after** confirming guest sshd answers on `dookie:2222` (the agent-os skill flags this as
"depends on first-boot provisioning, unconfirmed"). In short: **the skill must probe both channels
at preflight and pick whichever responds** — do not hard-code either as guaranteed.

---

## 6. Capturing evidence for the report

- **Screenshots:** `Screenshot` returns the PNG to the agent (in-band). To persist as files for a
  report, either (a) save host-side from the returned image, or (b) capture **inside the guest**
  via PowerShell to a known folder and retrieve them:
  ```powershell
  Add-Type -AssemblyName System.Windows.Forms,System.Drawing
  $b = New-Object Drawing.Bitmap([Windows.Forms.Screen]::PrimaryScreen.Bounds.Width, [Windows.Forms.Screen]::PrimaryScreen.Bounds.Height)
  $g = [Drawing.Graphics]::FromImage($b); $g.CopyFromScreen(0,0,0,0,$b.Size)
  $b.Save('C:\evidence\step01.png')
  ```
  This guest-side path is also the documented fallback when the Windows-MCP Python env lacks `cv2`
  and `Snapshot`/`Screenshot` fail. Use `GetWindowRect` (user32) to capture a single window.
- **UI tree dumps:** persist each `Snapshot` element list as JSON per step — this is the
  machine-readable record of what controls existed and what the agent targeted.
- **Logs / state:** `Get-WinEvent` (crashes), app log files via `FileSystem read`, `Process list`
  snapshots (alive/CPU/responding).
- **UX signals to record:** unexpected layout/clipping, controls without accessible names (a11y
  gaps — visible in `Snapshot` as unlabeled elements), slow/blocking operations (latency between
  action and state change), missing feedback, error dialogs, focus traps.
- **Retrieval:** copy the guest `C:\evidence\` folder back to host via SCP (`-P 2222`) or an HTTP
  upload, then attach to the report under
  `~/.agents/docs/sessions/.../evidence/`.

---

## 7. Reaching the tools from THIS Claude Code environment

The agent-os skill states Windows-MCP is registered as the `windows-mcp` MCP server in
`~/.claude.json` (HTTP + Bearer, Tailscale URL). When that server is connected, tools appear as:

```
mcp__windows-mcp__Screenshot   mcp__windows-mcp__Snapshot    mcp__windows-mcp__Click
mcp__windows-mcp__Type         mcp__windows-mcp__Shortcut    mcp__windows-mcp__Scroll
mcp__windows-mcp__Move         mcp__windows-mcp__MultiSelect mcp__windows-mcp__MultiEdit
mcp__windows-mcp__App          mcp__windows-mcp__Process     mcp__windows-mcp__PowerShell
mcp__windows-mcp__FileSystem   mcp__windows-mcp__Clipboard   mcp__windows-mcp__Registry
mcp__windows-mcp__Notification mcp__windows-mcp__Wait        mcp__windows-mcp__WaitFor
mcp__windows-mcp__Scrape
```

> NOTE: In *this* research session the `windows-mcp` server was not connected (its tools are not in
> the loaded tool list), so I could not live-probe schemas — but I read the **v0.8.1 source**
> directly, so the signatures in §2 are authoritative for that version. A skill author should still
> run `/mcp` in a live session to confirm the server is up and the deployed version matches.
> **Reconcile with the agent-os SKILL.md:** that skill uses loose shorthand — it says `Shell` (the
> real tool is **`PowerShell`**), `Shortcut {"keys": ...}` (the real param is **`shortcut`**),
> `Wait {"seconds": ...}` (real param **`duration`**), `Clipboard {"action": "set"}` (real param
> **`mode`**), and `Registry {"action": "write"}` (real param **`mode`** with value `set`). Use the
> source-verified names in §2, not the skill's prose.

### Concrete example invocations
```jsonc
// 1. Orient
mcp__windows-mcp__Screenshot {}
mcp__windows-mcp__Snapshot {}                      // element ids + coords

// 2. Land + unblock + launch the build (bump PowerShell timeout for the download)
mcp__windows-mcp__PowerShell {"command": "Invoke-WebRequest -Uri 'http://dookie:8099/app.exe' -OutFile \"$env:USERPROFILE\\Desktop\\app.exe\"; Unblock-File \"$env:USERPROFILE\\Desktop\\app.exe\"", "timeout": 120}
mcp__windows-mcp__PowerShell {"command": "$ws = New-Object -ComObject WScript.Shell; $ws.Run('\"' + \"$env:USERPROFILE\\Desktop\\app.exe\" + '\"', 1, $false)"}

// 3. Wait for the window (source-verified WaitFor), then read the control tree.
//    Click/Type by label require a prior Snapshot (labels resolve against last desktop_state).
mcp__windows-mcp__WaitFor {"condition": "active_window", "window_name": "MyApp", "timeout": 60}
mcp__windows-mcp__Snapshot {"use_vision": true}    // returns interactive elements with integer ids/labels + image

// 4. Exercise a feature by element label (int id from the Snapshot) — fall back to coords.
//    NOTE: `label` is the INTEGER id from the latest Snapshot, not a human string.
mcp__windows-mcp__Click {"label": 12}              // e.g. the "File" menu id
mcp__windows-mcp__Snapshot {}                      // re-snapshot: menu opened, new ids
mcp__windows-mcp__Click {"label": 27}              // "Open"
mcp__windows-mcp__Type  {"loc": [640, 380], "text": "C:\\test\\input.csv", "press_enter": true}

// 5. Detect crash / errors
mcp__windows-mcp__Process {"mode": "list"}
mcp__windows-mcp__PowerShell {"command": "Get-WinEvent -LogName Application -MaxEvents 30 | ? {$_.LevelDisplayName -in 'Error','Critical'} | Select TimeCreated,ProviderName,Message | ConvertTo-Json"}

// 6. Evidence + done cue
mcp__windows-mcp__PowerShell {"command": "...CopyFromScreen save to C:\\evidence\\featureX.png..."}
mcp__windows-mcp__Notification {"title": "QA", "message": "Feature X pass", "app_id": "<a valid installed-app AUMID>"}
```

---

## 8. What the existing agent-os skill already covers — and what's missing

### Already covered (reuse as foundation)
- Connection model documented (HTTP+Bearer `windows-mcp` server; container persists `/storage`).
  *Caveat:* its "nothing to start / auto-connected" framing assumes a running, pre-registered VM —
  which was false this session (see §7 reconciliation); the testing-skill must add explicit
  VM-start + MCP-registration steps.
- Full tool inventory with sensible "prefer Snapshot over pixels; prefer PowerShell for headless"
  guidance.
- Recipes: open-app-and-act, headless PowerShell, click-by-element, winget installs, clipboard
  paste, notification, registry persistence.
- **A dedicated "Script and capture a desktop GUI app" section** with hard-won gotchas — this is
  the single most valuable prior art for `.exe` testing (see below).
- noVNC visual-fallback path and the `/oem`, RDP, SSH side-channels.

### Missing for a desktop-app-**testing** workflow
The agent-os skill is a *general driver*, not a *test harness*. A testing skill must add:
1. **Build ingestion** — a defined, repeatable way to get a fresh `.exe` into the VM
   post-install (the skill only documents `/oem` install-time + side-channels; no "push my latest
   build" recipe). → §5.
2. **Feature enumeration strategy** — turning a `Snapshot` tree (+ optional spec) into a test
   checklist, and iterating it exhaustively.
3. **Failure taxonomy & detection** — crash vs hang vs error-dialog vs silent-wrong-output, with
   the specific probes (`Process list`, `Get-WinEvent`, `WaitFor` timeout, "(Not Responding)").
4. **Evidence pipeline** — per-step screenshots + tree JSON + logs saved to a known guest folder
   and retrieved to host; naming/manifest convention. (Skill mentions writing a manifest beside
   PNGs but doesn't formalize it.)
5. **UX review rubric** — what "review UI/UX" means concretely (a11y labels present, feedback,
   latency, layout, error messaging).
6. **Report format** — the works/doesn't-work deliverable structure.
7. **State hygiene between tests** — kill/relaunch discipline (mentioned in gotchas, not as a rule).
8. **`WaitFor` usage** — the skill predates/omits it; it's the right primitive for "app ready",
   replacing fixed sleeps.

---

## 9. Gaps, gotchas & reliability notes (decisive for autonomy)

From CLAUDE.md, the agent-os skill's gotchas section, and tool semantics:

- **Element-based > coordinate-based clicking — ids come from `Snapshot`, NOT `Screenshot`.** Prefer
  `label` (the integer id from the a11y tree) over pixels: pixel clicks break on
  resize/scaling/downscaled screenshots/theme changes. **Source-verified caching rule** (`desktop/
  service.py`): `self.desktop_state = desktop_state` is **guarded by `if use_ui_tree:`**. So:
  - `Snapshot` (use_ui_tree=True) **refreshes** the cached state → ids become valid/updated.
  - `Screenshot` (use_ui_tree=False) **does NOT touch** the cache → a Screenshot taken between
    Snapshots leaves the previous Snapshot's ids valid (you can interleave cheap Screenshots for
    visual evidence without invalidating labels).
  - After any **UI change**, re-`Snapshot` to get fresh ids; a stale id resolves to the old element
    and clicks the wrong thing. Calling a `label` with no prior Snapshot raises "Desktop state is
    empty. Please call Snapshot first."
  When using raw coordinates from a downscaled `Screenshot`, multiply by `original/displayed` ratio
  (the Snapshot/Screenshot response text states the original size for this).
- **a11y tree blind spots.** Custom-drawn UIs (GPUI, some Electron/canvas/game engines) expose
  little/nothing to UI Automation → `Snapshot` is sparse, forcing pixel clicks + vision. Windows-MCP
  README itself notes text-selection limits because it relies on the a11y tree. **Apps that don't
  speak UI Automation are the main blocker to fully-autonomous testing.**
- **noVNC typing is unreliable** (the historical `Shift+<digit>` bug) — do NOT drive input through
  the noVNC canvas; use `Type`/`Shortcut`. noVNC is for *eyeballing* only.
- **Desktop-attached launch matters.** A non-interactive SSH-launched PowerShell could not
  foreground a GPUI window; the same script worked through Windows-MCP's PowerShell (it's attached
  to the interactive desktop). Use `WScript.Shell.Run` + `AppActivate`; `Start-Process` may leave
  synthetic input unreliable for some GUI frameworks.
- **Synthetic input into non-standard text inputs** (GPUI etc.) may ignore clipboard paste; literal
  `SendKeys('cmd{ENTER}')` was the reliable path in the Axon Palette session.
- **Security prompts stall unattended runs.** MOTW/SmartScreen publisher prompts (→ `Unblock-File`,
  `SEE_MASK_NOZONECHECKS=1`) and the first-bind Windows Firewall prompt (→ pre-create allow rule)
  must be handled before expecting hands-off captures.
- **MCP call timeout ~120 s.** Even with a higher requested timeout the call layer can cut off near
  120 s. Split long screenshot batches/operations into chunks; write a manifest beside outputs.
- **`cv2` missing** can break `Snapshot`/`Screenshot` → fall back to PowerShell
  `CopyFromScreen` capture.
- **Tool gating** on the server could hide required tools (`--exclude-tools`) — verify the target
  VM exposes the full set.
- **Not for games / heavy custom rendering** (README explicitly excludes games).
- **Single primary display assumed** by most coordinate logic; use `display=[...]` deliberately.
- **English-default Windows** preferred (the `App` Start-menu launch is language-sensitive).

**Net autonomy assessment:** For standard Win32 / WinForms / WPF / WinUI apps (good UI Automation
support), fully-autonomous feature testing is realistic. For custom-rendered apps (GPUI, canvas,
some Electron), the agent degrades to screenshot+vision+SendKeys and needs more human-seeded hints
(known window titles, coordinates) — partially autonomous.

---

## 10. Recommendation — shape of a future `desktop-app-testing` skill

**Name/trigger:** "test a windows app", "run E2E on this .exe", "QA my desktop build on agent-os",
"does my exe work in the windows VM". Companion to (not replacing) `agent-os`; it *invokes*
`mcp__windows-mcp__*`.

**Inputs:** path to built `.exe`/installer (host), optional feature/spec list, optional known
window title(s), target VM (default agent-os).

**Workflow (codified):**
1. **Preflight** — confirm `windows-mcp` connected (`/mcp`), VM up, required tools present,
   evidence dir created guest-side (`C:\evidence\<run-id>\`).
2. **Ingest build** — HTTP-pull via PowerShell (primary) or SCP `-P 2222` (alt); `Unblock-File`;
   pre-create firewall rule if the app is a server.
3. **Install/launch** — silent install if installer; launch via `WScript.Shell.Run` + `AppActivate`
   (or `App launch`); `WaitFor` main window; `Snapshot` confirm.
4. **Enumerate** — `Snapshot` → derive feature checklist (merge with supplied spec). One bead/row
   per feature.
5. **Exercise loop** — per feature: act by label → `Snapshot`/`Screenshot` evidence → classify
   (pass / partial / fail) with probes (`Process list`, `Get-WinEvent`, `WaitFor` timeout). Kill +
   relaunch between independent features.
6. **UX pass** — score a fixed rubric (a11y labels, feedback, latency, layout, error messaging)
   from the captured trees + screenshots.
7. **Collect** — pull `C:\evidence\<run-id>\` (PNGs + per-step tree JSON + logs + manifest.json)
   back to host.
8. **Report** — write markdown to `~/.agents/docs/sessions/.../report.md`.

**Automation to ship in the skill** (`scripts/`): a guest-side PowerShell helper for
ingest+unblock+firewall+launch+screenshot-to-folder (avoids re-deriving the harness each run), and
a host-side fetch script for evidence retrieval.

**Report format:**
```markdown
# QA Report — <App> <version> — <date> (run <id>)
## Summary: X/Y features pass · N partial · M broken · <crash?>
## Environment: agent-os (dookie), Windows 11, build path, transfer method
## Feature results (table): Feature | Steps | Result | Evidence | Notes
## Failures (detail): repro steps, error text/event-log excerpt, screenshot
## UX review: a11y labels, feedback, latency, layout, error messaging — scored
## Crashes/hangs/errors: timeline + event-log entries
## Evidence index: links to PNGs / tree JSON / logs
## Recommendation: ship / fix-then-ship / blocked
```

**Reliability rules to bake in:** prefer element labels over coords; `WaitFor` not `Wait`; chunk
work under the ~120 s MCP timeout; handle MOTW/SmartScreen/Firewall prompts up front; kill/relaunch
between tests; fall back to PowerShell `CopyFromScreen` if `Snapshot`/`Screenshot` fails; treat
sparse a11y trees as a signal to switch to vision+SendKeys and flag reduced confidence in the
report.

---

## Live-environment probe (this session) — KEY FINDING

I ran read-only probes against the homelab. Results:

- **SSH to `dookie` works** (`ssh dookie 'hostname'` → exit 0; egress is **not** blocked).
- **The `agent-os` / Windows VM container is NOT currently running on `dookie`.** `docker ps -a`
  there lists **44 containers, none** matching `agent-os`, `win*`, or `dockur`. So as of this
  session there is **no `agent-os-win11` container at all** (not stopped — absent).
- Consequently `dookie:8006` (noVNC) and `dookie:2222` (guest SSH) refused direct `/dev/tcp`
  connections, consistent with the VM being down.
- The `windows-mcp` MCP server is **not connected** in this Claude Code session (its tools are
  absent from the loaded tool list) — expected, since the VM it lives in isn't running.

**Implication for the skill (critical):** the target VM is **not a standing always-on resource** —
it may be absent and need to be (re)created/started before any testing. The future skill's
**preflight is non-optional** and must: (1) SSH `dookie`, (2) check for the windows container
(`docker ps`), (3) start/create it if missing (it persists `/storage`, so a recreate keeps installed
software + the Windows-MCP server), (4) wait for boot, (5) confirm `/mcp` shows `windows-mcp`,
(6) confirm a working build-transfer channel. Everything in §3/§5/§7 about the running VM is the
*documented design* (from `~/.claude/CLAUDE.md` + agent-os SKILL.md); the **live state is "VM not
present right now."**

## Appendix — verification still owed (could not live-probe this session)
- Exact tool **parameter names/types** from the live `/mcp` schema or `src/windows_mcp/tools/*.py`
  (manifest descriptions used here; `PowerShell` vs the skill's `Shell` alias to be reconciled).
- Whether guest **sshd** is actually running on agent-os `:2222`.
- Whether the target VM **excludes** any required tools.
- `WaitFor` exact signature (text/window/element/focused-element param names). **RESOLVED from
  source** — see §2; conditions are `text_exists`/`active_window`/`element_exists`/
  `element_enabled`/`focused_element` with params `text`, `window_name`, `timeout`, `interval`,
  `use_dom`.

### Also resolved during this research (no longer owed)
- All 18 tool signatures are now source-verified (§2).
- `PowerShell` returns `"Response: <stdout>\nStatus Code: <n>"` and forces UTF-8; tool-level
  `timeout` default 30 s, underlying executor default 10 s.
- `Notification` requires `app_id` (AUMID).
- `Scrape` LLM-summarizes by default (`use_sampling`).
- `label` is an integer id valid only against the most-recent `Snapshot` (the
  `desktop.desktop_state` cache); a stale id clicks the wrong element.
