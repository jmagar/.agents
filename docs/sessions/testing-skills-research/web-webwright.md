# Webwright — Research Notes for a Future Web-App-Testing Skill

Research date: 2026-05-29
Sources studied:
- Upstream repo: `~/workspace/Webwright/` (Microsoft Research, MIT, v0.1.0, ~1.5k LoC Python)
- Installed Claude Code skill: `~/.claude/plugins/marketplaces/webwright/skills/webwright/`
  (a **homelab-customized fork** of the upstream skill — see "Upstream vs Installed" below)
- Homelab memory: `~/.claude/projects/-home-jmagar-workspace-lab/memory/feedback_webwright_playwright.md`
- Context on sibling tooling: `agent-browser`, `chrome` skill, Chrome CDP (from `~/.claude/CLAUDE.md`)

---

## 1. What Webwright is, mechanically

Webwright is a **code-as-action browser agent**. The thesis (Microsoft Research blog
"A Terminal Is All You Need For Web Agents"): instead of an agent predicting one
low-level browser action per turn against a *stateful* browser session, give a
*coding* agent a **terminal**, and let it write/run/inspect/repair **Python
Playwright scripts**. The persistent artifact is **not the browser session** — it's
**the code, screenshots, and logs in a local workspace**. The browser is disposable;
each script reconstructs state from scratch.

There are **two distinct things both called "Webwright"** and the distinction is the
single most important fact for building on it:

### (A) The upstream Python package (`webwright`) — a self-contained LLM agent
- Language: **Python ≥3.10**. Deps: `httpx`, `pydantic`, `playwright`, `typer`. ~1.5k LoC.
- It runs its **own** LLM loop. A model backend (OpenAI / Anthropic / OpenRouter,
  `src/webwright/models/`) is called; the model emits **one JSON-wrapped `bash_command`
  per turn**; the harness executes that bash command in a `local_workspace` +
  `local_browser` (Playwright) environment, feeds back stdout/stderr, and repeats.
- Two helper tools call the model with an image: `tools/image_qa.py` (visual Q&A on a
  screenshot) and `tools/self_reflection.py` (final success verdict). These exist
  because the harness model can't natively see images well / needs a structured gate.
- Entry point: `python -m webwright.run.cli` (a `typer` CLI, `src/webwright/run/cli.py`).
- Config is **stackable YAML** from `src/webwright/config/`: `base.yaml` (the system/
  instance prompt + workspace contract), `model_openai.yaml` / `model_claude.yaml` /
  `model_openrouter.yaml` (backend), plus overlays `task_showcase.yaml`,
  `crafted_cli.yaml`, `local_browser.yaml`, `persistent_browser.yaml`.
