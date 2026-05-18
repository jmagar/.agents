# Troubleshooting Guide

Common issues and solutions for synapse-mcp operations.

## Table of Contents

- [Connection Issues](#connection-issues)
- [Container Problems](#container-problems)
- [Compose Discovery](#compose-discovery)
- [Performance Issues](#performance-issues)
- [Security & Permissions](#security--permissions)
- [ZFS Operations](#zfs-operations)
- [Log Operations](#log-operations)

---

## Connection Issues

### SSH Connection Failed

**Error:** `Failed to connect to host: Connection refused`

**Causes:**

- Host not in SSH config
- Network connectivity issue
- SSH service not running

**Solutions:**

1. **Verify host in SSH config:**

```bash
grep "^Host production" ~/.ssh/config
```

2. **Test SSH manually:**

```bash
ssh production
```

3. **Check SSH service:**

```json
{
  "action": "exec",
  "host": "production",
  "command": "ss -tlnp | grep :22"
}
```

4. **Add missing host:**

```ssh-config
Host production
  HostName 192.168.1.100
  User admin
  IdentityFile ~/.ssh/id_ed25519
```

### Docker Connection Failed

**Error:** `Cannot connect to Docker daemon`

**Causes:**

- Docker not running
- Permission issues
- Socket path incorrect

**Solutions:**

1. **Check Docker status:**

```json
{
  "action": "host",
  "subaction": "status",
  "host": "production"
}
```

2. **Verify Docker service:**

```json
{
  "action": "host",
  "subaction": "services",
  "host": "production",
  "filter": "docker"
}
```

3. **Check socket permissions:**

```json
{
  "action": "exec",
  "host": "production",
  "command": "ls -la /var/run/docker.sock"
}
```

### SSH Key Permission Denied

**Error:** `Permission denied (publickey)`

**Causes:**

- Wrong private key
- Key not authorized on remote host
- Incorrect key permissions

**Solutions:**

1. **Verify key permissions:**

```bash
chmod 600 ~/.ssh/id_ed25519
chmod 700 ~/.ssh
```

2. **Check authorized keys:**

```json
{
  "action": "peek",
  "target": "production:~/.ssh/authorized_keys"
}
```

3. **Add public key to authorized_keys:**

```bash
ssh-copy-id -i ~/.ssh/id_ed25519.pub production
```

---

## Container Problems

### Container Won't Start

**Error:** Container exits immediately after start

**Diagnostic steps:**

1. **Check container status:**

```json
{
  "action": "container",
  "subaction": "list",
  "name_filter": "problem-container"
}
```

2. **Review startup logs:**

```json
{
  "action": "container",
  "subaction": "logs",
  "container_id": "problem-container",
  "lines": 100
}
```

3. **Inspect configuration:**

```json
{
  "action": "container",
  "subaction": "inspect",
  "container_id": "problem-container"
}
```

4. **Check for port conflicts:**

```json
{
  "action": "host",
  "subaction": "ports",
  "port_filter": 8080
}
```

**Common solutions:**

- Fix configuration errors in compose file
- Resolve port conflicts
- Ensure required volumes exist
- Check environment variables

### Container Using Too Much Resources

**Diagnostic steps:**

1. **Check resource usage:**

```json
{
  "action": "container",
  "subaction": "stats",
  "container_id": "resource-hog"
}
```

2. **View running processes:**

```json
{
  "action": "container",
  "subaction": "top",
  "container_id": "resource-hog"
}
```

3. **Check for resource limits:**

```json
{
  "action": "container",
  "subaction": "inspect",
  "container_id": "resource-hog"
}
```

**Solutions:**

- Add resource limits to compose file
- Investigate application-level issues
- Scale horizontally if needed
- Optimize container configuration

### Cannot Access Container Logs

**Error:** `Failed to retrieve logs`

**Solutions:**

1. **Verify container exists:**

```json
{
  "action": "container",
  "subaction": "list",
  "name_filter": "target-container"
}
```

2. **Check container state:**

```json
{
  "action": "container",
  "subaction": "inspect",
  "container_id": "target-container",
  "summary": true
}
```

3. **Try smaller log range:**

```json
{
  "action": "container",
  "subaction": "logs",
  "container_id": "target-container",
  "lines": 10
}
```

---

## Compose Discovery

### Compose Project Not Found

**Error:** `Project 'media-stack' not found`

**Causes:**

- Project not in configured search paths
- Cache stale
- Project renamed/moved

**Solutions:**

1. **List discovered projects:**

```json
{
  "action": "compose",
  "subaction": "list"
}
```

2. **Refresh compose cache:**

```json
{
  "action": "compose",
  "subaction": "refresh"
}
```

3. **Check project location:**

```json
{
  "action": "peek",
  "target": "production:/opt/stacks",
  "tree": true
}
```

4. **Add to search paths:**

```json
{
  "hosts": [
    {
      "name": "production",
      "composeSearchPaths": ["/opt/stacks", "/srv/docker", "/custom/path"]
    }
  ]
}
```

5. **Use explicit project path:**

```json
{
  "action": "compose",
  "subaction": "up",
  "project": "/opt/stacks/media/docker-compose.yml",
  "host": "production"
}
```

### Discovery Timeout

**Error:** `Compose discovery timed out`

**Causes:**

- Large directory structures
- Slow filesystem
- Many nested directories

**Solutions:**

1. **Use explicit host targeting:**

```json
{
  "action": "compose",
  "subaction": "up",
  "project": "media-stack",
  "host": "production"
}
```

2. **Reduce search paths:**

```json
{
  "hosts": [
    {
      "composeSearchPaths": ["/opt/stacks"] // Narrow scope
    }
  ]
}
```

3. **Increase TTL:**

```bash
COMPOSE_CACHE_TTL_HOURS=48
```

---

## Performance Issues

### Slow Container List

**Causes:**

- Many containers across many hosts
- No filtering applied
- Network latency

**Solutions:**

1. **Use filters:**

```json
{
  "action": "container",
  "subaction": "list",
  "state": "running",
  "host": "production"
}
```

2. **Target specific host:**

```json
{
  "action": "container",
  "subaction": "list",
  "host": "production"
}
```

3. **Use pagination:**

```json
{
  "action": "container",
  "subaction": "list",
  "limit": 50,
  "offset": 0
}
```

### Slow Compose Operations

**Causes:**

- Discovery overhead
- Cache miss
- Multiple hosts

**Solutions:**

1. **Use explicit host:**

```json
{
  "action": "compose",
  "subaction": "status",
  "project": "media-stack",
  "host": "production"
}
```

2. **Pre-warm cache:**

```json
{
  "action": "compose",
  "subaction": "refresh"
}
```

### SSH Connection Latency

**Causes:**

- New connections (not using pool)
- Network latency
- DNS resolution

**Solutions:**

- Connection pooling is automatic (50× speedup)
- Use IP addresses instead of hostnames if DNS is slow
- Increase pool size for high concurrency:

```bash
SSH_POOL_MAX_CONNECTIONS=20
```

---

## Security & Permissions

### Command Not Allowed

**Error:** `Command 'rm' not in allowlist`

**Cause:** Scout `exec` only allows safe commands

**Solution:** Use Scout's specialized operations instead:

| Need        | Instead of        | Use                                          |
| ----------- | ----------------- | -------------------------------------------- |
| Read file   | `exec cat file`   | `peek host:file`                             |
| List files  | `exec ls dir`     | `peek host:dir --tree`                       |
| Find files  | `exec find -name` | `find host:pattern`                          |
| Delete file | `exec rm file`    | Not supported (use container exec or manual) |

**Allowlisted commands:**

- File: cat, head, tail, grep, find, ls, stat, file, wc
- System: df, du, ps, top, uptime, free, hostname, uname
- Network: ping, ip, ss, netstat

### Permission Denied on File Access

**Error:** `Permission denied: /etc/restricted-file`

**Solutions:**

1. **Check file permissions:**

```json
{
  "action": "exec",
  "host": "production",
  "command": "stat /etc/restricted-file"
}
```

2. **Use appropriate user:**

```json
{
  "action": "container",
  "subaction": "exec",
  "container_id": "app",
  "command": "cat /restricted-file",
  "user": "root"
}
```

3. **Verify SSH user permissions:**

```ssh-config
Host production
  User root  # or user with appropriate permissions
```

### Path Traversal Blocked

**Error:** `Invalid path: contains '..'`

**Cause:** Security protection against path traversal

**Solution:** Use absolute paths only:

```json
{
  "action": "peek",
  "target": "production:/etc/app/config.yml" // ✅ Absolute
}
```

Not:

```json
{
  "action": "peek",
  "target": "production:../../etc/app/config.yml" // ❌ Relative
}
```

---

## ZFS Operations

### ZFS Command Not Found

**Error:** `zfs: command not found`

**Cause:** ZFS not installed on target host

**Solution:**

1. **Verify ZFS installation:**

```json
{
  "action": "exec",
  "host": "storage",
  "command": "command -v zfs"
}
```

2. **Install ZFS:**

```bash
# Debian/Ubuntu
apt-get install zfsutils-linux

# RHEL/CentOS
yum install zfs
```

### No ZFS Pools Found

**Error:** `No pools available`

**Solutions:**

1. **Check ZFS module loaded:**

```json
{
  "action": "exec",
  "host": "storage",
  "command": "lsmod | grep zfs"
}
```

2. **Load ZFS module:**

```bash
modprobe zfs
```

3. **Verify pools exist:**

```json
{
  "action": "exec",
  "host": "storage",
  "command": "zpool list"
}
```

---

## Log Operations

### Journal Not Available

**Error:** `systemd journal not available`

**Cause:** systemd not in use or journal not configured

**Solution:** Use syslog instead:

```json
{
  "action": "logs",
  "subaction": "syslog",
  "host": "production",
  "file": "syslog"
}
```

### Log Grep Returns No Results

**Cause:**

- Pattern doesn't match
- Time range too narrow
- Log level filtered out

**Solutions:**

1. **Try broader pattern:**

```json
{
  "action": "container",
  "subaction": "logs",
  "container_id": "nginx",
  "grep": "error|fail|warn" // Multiple patterns
}
```

2. **Expand time range:**

```json
{
  "action": "container",
  "subaction": "logs",
  "container_id": "nginx",
  "since": "24h" // Wider window
}
```

3. **Remove filters:**

```json
{
  "action": "container",
  "subaction": "logs",
  "container_id": "nginx",
  "lines": 100 // No grep filter
}
```

---

## General Troubleshooting

### Enable Debug Logging

**For synapse-mcp server:**

```bash
DEBUG=synapse:* node dist/index.js --stdio
```

### Check MCP Server Status

**Verify server is running:**

```bash
ps aux | grep synapse-mcp
```

### Validate Configuration

**Check synapse.config.json:**

```json
{
  "action": "peek",
  "target": "localhost:~/.config/synapse/synapse.config.json"
}
```

### Common Error Codes

| Code         | Meaning             | Action                           |
| ------------ | ------------------- | -------------------------------- |
| ECONNREFUSED | Connection refused  | Check SSH/Docker service running |
| ETIMEDOUT    | Operation timed out | Check network connectivity       |
| EACCES       | Permission denied   | Verify SSH keys and permissions  |
| ENOENT       | File not found      | Verify path exists               |
| ENOTFOUND    | Host not found      | Check SSH config or hostname     |

---

## Getting Help

**Report issues:**

- GitHub: https://github.com/jmagar/synapse-mcp/issues
- Include: Error message, operation attempted, host configuration

**Debug information to include:**

- synapse-mcp version
- Operating system and version
- Docker version (if applicable)
- SSH configuration (sanitized)
- Complete error message

---

**Version:** 1.0.0
**Last Updated:** 2026-02-13
