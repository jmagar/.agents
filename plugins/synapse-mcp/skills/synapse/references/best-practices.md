# Best Practices Guide

Advanced usage patterns and recommendations for synapse-mcp.

## Table of Contents

- [Multi-Host Management](#multi-host-management)
- [Performance Optimization](#performance-optimization)
- [Security](#security)
- [Operational Excellence](#operational-excellence)
- [Monitoring & Alerting](#monitoring--alerting)

---

## Multi-Host Management

### Host Discovery Strategy

**Auto-Discovery (Recommended):**

```ssh-config
# ~/.ssh/config
Host production
  HostName 192.168.1.100
  User admin
  IdentityFile ~/.ssh/id_ed25519

Host staging
  HostName 192.168.1.101
  User admin
  IdentityFile ~/.ssh/id_ed25519
```

Hosts are automatically available in Flux and Scout.

**Manual Configuration (Advanced):**

```json
{
  "hosts": [
    {
      "name": "production",
      "host": "192.168.1.100",
      "protocol": "ssh",
      "sshUser": "admin",
      "sshKeyPath": "~/.ssh/id_ed25519",
      "composeSearchPaths": ["/opt/stacks", "/srv/docker"],
      "tags": ["production", "critical"]
    },
    {
      "name": "storage",
      "host": "nas.local",
      "protocol": "ssh",
      "sshUser": "root",
      "sshKeyPath": "~/.ssh/id_rsa",
      "tags": ["storage", "zfs"]
    }
  ]
}
```

**Best Practices:**

- ✅ Use SSH key authentication (never passwords)
- ✅ Tag hosts for filtering (production, staging, storage)
- ✅ Document custom compose search paths
- ✅ Use descriptive host names
- ❌ Don't expose Docker TCP socket (use SSH tunnel)
- ❌ Don't mix production and staging credentials

### Host Targeting

**Explicit targeting (faster):**

```json
{
  "action": "container",
  "subaction": "list",
  "host": "production"
}
```

Skips host discovery, connects directly.

**All hosts (comprehensive):**

```json
{
  "action": "container",
  "subaction": "list"
}
```

Runs on all discovered hosts in parallel.

**Multi-host patterns:**

```json
{
  "action": "emit",
  "targets": ["host1:/", "host2:/", "host3:/"],
  "command": "uptime"
}
```

Parallel execution across specific hosts.

---

## Performance Optimization

### Compose Project Discovery

**Discovery layers (in order):**

1. **Local cache** (fastest, 24hr TTL)
2. **`docker compose ls`** (medium speed)
3. **Filesystem scan** (slowest, max depth 3)

**Optimization strategies:**

**Use explicit host targeting:**

```json
{
  "action": "compose",
  "subaction": "up",
  "project": "media-stack",
  "host": "production"
}
```

Skips discovery, uses cached location.

**Configure search paths:**

```json
{
  "hosts": [
    {
      "name": "production",
      "composeSearchPaths": ["/opt/stacks", "/srv/docker"]
    }
  ]
}
```

Reduces scan surface, faster discovery.

**Manual cache refresh:**

```json
{
  "action": "compose",
  "subaction": "refresh"
}
```

Use after adding new projects.

**Set custom TTL:**

```bash
COMPOSE_CACHE_TTL_HOURS=48 # Extend cache lifetime
```

### SSH Connection Pooling

**Built-in optimization:** 50× faster than new connections

**Tuning:**

```bash
SSH_POOL_MAX_CONNECTIONS=20 # Increase for high-concurrency
```

**Best practices:**

- ✅ Connection pool auto-recovers from failures
- ✅ Idle timeout prevents stale connections
- ✅ Health checks ensure connection validity
- ❌ Don't manually manage connections

### Pagination Strategy

**For large datasets:**

```json
{
  "action": "container",
  "subaction": "list",
  "limit": 100,
  "offset": 0
}
```

**Best practices:**

- ✅ Filter early (state, name, image) to reduce data transfer
- ✅ Use reasonable limits (50-100) for interactive queries
- ✅ Use pagination for batch processing
- ❌ Don't request unlimited results (max: 1000)

### Filtering Strategy

**Container filtering (reduces overhead):**

```json
{
  "action": "container",
  "subaction": "list",
  "state": "running",
  "name_filter": "media",
  "image_filter": "plex"
}
```

**Log filtering (reduces bandwidth):**

```json
{
  "action": "container",
  "subaction": "logs",
  "container_id": "nginx",
  "since": "1h",
  "grep": "error"
}
```

**Best practices:**

- ✅ Apply filters on server side (not client)
- ✅ Use time-range filters for logs
- ✅ Combine multiple filters for precision
- ❌ Don't fetch all data then filter locally

---

## Security

### Command Execution

**Scout allowlist (safe commands only):**

- File: `cat`, `head`, `tail`, `grep`, `find`, `ls`, `stat`
- System: `df`, `du`, `ps`, `uptime`, `free`, `hostname`
- Network: `ping`, `ip`, `ss`

**Why allowlisting matters:**

```json
{
  "action": "exec",
  "host": "production",
  "command": "rm -rf /" // ❌ BLOCKED
}
```

Protection against command injection and destructive operations.

**Best practices:**

- ✅ Use Scout's specialized operations (peek, find) instead of exec
- ✅ Prefer Scout operations over raw commands
- ❌ Don't try to bypass allowlist
- ❌ Don't request `SYNAPSE_ALLOW_ANY_COMMAND=true` (disables all protections)

### Path Security

**Validation rules:**

```json
{
  "action": "peek",
  "target": "production:/etc/../../../etc/passwd" // ❌ BLOCKED
}
```

**Path traversal protection:**

- ✅ Absolute paths required
- ✅ No `..` components allowed
- ✅ Symbolic links controlled
- ❌ Don't use relative paths

### Credential Management

**SSH keys (recommended):**

```ssh-config
Host production
  IdentityFile ~/.ssh/id_ed25519
  IdentitiesOnly yes
```

**Best practices:**

- ✅ Use Ed25519 keys (faster, more secure)
- ✅ Protect private keys: `chmod 600 ~/.ssh/id_ed25519`
- ✅ Use different keys per environment
- ✅ Rotate keys periodically
- ❌ Never use password authentication
- ❌ Never commit keys to version control

### Destructive Operation Safety

**Require explicit confirmation:**

```json
{
  "action": "compose",
  "subaction": "down",
  "project": "media-stack",
  "force": true // Required
}
```

**Destructive operations:**

- `container:recreate`
- `compose:down`
- `compose:recreate`
- `docker:rmi`
- `docker:prune`

**Best practices:**

- ✅ Always review operation before executing
- ✅ Check impact with `status` or `list` first
- ✅ Have backup/rollback plan
- ❌ Don't script destructive operations without safeguards

---

## Operational Excellence

### Error Handling

**Transient failures (auto-retry):**

- SSH connection errors
- Temporary network issues
- Docker API timeouts

**Permanent failures (require intervention):**

- Invalid host configuration
- Permission denied
- Unknown project/container

**Best practices:**

- ✅ Check host status before operations
- ✅ Verify resources exist before acting
- ✅ Monitor logs for error patterns
- ✅ Document recovery procedures

### Logging Strategy

**Structured log filtering:**

```json
{
  "action": "container",
  "subaction": "logs",
  "lines": 100,
  "since": "1h",
  "grep": "ERROR|WARN|FATAL"
}
```

**Time-range queries:**

```json
{
  "action": "logs",
  "subaction": "journal",
  "host": "production",
  "since": "2024-01-15T14:00:00",
  "until": "2024-01-15T16:00:00"
}
```

**Best practices:**

- ✅ Use time-range filters to reduce noise
- ✅ Grep for specific patterns
- ✅ Start with recent logs, expand as needed
- ✅ Correlate container + system logs
- ❌ Don't fetch entire log history

### Configuration Management

**Version control compose files:**

```bash
git init /opt/stacks
cd /opt/stacks
git add docker-compose.yml
git commit -m "Initial compose config"
```

**Backup strategy:**

```json
{
  "action": "beam",
  "source": "production:/opt/stacks",
  "destination": "backup:/configs/production"
}
```

**Best practices:**

- ✅ Version control all configurations
- ✅ Document compose project locations
- ✅ Backup configurations regularly
- ✅ Test restore procedures
- ❌ Don't modify production configs without backups

---

## Monitoring & Alerting

### Health Check Patterns

**Periodic health checks:**

```json
{
  "action": "host",
  "subaction": "status"
}
```

**Resource monitoring:**

```json
{
  "action": "host",
  "subaction": "resources"
}
```

**Container health:**

```json
{
  "action": "container",
  "subaction": "stats"
}
```

**Best practices:**

- ✅ Run health checks every 5-15 minutes
- ✅ Monitor resource trends over time
- ✅ Alert on threshold violations
- ✅ Combine multiple signals for accuracy

### Alerting Strategy

**Alert on:**

- ✅ Container state changes (running → exited)
- ✅ Resource threshold violations (>80% CPU/memory)
- ✅ ZFS pool errors
- ✅ Failed authentication attempts
- ✅ Disk space warnings (<10% free)

**Don't alert on:**

- ❌ Transient connection errors
- ❌ Expected container restarts
- ❌ Normal resource fluctuations

### Dashboard Metrics

**Key metrics to track:**

1. **Container health:** Running vs total containers
2. **Resource usage:** CPU, memory, disk per host
3. **Network activity:** Bytes in/out per container
4. **Storage health:** ZFS pool status, disk usage
5. **Log errors:** Error count per hour

**Implementation:**

```json
// Periodic collection
{
  "action": "container",
  "subaction": "stats"
}

{
  "action": "host",
  "subaction": "resources"
}

{
  "action": "zfs",
  "subaction": "pools",
  "host": "storage"
}
```

---

## Advanced Patterns

### Orchestration Workflows

**Gradual rollout:**

1. Deploy to staging
2. Run smoke tests
3. Deploy to canary (10% traffic)
4. Monitor for issues
5. Full production rollout

**Multi-stage deployment:**

```json
// Stage 1: Update staging
{
  "action": "compose",
  "subaction": "pull",
  "project": "app",
  "host": "staging"
}

// Stage 2: Verify staging
{
  "action": "container",
  "subaction": "stats",
  "host": "staging"
}

// Stage 3: Production deployment
{
  "action": "compose",
  "subaction": "up",
  "project": "app",
  "host": "production"
}
```

### GitOps Integration

**Workflow:**

1. Update compose files in git
2. CI/CD pushes to hosts
3. Use Flux to apply changes
4. Monitor deployment via Scout

**Validation:**

```json
{
  "action": "delta",
  "source": "git:/docker-compose.yml",
  "target": "production:/opt/stacks/docker-compose.yml"
}
```

---

**Version:** 1.0.0
**Last Updated:** 2026-02-13