- Run invocation:
  ```bash
  python -m webwright.run.cli \
      -c base.yaml -c model_openai.yaml \
      -t "Search for flights from SEA to JFK on 2026-08-15 to 2026-08-20" \
      --start-url https://www.google.com/flights \
      --task-id demo_openai \
      -o outputs/default
  ```
  Flags: `-c` config (stackable), `-t` task, `--start-url` initial page,
  `--task-id` output subfolder, `-o` output dir. Requires an API key for the chosen
  backend (`OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / OpenRouter).

### (B) The Claude Code skill (`webwright:webwright`) — the host agent IS the loop
- **This is what we would build on.** The skill *removes* the upstream Python agent
  loop and the model backends entirely. Claude Code itself plays the role of the
  "model": it uses the **`Bash` tool** exactly where the upstream harness used the
  `bash_command` field, **no JSON wrapping**, one bash command per turn.
- It keeps the upstream **workspace contract** (`plan.md`, `final_runs/run_<id>/`,
  instrumented `final_script.py`, screenshots, action log) but **replaces** the
  OpenAI-backed `image_qa` / `self_reflection` tools with Claude's **native vision**:
  Claude reads PNG screenshots with the `Read` tool and verifies success against
  `plan.md` by reasoning. **No API keys are needed for the skill.**
- The skill is plain Markdown + reference files; there is **no running daemon, no
  MCP server**. It is pure prompt/contract + the host's Bash/Read/Write/Edit tools.
- `allowed-tools: Bash, Read, Write, Edit, bash, read_file, write_file`.

So in Claude Code: Webwright = "a disciplined contract for Claude to write, run,
screenshot, and self-verify Playwright scripts in a structured workspace." The LLM
drives by **generating free-form async Python Playwright scripts** (via heredocs for
exploration, via `Write`/`Edit` for `final_script.py`) and running them with Bash.

### Package internals worth knowing (`agents/default.py`, `base.yaml`)
These are the upstream package's mechanics — the skill *reimplements the spirit* of
them using Claude's native turn loop:
- **Strict JSON action protocol (package only):** each model turn returns one JSON object
  `{thought, bash_command, done, final_response}`. Exactly one shell command per turn;
  Python runs via heredoc inside `bash_command`. `done=true` may not share a turn with a
  non-empty command. (The Claude Code skill drops this — plain Bash calls, no JSON.)
- **`step_limit: 100`** (the benchmark budget), `command_timeout_seconds: 240`,
  `max_output_tokens: 4000`, `output_truncation_chars: 24000`.
- **Self-reflection completion gate (`require_self_reflection_success: true`):** the
  agent literally **cannot** set `done=true` until
  `final_runs/run_<latest>/self_reflect_result.json` exists with `predicted_label == 1`
  (enforced in code by `_tool_gate_error`). `self_reflection` (a 2-stage VLM judge:
  per-image score 1–5, then one aggregated `Status: success|failure` verdict) is the
  upstream "visual verification." **The Claude Code skill replaces this entire gate with
  Claude reading PNGs and ticking `plan.md` itself** — no JSON judge file.
- **Observations** are not screenshots by default (`attach_observation_screenshot:false`,
  "Step screenshots are NOT automatically attached"): the model gets the command's
  stdout/stderr/return-code + ARIA text, and must *invoke* `image_qa` to see a PNG.
  Claude Code's native vision removes this two-step dance.
- **Context management:** ARIA snapshots in old observations get pruned
  (`keep_last_n_observations`), and history is LLM-summarized every
  `summary_every_n_steps` (20) — relevant if a testing skill runs long.
- **Artifacts the package writes:** `trajectory.json` (full message log,
  `trajectory_format: webwright-0.1`) + `debug/steps.md` + `debug/steps/step_NNNN.json`.
  The Claude Code skill keeps only the `final_runs/` workspace artifacts (the chat
  transcript replaces `trajectory.json`).

---

## 2. Complete capability surface

Because the action space is **free-form Python Playwright**, the capability surface is
"all of Playwright" — not a fixed verb list. In practice the skill emphasizes:

- **Navigation:** `page.goto(url, wait_until="domcontentloaded")`, multi-page flows by
  re-navigating + reapplying state each run (no persistent session).
- **Observation (two channels):**
  - **DOM/accessibility:** `await page.locator("body").aria_snapshot()` (the *primary*
    cheap observation — print ARIA tree, URL, title, visible labels every step);
    `evaluate` / `evaluate_all` to read form state (`aria-label`, `value`, hidden).
  - **Visual:** `await page.screenshot(path=...)` then `Read` the PNG natively.
    **Hard rule: viewport `{"width":1280,"height":1800}`, NEVER `full_page=True`.**
- **Click / interact:** `get_by_role("button", name=...).click()`, `.check()` checkboxes,
  role+name targeting preferred over brittle CSS classes. Snapshot the *parent* of a
  control (`.locator("..")`) to enumerate sibling options.
- **Type / form-fill:** type value → wait for suggestion listbox → click the option
  containing the canonical token. **Prefer interactive form-filling over deep-link
  URLs** (deep links silently drop params, vary by locale/A-B/auth). For paired fields
  in one modal (date-range pickers, steppers), open the modal **once** and `Tab`
  between fields. Always click an explicit submit control, not auto-submit.
- **Data extraction:** read text/values via locators + `evaluate`, print the final
  datum to stdout and into the log.
- **Assertions / visual verification:** there is no `expect()`-style framework; the
  verification model is the **Critical Points checklist** in `plan.md`, proven by
  cited screenshots and log lines, judged by Claude reading the PNGs (this *is* the
  "visual verification" — it replaces `self_reflection`).
- **Error detection:** crashes surface as Python tracebacks in stdout/stderr;
  navigation/blocker detection ("Access Denied", missing controls) requires repeated
  on-site UI evidence before being accepted. (Note: the skill does **not** wire up
  console-error or network-failure capture by default — see Gaps §7.)
- **Two output modes** (see §4): one-shot script vs. parameterized CLI tool.
- **Task2UI / Task Showcase** (upstream only): with `-c task_showcase.yaml`, a run also
  emits `task.json` + `report.json` (structured: sources + result sections) renderable
  by a tiny Flask dashboard (`assets/task_showcase/app.py`, port 5005). Plain `base.yaml`
  runs produce `trajectory.json` + debug artifacts but **no `report.json`**.

### Run-artifact layout (the workspace contract)
```
WORKSPACE_DIR/                       # e.g. outputs/<task_id>/  — work ONLY here
├── plan.md                          # Task + numbered Critical Points checklist
│                                    #   (+ # Parameters table in CLI/craft mode)
├── screenshots/                     # scratch EXPLORATION pngs (explore_<n>_<action>.png)
└── final_runs/
    └── run_<id>/                    # <id> = next integer above any existing run_*
        ├── final_script.py          # the required final artifact
        ├── final_script_log.txt     # reset each clean run; "step <n> action: ..." lines;
        │                            #   FINAL_RESPONSE: <datum> at the end
        │                            #   (CLI mode: first line "step 0 params: k=v ...")
        └── screenshots/
            └── final_execution_<step>_<action>.png   # one per Critical Point
```
Each `final_execution_*.png` should map 1:1 to a CP in `plan.md` so verification is
trivial. Upstream (package) instead writes `trajectory.json` and (with the overlay)
`task_showcase/tasks/<short_id>/{task.json,report.json}`.

---

## 3. The exact LLM interaction loop (Claude Code skill)

Six steps, one Bash command per turn, observe output before the next:

1. **Plan.** Parse the task into *Critical Points* (CPs) — every explicit constraint,
   filter, sort, selection, required datum. Write `WORKSPACE_DIR/plan.md`:
   ```markdown
   # Task
   <verbatim task>
   # Critical Points
   - [ ] CP1: <independently verifiable requirement>
   - [ ] CP2: ...
   ```
   Numeric/date/quantity/unit CPs are **exact**; ranking CPs ("cheapest", "highest-rated")
   must reference the site's *actual* sort/filter control; a required final datum is its
   own CP.
2. **Explore.** Run scratch Playwright scripts (heredoc style) to discover stable
   selectors and confirm each filter control exists. Print URL/title/ARIA every step;
   `Read` saved PNGs when ARIA is ambiguous; expand drawers/accordions/mobile filter
   panels before concluding a control is missing.
3. **Author `final_script.py`** in a fresh `final_runs/run_<id>/`, instrumented:
   reset the log, one `step <n> action:` line per constraint-relevant action, a uniquely
   named screenshot per CP, final datum printed at the end.
4. **Execute** the final script once; capture stdout/stderr. If it crashes, fix in place
   and re-run, deleting stale screenshots so the folder reflects one clean run.
5. **Self-verify** (replaces `self_reflection`). For each CP: cite a screenshot and/or
   log line, `Read` the PNG, confirm evidence is **unambiguous** (filter chip visible /
   date exact / sort applied via control / submit visibly taken / datum legible). Be
   harsh on occluded/partial states. On failure, diagnose the *specific* issue, fix,
   re-run in `run_<id+1>/`, re-verify. Empty result sets are OK if filters were
   demonstrably applied.
6. **Done** only when every CP is ticked with cited evidence; report the final datum
   verbatim (and it's in `final_script_log.txt`).

**Observation = screenshot AND DOM/AX.** ARIA snapshots are the cheap default; PNG
screenshots are the verification/disambiguation channel that Claude reads natively.
**Error detection** is primarily: Python tracebacks (script failures), ARIA/visual
absence of expected controls, and explicit on-site blocker text — *not* automated
console/network instrumentation.

---

## 4. `webwright:webwright` vs `webwright:craft` vs `webwright:run`

All three are the **same skill + workflow**; the difference is the output shape and how
they're triggered:

| Entry | What it is | Output shape | When |
|---|---|---|---|
| `webwright:webwright` (the skill) | The full code-as-action workflow + contract. Auto-activates from its description on any "automate this web task with reusable scripts + screenshot evidence" prompt. | Default = one-shot. | Plain English web-task prompts; the umbrella skill the other two invoke. |
| `webwright:run` | A slash-command **template** that hands `$ARGUMENTS` to the skill in **one-shot mode**. `commands/run.md`. | `final_script.py` solves the task for the **literal** values. Explicitly "Do NOT use CLI tool mode." | Quick "just do this web task once." |
| `webwright:craft` | Slash-command template for **CLI-tool / parameterized mode**. `commands/craft.md` + `reference/cli_tool_mode.md`. | `final_script.py` = **one reusable function** with Google-style `Args:` docstring + an `argparse` wrapper whose `--flags` default to the concrete task values; **import-safe** (no side effects at import). | "Make it reusable / parameterize / turn into a CLI / I'll rerun with different X." |

CLI/craft mode adds to the contract: a `# Parameters` table in `plan.md`
(`name|type|source phrase|default|allowed/format`), every param → one function arg +
one argparse flag (default = original task value, so no-arg run reproduces the task),
a mandatory `step 0 params: k=v ...` first log line, an **import-safety smoke test**
(import the module in a fresh process; no browser launch), an optional second run with
a different arg, and ending by printing `--help`. Example reuse:
`python final_script.py --origin JFK --destination LAX --depart-date 2026-07-01`.

(Upstream package equivalents: default = `base.yaml`; craft = `crafted_cli.yaml`
overlay; the `webwright:run` one-shot maps to `base.yaml` without the CLI overlay.)

---

## 5. Prerequisites & setup

### Upstream package (if running the Python agent directly)
```bash
pip install -e .
playwright install chromium
export OPENAI_API_KEY=...      # or ANTHROPIC_API_KEY / OpenRouter, per chosen -c model_*.yaml
```

### Installed Claude Code skill (homelab fork — what we have here)
- **No API keys.** Host vision replaces `image_qa`/`self_reflection`.
- Python venv for Playwright (one-time), because system pipx playwright 1.60 is
  incompatible with the installed browsers on Ubuntu 26.04:
  ```bash
  uv venv /tmp/pw_venv --python 3.12
  uv pip install --python /tmp/pw_venv/bin/python "playwright>=1.59,<1.60"
  ```
- **Always invoke scripts as** `/tmp/pw_venv/bin/python script.py`.
- **Browser strategy (the fork's key customization, and an internal inconsistency to
  fix in any derived skill — see §6):**
  - `playwright_patterns.md` (installed) says: **default = connect to the persistent
    `axon-chrome` container (Chromium 134, headless) via
    `playwright.chromium.connect_over_cdp("http://127.0.0.1:9222")`**; **use
    `context.close()` / `ctx.close()`, NEVER `browser.close()`** (so axon-chrome stays
    alive for the Axon RAG pipeline). Fallback to local Firefox
    (`playwright.firefox.launch(headless=True)` with
    `PLAYWRIGHT_BROWSERS_PATH=/home/jmagar/.cache/ms-playwright`) for Akamai/Chromium-
    blocked sites (`ERR_HTTP2_PROTOCOL_ERROR` from TLS/H2 fingerprinting).
  - `SKILL.md` (installed) text still says "every run launches a fresh **Firefox** via
    `playwright.firefox.launch(headless=True)`" — **stale/contradicts** the reference
    file. Treat `playwright_patterns.md` (CDP-to-axon-chrome, Chromium) as the intended
    default for this homelab.
- Artifacts land in the chosen `WORKSPACE_DIR` (typically `outputs/<task_id>/`).
- Headless throughout; viewport fixed at 1280×1800; never `full_page=True`.

### Upstream skill (microsoft/Webwright, for comparison)
The pristine upstream `skills/webwright/` uses **local Firefox**
(`playwright.firefox.launch(headless=True)`, prereq `playwright install firefox`) as its
default engine — Firefox is chosen because some sites throw `ERR_HTTP2_PROTOCOL_ERROR`
under Chromium (TLS/H2 fingerprinting). No axon-chrome, no CDP, no `/tmp/pw_venv`. The
homelab fork swapped the default to the persistent axon-chrome Chromium over CDP (:9222),
kept Firefox only as a fallback, and added the uv-venv Playwright workaround.

### Upstream *package* (base.yaml system prompt) browser modes
Separately from the skill, the upstream **Python package** `base.yaml` defines
`browser_mode` with two values exposed to generated scripts as `BROWSER_MODE`:
`browserbase` (default — a Browserbase **cloud** session via `BROWSERBASE_API_KEY` /
`BROWSERBASE_PROJECT_ID`, connected over CDP) and `local` (a local
`playwright.chromium.launch(...)`, no creds). So the package's "local" mode is Chromium;
the *skill's* local mode is Firefox; the *fork's* default is CDP Chromium. Three
different browser stories — name them explicitly in any derived skill.

---

## 6. Upstream vs Installed (reconciliation)

`diff -rq` of `~/workspace/Webwright/skills/webwright/` vs the installed skill:
- `SKILL.md` **differs** (fork: uv venv prereqs, axon-chrome/Firefox notes, "no API key").
- `reference/playwright_patterns.md` **differs** (fork: `connect_over_cdp` to
  `127.0.0.1:9222`, `ctx.close()`, Firefox fallback, `/tmp/pw_venv`).
- `reference/workflow.md`, `reference/cli_tool_mode.md`, `commands/run.md`,
  `commands/craft.md` are **identical** to upstream.
- The installed dir also has a leftover `SKILL.md.orig` (the pre-fork upstream copy) —
  evidence this was hand-patched in place.
- **Internal inconsistency in the fork:** SKILL.md says Firefox-default; the reference
  says Chromium-CDP-default. Any new skill must pick one and make both files agree.

Net: the installed skill is the upstream Microsoft skill, **re-pointed at the homelab's
persistent axon-chrome Chromium (CDP :9222)** with a uv-venv Playwright and a Firefox
fallback, and stripped of API-key requirements.

---

## 7. Capturing evidence for a works/doesn't-work report

What Webwright already gives you, per run:
- **Screenshots** — one `final_execution_<step>_<action>.png` per Critical Point, plus
  scratch `explore_*` PNGs. Read natively for the visual/UX judgment.
- **Action log** — `final_script_log.txt`: ordered `step <n> action: ...` lines (a
  human-readable trajectory) + `FINAL_RESPONSE: <datum>`; CLI mode adds `step 0 params:`.
- **The script itself** — `final_script.py` is a re-runnable record of exactly what was
  done (the "browsing history as a single code file").
- **Pass/fail verdict** — the `plan.md` Critical Points checklist, each ticked with cited
  evidence; this is the natural backbone of a works/doesn't-work report.
- **Structured report (upstream Task Showcase only)** — `report.json` (sources + tables/
  lists/summaries) + Flask dashboard, when `-c task_showcase.yaml` is stacked.

What it does **not** capture out of the box (must be added for a real test report):
- **Console errors** — not collected. Add `page.on("console", ...)` / `page.on("pageerror", ...)`.
- **Network failures** — not collected. Add `page.on("response", ...)` / `page.on("requestfailed", ...)`
  to flag 4xx/5xx and failed requests.
- **Failed navigation / HTTP status** — capture `response = await page.goto(...)` and
  assert `response.status`.
- **Timing/perf, accessibility audit, coverage** — none; would need explicit additions.

---

## 8. Gaps & gotchas vs `agent-browser` and the `chrome` skill

| | `agent-browser` (Vercel CLI) | `chrome` skill (CDP over SSH) | **Webwright (skill)** |
|---|---|---|---|
| Form factor | Global npm CLI; discrete subcommands (`open`, `click @e2`, `snapshot`, `eval`); daemon holds a session across calls | One-shot CDP calls to a real Chrome over SSH (the user's tab) | Markdown contract; Claude writes free-form Playwright **Python** scripts |
| Action space | Fixed verbs (click/type/snapshot/eval) | Eval JS, navigate, screenshot, read console/network on the live tab | **All of Playwright** (loops, functions, waits, abstractions) |
| State | Browser session (daemon) | The user's live browser session | **Workspace** (code+screenshots+logs); browser disposable |
| Reusable artifact | No (ephemeral commands) | No | **Yes** — `final_script.py` re-runnable, optionally a parameterized CLI tool |
| Evidence trail | Per-call output | Live, manual | **Built-in** — per-CP screenshots + ordered action log + plan.md verdict |
| Console/network capture | Some, via subcommands | Native (`chrome` reads console/network) | **Not by default** — must add Playwright listeners |
| Best at | Fast micro-interactions, dogfooding, quick scrape | Inspecting/driving an *already-open* real Chrome tab | **Repeatable, evidence-rich, multi-step flows; long-horizon tasks** |

What Webwright uniquely gives us for app testing: (1) a **reusable script** that encodes
the exact test, re-runnable in CI or as a regression check; (2) a **structured evidence
bundle** (screenshots mapped to requirements + action log) that *is* a test report
skeleton; (3) a **disciplined verification gate** (Critical Points, harsh visual
self-check) that maps cleanly onto "works / doesn't work per feature." `agent-browser`
and `chrome` are better for fast, live, one-off interaction but leave no durable,
re-runnable, evidence-bearing artifact.

Gotchas: no persistent browser state between scripts (each run reconstructs); fixed
1280×1800 viewport / no full-page screenshots (so above-the-fold framing matters);
homelab Chromium-vs-Firefox inconsistency in the fork; console/network/HTTP-status
evidence must be added; on Ubuntu 26.04 you must use the `/tmp/pw_venv` Playwright, not
system pipx; `ctx.close()` not `browser.close()` to keep axon-chrome alive.

---

## 9. Recommendation: shape of a future "web-app-testing" skill

**Build a NEW sibling skill (e.g. `web-app-test`) that adopts Webwright's contract,
rather than wrapping the installed `webwright` skill directly.** Reasons: the testing
goal is "exercise *every* feature and produce a works/doesn't-work + UX report," which
needs (a) **discovery/coverage of all operations** (not a single user-specified task),
(b) **console/network/HTTP-status capture** (Webwright omits these), and (c) a
**fixed report format**. Webwright's skill is task-completion-oriented and would need
enough additions that a clean sibling is cleaner than overriding it. But it should be
an *explicit Webwright derivative* — reuse the contract verbatim where it fits.

Concretely, the new skill should:

1. **Reuse the Webwright workspace contract wholesale:** `plan.md` (here = a **feature
   inventory checklist** instead of task Critical Points), `final_runs/run_<id>/`,
   instrumented `final_script.py`, per-step screenshots, `final_script_log.txt`,
   `ctx.close()`, 1280×1800 viewport, `/tmp/pw_venv` Playwright, axon-chrome CDP default
   with Firefox fallback. Fix the Firefox/Chromium inconsistency up front.
2. **Add a discovery phase** before planning: crawl the target app (nav menu, routes,
   buttons, forms) via ARIA snapshots to **enumerate features/operations**, then write
   each as a checklist item ("FEAT-n: <feature> — <expected behavior>"). This is the
   key addition over Webwright's user-supplied single task.
3. **Mandate instrumentation Webwright lacks**, baked into the `final_script.py`
   skeleton: `page.on("console")` + `page.on("pageerror")` → log console errors;
   `page.on("requestfailed")` + response-status checks → log network/HTTP failures;
   capture `goto` response status; one screenshot per feature exercised.
4. **Per-feature verdict loop** (Webwright's self-verify, generalized): for each FEAT,
   drive it, screenshot, read the PNG, check for console/network errors, mark
   PASS / FAIL / BLOCKED with cited evidence (screenshot path + log lines + error text).
5. **Fixed report deliverable** — a `report.md` (and/or reuse the upstream Task Showcase
   `report.json` + Flask dashboard for a browsable HTML view): a results table
   (feature | status | evidence | notes), a UI/UX observations section (layout, flow,
   broken/empty states, latency), the console/network error inventory, and a final
   works/doesn't-work summary. This mirrors what's wanted for Android/desktop apps.
6. **Two run modes** like Webwright: a one-shot full sweep, and a `craft`-style
   parameterized variant (e.g. run against staging vs prod URLs, or per-feature reruns).
7. **Cross-platform symmetry:** keep the report schema and verdict vocabulary
   (PASS/FAIL/BLOCKED + evidence) identical across web/Android/desktop so the three
   testing skills produce comparable reports.

In short: **fork the Webwright *contract*, not the Webwright *skill file*.** Webwright
supplies the proven scaffolding (code-as-action Playwright + screenshot evidence +
plan-driven verification + reusable scripts); the new skill adds feature-discovery,
error instrumentation, and a fixed test-report format on top.
