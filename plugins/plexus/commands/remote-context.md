---
description: Load durable REMOTE.md memory and live operating context for a named host.
argument-hint: <host> [--json] [--no-probe]
---

# Remote Context

Load host-specific operating context before touching a remote device.

```bash
python3 plugins/plexus/scripts/remote-context.py $ARGUMENTS
```

Use the output as the working host context for this turn. Durable notes come
from `plugins/plexus/remotes/<host>/REMOTE.md`; live state comes from SSH,
Tailscale, Docker/systemd probes, and `syslog-mcp` when available.
