# `bin/`

Executable helper scripts for fastproxy. Added to `PATH` in plugin environments.

## Contract

- Every file needs a shebang and must be executable
- Keep scripts shell-friendly and portable
- Names should be stable — safe to expose on `PATH`
- Document required inputs near the script

## Scripts

| Script | Purpose |
|--------|---------|
| `gen-secret.sh` | Generate a `FASTPROXY_JWT_SECRET` (openssl rand) |
| `health-check.sh` | Check proxy `/health` endpoint and print status |
| `wait-for-proxy.sh` | Block until proxy is healthy (used in CI / compose) |
