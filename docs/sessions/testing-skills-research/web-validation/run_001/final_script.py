import sys, json, datetime
from playwright.sync_api import sync_playwright

RUN_DIR = sys.argv[1] if len(sys.argv) > 1 else "."
CDP = "http://127.0.0.1:9222"
log = []
def step(msg):
    line = f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}"
    log.append(line); print(line, flush=True)

console_errors, page_errors, failed_requests = [], [], []
result = {}

with sync_playwright() as p:
    step(f"connect_over_cdp {CDP}")
    browser = p.chromium.connect_over_cdp(CDP)
    ctx = browser.contexts[0] if browser.contexts else browser.new_context()
    page = ctx.new_page()
    page.set_viewport_size({"width": 1280, "height": 1800})

    page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: page_errors.append(str(e)))
    page.on("requestfailed", lambda r: failed_requests.append(f"{r.method} {r.url} :: {r.failure}"))

    # CP1: navigate + confirm load
    step("CP1: goto example.com")
    resp = page.goto("https://example.com", wait_until="load", timeout=30000)
    status = resp.status if resp else None
    step(f"CP1: status={status}")
    title = page.title()
    step(f"CP1: title={title!r}")
    page.wait_for_timeout(500)
    page.screenshot(path=f"{RUN_DIR}/final_execution_cp1.png")

    # CP2: read DOM content
    step("CP2: read h1")
    h1 = page.locator("h1").first.inner_text()
    step(f"CP2: h1={h1!r}")

    # CP3: interact by ARIA role, confirm navigation
    step("CP3: click 'More information' link")
    page.get_by_role("link", name="More information").click()
    page.wait_for_load_state("load", timeout=30000)
    page.wait_for_timeout(500)
    final_url = page.url
    step(f"CP3: url={final_url}")
    page.screenshot(path=f"{RUN_DIR}/final_execution_cp3.png")

    result = {
        "cp1_loaded": status == 200,
        "cp1_status": status,
        "cp1_title": title,
        "cp2_h1": h1,
        "cp3_navigated": final_url != "https://example.com/",
        "cp3_final_url": final_url,
        "console_errors": console_errors,
        "page_errors": page_errors,
        "failed_requests": failed_requests,
    }
    step(f"FINAL_RESPONSE={json.dumps(result)}")
    page.close()

with open(f"{RUN_DIR}/final_script_log.txt", "w") as f:
    f.write("\n".join(log) + "\n")
with open(f"{RUN_DIR}/result.json", "w") as f:
    json.dump(result, f, indent=2)
print("WROTE_ARTIFACTS", flush=True)
