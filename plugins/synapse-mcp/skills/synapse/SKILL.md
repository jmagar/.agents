---
name: synapse
description: This skill should be used when managing Docker containers, Compose projects, or Docker images across homelab hosts; when executing remote commands or reading files on SSH hosts; when monitoring ZFS pools, datasets, or snapshots; when aggregating or filtering system logs (syslog, journal, dmesg, auth); or when performing multi-host health checks, resource monitoring, or infrastructure troubleshooting. Prefer the synapse MCP tools when available; fall back to HTTP only when MCP tool wiring is unavailable. Typical triggers include "restart my nginx container", "show disk usage on the storage server", "pull the latest images for media-stack", "check ZFS pool health", "tail the journal on production", "compare configs between two hosts", or "list all running containers".
---

# Synapse - Homelab Infrastructure Management

## Mode Detection

**MCP mode** (preferred): Use `mcp__synapse__flux` and `mcp__synapse__scout` when those tools are available.

**HTTP fallback**: If MCP tools are unavailable, connect to `${user_config.synapse_mcp_url}` with bearer auth using `${user_config.synapse_mcp_token}`. Do not attempt to read sensitive values from `${user_config.*}` for Bash fallbacks; use environment variables provided by the plugin hook instead.

## Purpose

Synapsis provides comprehensive homelab infrastructure management through two specialized tools:

- **Flux** - Docker infrastructure management (41 operations)
- **Scout** - SSH-based remote operations (16 operations)

Access these tools via `/flux` and `/scout` commands, which invoke the synapse-mcp MCP server.

**Capabilities:**

- ✅ **Read-Write Operations** - Full Docker and SSH management
- ✅ **Multi-Host Orchestration** - Auto-discovery from SSH config
- ✅ **Intelligent Caching** - Compose project discovery (24hr TTL)
- ✅ **Security-First** - Command allowlisting, path validation
- ✅ **Performance Optimized** - SSH connection pooling (50× speedup)

---

## Tool Selection

### Use Flux When:

- Managing Docker containers (start, stop, restart, logs, stats)
- Orchestrating Compose projects (up, down, recreate)
- Working with Docker images (pull, build, prune)
- Checking host system health (resources, uptime, services)
- Managing Docker networks or volumes

### Use Scout When:

- Reading/writing remote files
- Executing allowlisted commands on remote hosts
- Managing ZFS pools, datasets, snapshots
- Analyzing system logs (syslog, journal, dmesg, auth)
- Transferring files between hosts
- Monitoring processes or disk usage

---

## Quick Command Reference

### Flux Operations

**Container Management:**

```
/flux list containers
/flux start container-name
/flux logs nginx --lines 50 --grep error
/flux stats plex
/flux exec container-name ls -la /data
```

**Compose Projects:**

```
/flux list compose projects
/flux up media-stack
/flux down media-stack
/flux logs media-stack
/flux recreate media-stack --pull
```

**Host Diagnostics:**

```
/flux check host status
/flux show system resources
/flux list docker images
/flux show disk usage
```

### Scout Operations

**File Operations:**

```
/scout list hosts
/scout read production:/etc/docker/daemon.json
/scout exec production df -h
/scout find files matching *.log on production
```

**ZFS Management:**

```
/scout show zfs pools on storage
/scout list zfs datasets on storage
/scout show zfs snapshots on storage
```

**Log Analysis:**

```
/scout show journal logs on production
/scout show syslog on production --grep error
/scout show auth logs on production
```

---

## Common Workflows

### 1. Docker Deployment

**Deploy new version:**

1. Check current status: `/flux list containers --state running`
2. Pull latest images: `/flux pull media-stack`
3. Stop old version: `/flux down media-stack`
4. Start new version: `/flux up media-stack`
5. Verify health: `/flux logs media-stack --lines 20`
6. Monitor resources: `/flux stats`

**Quick restart:**

1. Restart services: `/flux restart media-stack`
2. Check logs: `/flux logs media-stack`

### 2. Multi-Host Health Check

**System overview:**

1. List all hosts: `/scout list hosts`
2. Check Docker status: `/flux check all hosts`
3. View system resources: `/flux show resources on all hosts`
4. Check critical services: `/flux show services on all hosts`

**Storage health:**

1. Check ZFS pools: `/scout show zfs pools on storage`
2. Disk usage: `/scout exec all-hosts df -h`
3. Mount status: `/flux show mounts on all hosts`

### 3. Troubleshooting

**Container issues:**

1. Check container state: `/flux list containers --name problematic-service`
2. View recent logs: `/flux logs service --lines 100 --since 1h`
3. Inspect configuration: `/flux inspect service`
4. Check processes: `/flux top service`
5. Verify resources: `/flux stats service`

**Application errors:**

1. Search logs: `/flux logs service --grep "ERROR|FATAL"`
2. Check system logs: `/scout show journal on host --unit service`
3. Review auth logs: `/scout show auth logs on host`
4. Compare configs: `/scout compare host1:/config host2:/config`

### 4. Log Aggregation

**Centralized log analysis:**

