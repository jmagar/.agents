---
description: Check fastproxy health and upstream server status
argument-hint: [base-url]
allowed-tools: Bash(bash:*)
---

Run `./bin/health-check.sh $ARGUMENTS` (default base URL: `http://localhost:8000`).

Report:
- Overall proxy status
- Storage backend status
- Active session count
- Per-upstream-server health

If status is not `ok`, diagnose:
- `storage: error` → check Redis connectivity: `docker compose ps redis`
- `server <alias>: down` → check the upstream server process or URL
- Proxy unreachable (curl error) → check if `fastproxy serve` is running and the base URL is correct
