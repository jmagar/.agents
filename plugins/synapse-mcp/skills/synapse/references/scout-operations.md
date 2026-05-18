# Scout Operations Reference

Complete reference for all 16 Scout operations organized by category.

## Table of Contents

- [Simple Operations (9)](#simple-operations)
- [ZFS Operations (3)](#zfs-operations)
- [Log Operations (4)](#log-operations)
- [Help System (1)](#help-system)

---

## Simple Operations

### nodes

List all configured SSH hosts.

**Parameters:**

- `action`: "nodes" (required)

**Returns:** List of all auto-discovered and manually configured hosts.

**Example:**

```json
{
  "action": "nodes"
}
```

### peek

Read file or directory contents on remote host.

**Parameters:**

- `action`: "peek" (required)
- `target`: string (required) - Format: "hostname:/path"
- `tree`: boolean (optional, default: false) - Show directory tree
- `depth`: number (optional, 1-10, default: 3) - Tree depth
- `max_answer_chars`: number (optional) - Limit output size

**Target format:** `hostname:/path/to/file`

**Example - Read file:**

```json
{
  "action": "peek",
  "target": "production:/etc/docker/daemon.json"
}
```

**Example - Directory tree:**

```json
{
  "action": "peek",
  "target": "production:/opt/stacks",
  "tree": true,
  "depth": 2
}
```

### exec

Execute allowlisted command on remote host.

**Parameters:**

- `action`: "exec" (required)
- `target`: string (required) - Working directory in `hostname:/path` format (e.g., `"production:/"`)
- `command`: string (required) - Command (allowlist only)
- `timeout`: number (optional, 1-300000ms, default: 30000) - Milliseconds

**Allowlisted commands:**

- File operations: `cat`, `head`, `tail`, `grep`, `find`, `ls`, `stat`, `file`, `wc`
- System info: `df`, `du`, `ps`, `top`, `uptime`, `free`, `hostname`, `uname`
- Network: `ping`, `ip`, `ss`, `netstat`
- Other: `date`, `echo`

**Example:**

```json
{
  "action": "exec",
  "target": "production:/",
  "command": "df -h /mnt/data",
  "timeout": 10000
}
```

### find

Find files by glob pattern on remote host.

**Parameters:**

- `action`: "find" (required)
- `host`: string (required)
- `pattern`: string (required) - Glob pattern (e.g., `*.log`, `**/*.conf`)
- `path`: string (optional, default: "/") - Search root
- `max_depth`: number (optional) - Limit search depth

**Example:**

```json
{
  "action": "find",
  "host": "production",
  "pattern": "*.log",
  "path": "/var/log"
}
```

### delta

Compare files or content between locations.

**Parameters:**

- `action`: "delta" (required)
- `source`: string (required) - Source location
- `target`: string (required) - Target location (can be different host)

**Location formats:**

- Remote file: `hostname:/path/to/file`
- Local content: Can provide content directly

**Example:**

```json
{
  "action": "delta",
  "source": "host1:/etc/config.yml",
  "target": "host2:/etc/config.yml"
}
```

### beam

Transfer file between hosts.

**Parameters:**

- `action`: "beam" (required)
- `source`: string (required) - Source location (hostname:/path)
- `destination`: string (required) - Destination (hostname:/path)
- `preserve_permissions`: boolean (optional, default: true)

**Example:**

```json
{
  "action": "beam",
  "source": "production:/backup/config.tar.gz",
  "destination": "storage:/archives/config.tar.gz"
}
```

### emit

Execute command across multiple hosts in parallel.

**Parameters:**

- `action`: "emit" (required)
- `targets`: string[] (required) - List of "hostname:/workdir" targets
- `command`: string (required) - Command to execute (allowlist only)
- `timeout`: number (optional, default: 30)

**Example:**

```json
{
  "action": "emit",
  "targets": ["host1:/tmp", "host2:/tmp", "host3:/tmp"],
  "command": "df -h"
}
```

### ps

List and filter processes on remote host.

**Parameters:**

- `action`: "ps" (required)
- `host`: string (required)
- `user_filter`: string (optional) - Filter by username
- `cpu_threshold`: number (optional) - Min CPU% to show
- `mem_threshold`: number (optional) - Min memory% to show
- `sort_by`: "cpu" | "mem" | "pid" (optional)

**Example:**

```json
{
  "action": "ps",
  "host": "production",
  "cpu_threshold": 5.0,
  "sort_by": "cpu"
}
```

### df

Show disk usage for mounted filesystems.

**Parameters:**

- `action`: "df" (required)
- `host`: string (required)
- `path`: string (optional) - Specific mount point

**Example:**

```json
{
  "action": "df",
  "host": "production",
  "path": "/mnt/data"
}
```

---

## ZFS Operations

### zfs pools

List ZFS storage pools with health status.

**Parameters:**

- `action`: "zfs" (required)
- `subaction`: "pools" (required)
- `host`: string (required)

**Returns:** Pool name, size, allocated, free, health, fragmentation

**Example:**

```json
{
  "action": "zfs",
  "subaction": "pools",
  "host": "storage-server"
}
```

### zfs datasets

List ZFS datasets and volumes.

**Parameters:**

- `action`: "zfs" (required)
- `subaction`: "datasets" (required)
- `host`: string (required)
- `pool`: string (optional) - Filter by pool name

**Returns:** Dataset name, used space, available, referenced, mountpoint

**Example:**

```json
{
  "action": "zfs",
  "subaction": "datasets",
  "host": "storage-server",
  "pool": "tank"
}
```

### zfs snapshots

List ZFS snapshots with metadata.

**Parameters:**

- `action`: "zfs" (required)
- `subaction`: "snapshots" (required)
- `host`: string (required)
- `dataset`: string (optional) - Filter by dataset

**Returns:** Snapshot name, used space, creation time, referenced

**Example:**

```json
{
  "action": "zfs",
  "subaction": "snapshots",
  "host": "storage-server",
  "dataset": "tank/data"
}
```

---

## Log Operations

### logs syslog

Access system log files in /var/log.

**Parameters:**

- `action`: "logs" (required)
- `subaction`: "syslog" (required)
- `host`: string (required)
- `file`: string (optional, default: "syslog") - Log file name
- `lines`: number (optional, default: 100) - Number of lines
- `grep`: string (optional) - Filter pattern (safe patterns only)
- `since`: string (optional) - Relative time ("1h", "30m")

**Example:**

```json
{
  "action": "logs",
  "subaction": "syslog",
  "host": "production",
  "lines": 50,
  "grep": "error"
}
```

### logs journal

Access systemd journal logs.

**Parameters:**

- `action`: "logs" (required)
- `subaction`: "journal" (required)
- `host`: string (required)
- `unit`: string (optional) - systemd unit name
- `lines`: number (optional, default: 100)
- `since`: string (optional) - Relative time or ISO 8601
- `until`: string (optional) - Relative time or ISO 8601
- `grep`: string (optional) - Filter pattern
- `priority`: string (optional) - "emerg" | "alert" | "crit" | "err" | "warning" | "notice" | "info" | "debug"

**Example:**

```json
{
  "action": "logs",
  "subaction": "journal",
  "host": "production",
  "unit": "docker.service",
  "lines": 100,
  "since": "1h"
}
```

### logs dmesg

Access kernel ring buffer logs.

**Parameters:**

- `action`: "logs" (required)
- `subaction`: "dmesg" (required)
- `host`: string (required)
- `lines`: number (optional, default: 100)
- `level`: string (optional) - Kernel log level filter
- `facility`: string (optional) - Kernel facility filter
- `grep`: string (optional) - Filter pattern

**Example:**

```json
{
  "action": "logs",
  "subaction": "dmesg",
  "host": "production",
  "lines": 50,
  "level": "err"
}
```

### logs auth

Access authentication logs.

**Parameters:**

- `action`: "logs" (required)
- `subaction`: "auth" (required)
- `host`: string (required)
- `lines`: number (optional, default: 100)
- `grep`: string (optional) - Filter pattern
- `since`: string (optional) - Relative time

**Example:**

```json
{
  "action": "logs",
  "subaction": "auth",
  "host": "production",
  "lines": 100,
  "grep": "Failed"
}
```

---

## Help System

### help

Auto-generated help documentation.

**Parameters:**

- `action`: "help" (required)
- `topic`: string (optional) - Specific operation (e.g., "zfs:pools")
- `format`: "markdown" | "json" (optional)

**Example:**

```json
{
  "action": "help",
  "topic": "logs:journal"
}
```

---

## Common Patterns

### File Operations

**Read configuration file:**

```json
{
  "action": "peek",
  "target": "production:/etc/app/config.yml"
}
```

**Browse directory structure:**

```json
{
  "action": "peek",
  "target": "production:/opt/stacks",
  "tree": true,
  "depth": 3
}
```

**Find log files:**

```json
{
  "action": "find",
  "host": "production",
  "pattern": "*.log",
  "path": "/var/log"
}
```

### Remote Execution

**Check disk space:**

```json
{
  "action": "exec",
  "host": "production",
  "command": "df -h"
}
```

**List processes:**

```json
{
  "action": "ps",
  "host": "production",
  "cpu_threshold": 10.0,
  "sort_by": "cpu"
}
```

**Multi-host command:**

```json
{
  "action": "emit",
  "targets": ["host1:/", "host2:/", "host3:/"],
  "command": "uptime"
}
```

### ZFS Management

**Pool health:**

```json
{
  "action": "zfs",
  "subaction": "pools",
  "host": "storage"
}
```

**Dataset usage:**

```json
{
  "action": "zfs",
  "subaction": "datasets",
  "host": "storage",
  "pool": "tank"
}
```

**Snapshot list:**

```json
{
  "action": "zfs",
  "subaction": "snapshots",
  "host": "storage",
  "dataset": "tank/backups"
}
```

### Log Analysis

**Recent errors:**

```json
{
  "action": "logs",
  "subaction": "journal",
  "host": "production",
  "since": "1h",
  "priority": "err"
}
```

**Service logs:**

```json
{
  "action": "logs",
  "subaction": "journal",
  "host": "production",
  "unit": "nginx.service",
  "lines": 100
}
```

**Authentication attempts:**

```json
{
  "action": "logs",
  "subaction": "auth",
  "host": "production",
  "grep": "sshd"
}
```

---

## Security Considerations

### Command Allowlist

Only these commands are allowed for `exec` and `emit`:

**File operations:**

- `cat`, `head`, `tail`, `grep`, `find`, `ls`, `stat`, `file`, `wc`

**System info:**

- `df`, `du`, `ps`, `top`, `uptime`, `free`, `hostname`, `uname`

**Network:**

- `ping`, `ip`, `ss`, `netstat`

**Utilities:**

- `date`, `echo`

**Arbitrary commands are blocked** to prevent security vulnerabilities.

### Path Security

- All paths validated for traversal attacks
- No `..` allowed in paths
- Absolute paths required for file operations
- Symbolic link resolution controlled

### Pattern Safety

- Grep patterns validated (no injection)
- Glob patterns sanitized
- Regular expressions bounded

---

## Error Handling

### Common Errors

**Host not found:**

- Verify host in `~/.ssh/config` or `synapse.config.json`
- Check SSH connectivity

**Permission denied:**

- Verify SSH key permissions
- Check target file/directory permissions

**Command not allowed:**

- Only allowlisted commands work for `exec`/`emit`
- Use alternative Scout operations (peek, find, etc.)

**Path not found:**

- Verify path exists on target host
- Check for typos in hostname or path

**ZFS not available:**

- Ensure ZFS tools installed on target host
- Verify ZFS pools exist

---

**Version:** 1.0.0
**Last Updated:** 2026-02-13