1. Get container logs: `/flux logs --all --since 1h --grep error`
2. Get system logs: `/scout show journal on all hosts --since 1h`
3. Get auth activity: `/scout show auth logs on all hosts`
4. Get kernel messages: `/scout show dmesg on all hosts`

---

## Best Practices

### Multi-Host Management

**Auto-Discovery:**

- Hosts from `~/.ssh/config` are automatically available
- Use `synapse.config.json` for advanced host configuration
- Tag hosts for filtering (production, staging, storage)

**Host Targeting:**

- Omit `host` parameter to run on all discovered hosts
- Use specific host name for targeted operations
- Use `emit` for parallel multi-host commands

**Compose Discovery:**

- Projects are auto-discovered with 24hr cache
- Default search paths: `/compose`, `/mnt/cache/compose`, `/mnt/cache/code`
- Use `/flux refresh compose cache` to force re-scan
- Explicit host targeting skips discovery (faster)

### Performance

**Caching:**

- Compose projects cached for 24 hours (configurable via `COMPOSE_CACHE_TTL_HOURS`)
- SSH connections pooled (50× faster than new connections)
- Container-to-host mapping cached to avoid repeated lookups

**Pagination:**

- Use `--limit` for large result sets (default: 50, max: 1000)
- Use `--offset` for browsing paginated data
- Filter early (state, name, image) to reduce data transfer

**Filtering:**

- Container filters: state, name, image, labels
- Log filters: time range (`--since`, `--until`), grep patterns
- Process filters: user, CPU threshold, memory threshold

### Security

**Command Execution:**

- Scout `exec` only allows 20+ safe commands (cat, grep, find, ls, stat, etc.)
- Never expose credentials in logs or output
- Use SSH key authentication (not passwords)
- Path traversal protection (no `..` in paths)

**Destructive Operations:**

- `recreate`, `down`, `rmi`, `prune` require `force: true`
- Always check impact before destructive operations
- Use `--dry-run` where available

**Validation:**

- All input validated with Zod schemas (O(1) discrimination)
- Safe grep patterns only (no injection)
- Command allowlisting enforced

### Error Handling

**Transient Failures:**

- SSH connection errors: Check network, verify host in `~/.ssh/config`
- Docker connection errors: Verify Docker socket accessibility
- Compose discovery timeout: Use explicit host targeting

**Permanent Failures:**

- Invalid host: Add to SSH config or synapse.config.json
- Permission denied: Verify SSH keys and Docker socket permissions
- Unknown project: Check compose search paths, run refresh

**Recovery:**

- Connection pool auto-recovers from transient failures
- Compose cache auto-refreshes on miss
- Failed operations return structured errors with context

---

## Configuration

### Environment Variables

Set via `.env` or shell environment:

```bash
SYNAPSE_CONFIG_FILE=/path/to/synapse.config.json
SYNAPSE_DEFAULT_HOST=production
SSH_POOL_MAX_CONNECTIONS=10
COMPOSE_CACHE_TTL_HOURS=24
```

### Host Configuration

**Minimal (SSH config only):**

```ssh-config
Host production
  HostName 192.168.1.100
  User admin
  IdentityFile ~/.ssh/id_rsa
```

**Advanced (synapse.config.json):**

```json
{
  "hosts": [
    {
      "name": "production",
      "host": "192.168.1.100",
      "protocol": "ssh",
      "sshUser": "admin",
      "sshKeyPath": "~/.ssh/id_rsa",
      "composeSearchPaths": ["/opt/stacks", "/srv/docker"],
      "tags": ["production", "docker"]
    }
  ]
}
```

---

## Notes

**Compose Auto-Discovery:**

- First checks local cache (fastest)
- Falls back to `docker compose ls` (medium)
- Last resort: filesystem scan (slowest)
- Cache TTL: 24 hours (configurable)
- Manual refresh available

**SSH Connection Pooling:**

- 50× performance improvement over new connections
- Configurable pool size (default: 10)
- Auto-recovery from failures
- Idle timeout management

**Output Formats:**

- Default: Human-readable markdown
- Optional: Structured JSON (`response_format: "json"`)
- Pagination support for large datasets
- Context-aware formatting (tables, lists, trees)

**Limitations:**

- Scout `exec` limited to allowlisted commands (security)
- Compose projects must be in configured search paths
- ZFS operations require ZFS tools on target host
- Log operations require appropriate permissions

---

## Reference Documentation

For comprehensive documentation, see:

- **[Flux Operations Reference](references/flux-operations.md)** - All 41 Flux operations with parameters
- **[Scout Operations Reference](references/scout-operations.md)** - All 16 Scout operations with parameters
- **[Workflow Guide](references/workflows.md)** - Detailed workflow examples
- **[Best Practices Guide](references/best-practices.md)** - Advanced usage patterns
- **[Troubleshooting Guide](references/troubleshooting.md)** - Common issues and solutions

For working examples, see:

- **[Docker Deployment Example](examples/docker-deployment.md)** - Complete deployment workflow
- **[Multi-Host Monitoring Example](examples/multi-host-monitoring.md)** - Health check automation
- **[Log Analysis Example](examples/log-analysis.md)** - Centralized log aggregation

---

**Version:** 1.0.0
**Last Updated:** 2026-03-14
