# Flux Operations Reference

Complete reference for all 41 Flux operations organized by category.

## Table of Contents

- [Container Operations (14)](#container-operations)
- [Compose Operations (10)](#compose-operations)
- [Docker System (9)](#docker-system)
- [Host Operations (7)](#host-operations)
- [Help System (1)](#help-system)

---

## Container Operations

### list

List containers with filtering and pagination.

**Parameters:**

- `action`: "container" (required)
- `subaction`: "list" (required)
- `host`: string (optional) - Target host, omit for all hosts
- `state`: "running" | "exited" | "paused" | "restarting" | "all" (optional)
- `name_filter`: string (optional) - Partial match on container name
- `image_filter`: string (optional) - Partial match on image name
- `label_filter`: string (optional) - Key=value format
- `limit`: number (optional, 1-1000) - Results per page
- `offset`: number (optional) - Pagination offset
- `response_format`: "markdown" | "json" (optional)

**Example:**

```json
{
  "action": "container",
  "subaction": "list",
  "state": "running",
  "limit": 50
}
```

### start

Start one or more stopped containers.

**Parameters:**

- `action`: "container" (required)
- `subaction`: "start" (required)
- `container_id`: string (required) - Container name or ID
- `host`: string (optional)

**Example:**

```json
{
  "action": "container",
  "subaction": "start",
  "container_id": "nginx"
}
```

### stop

Stop one or more running containers.

**Parameters:**

- `action`: "container" (required)
- `subaction`: "stop" (required)
- `container_id`: string (required)
- `host`: string (optional)
- `timeout`: number (optional) - Seconds to wait before kill

**Example:**

```json
{
  "action": "container",
  "subaction": "stop",
  "container_id": "plex",
  "timeout": 30
}
```

### restart

Restart one or more containers.

**Parameters:**

- `action`: "container" (required)
- `subaction`: "restart" (required)
- `container_id`: string (required)
- `host`: string (optional)
- `timeout`: number (optional)

**Example:**

```json
{
  "action": "container",
  "subaction": "restart",
  "container_id": "nginx"
}
```

### pause

Pause container execution.

**Parameters:**

- `action`: "container" (required)
- `subaction`: "pause" (required)
- `container_id`: string (required)
- `host`: string (optional)

**Example:**

```json
{
  "action": "container",
  "subaction": "pause",
  "container_id": "cpu-intensive-task"
}
```

### resume

Resume paused container.

**Parameters:**

- `action`: "container" (required)
- `subaction`: "resume" (required)
- `container_id`: string (required)
- `host`: string (optional)

**Example:**

```json
{
  "action": "container",
  "subaction": "resume",
  "container_id": "cpu-intensive-task"
}
```

### logs

Get container logs with filtering.

**Parameters:**

- `action`: "container" (required)
- `subaction`: "logs" (required)
- `container_id`: string (required)
- `host`: string (optional)
- `lines`: number (optional, 1-5000, default: 100)
- `since`: string (optional) - ISO 8601 or relative ("1h", "30m")
- `until`: string (optional) - ISO 8601 or relative
- `grep`: string (optional) - Filter log lines (safe patterns only)
- `stream`: "stdout" | "stderr" | "both" (optional, default: "both")
- `follow`: boolean (optional) - Follow log output

**Example:**

```json
{
  "action": "container",
  "subaction": "logs",
  "container_id": "nginx",
  "lines": 50,
  "since": "1h",
  "grep": "error"
}
```

### stats

Real-time resource usage statistics.

**Parameters:**

- `action`: "container" (required)
- `subaction`: "stats" (required)
- `container_id`: string (optional) - Specific container or all
- `host`: string (optional)

**Returns:** CPU %, memory usage, network I/O, block I/O

**Example:**

```json
{
  "action": "container",
  "subaction": "stats",
  "container_id": "plex"
}
```

### inspect

Detailed container metadata.

**Parameters:**

- `action`: "container" (required)
- `subaction`: "inspect" (required)
- `container_id`: string (required)
- `host`: string (optional)
- `summary`: boolean (optional, default: false) - Basic info only

**Example:**

```json
{
  "action": "container",
  "subaction": "inspect",
  "container_id": "nginx",
  "summary": true
}
```

### exec

Execute command in running container.

**Parameters:**

- `action`: "container" (required)
- `subaction`: "exec" (required)
- `container_id`: string (required)
- `host`: string (optional)
- `command`: string (required) - Command to execute
- `user`: string (optional) - User to run as

**Example:**

```json
{
  "action": "container",
  "subaction": "exec",
  "container_id": "nginx",
  "command": "nginx -t"
}
```

### top

Show running processes inside container.

**Parameters:**

- `action`: "container" (required)
- `subaction`: "top" (required)
- `container_id`: string (required)
- `host`: string (optional)

**Example:**

```json
{
  "action": "container",
  "subaction": "top",
  "container_id": "postgres"
}
```

### search

Full-text search across containers.

**Parameters:**

- `action`: "container" (required)
- `subaction`: "search" (required)
- `query`: string (required) - Search term
- `host`: string (optional)

**Example:**

```json
{
  "action": "container",
  "subaction": "search",
  "query": "nginx"
}
```

### pull

Pull latest image for container.

**Parameters:**

- `action`: "container" (required)
- `subaction`: "pull" (required)
- `container_id`: string (required)
- `host`: string (optional)

**Example:**

```json
{
  "action": "container",
  "subaction": "pull",
  "container_id": "nginx"
}
```

### recreate

⚠️ **Destructive** - Recreate container(s).

**Parameters:**

- `action`: "container" (required)
- `subaction`: "recreate" (required)
- `container_id`: string (required)
- `host`: string (optional)
- `force`: boolean (required) - Must be true
- `pull_image`: boolean (optional) - Pull latest before recreate

**Example:**

```json
{
  "action": "container",
  "subaction": "recreate",
  "container_id": "nginx",
  "force": true,
  "pull_image": true
}
```

---

## Compose Operations

### list

List all discovered compose projects.

**Parameters:**

- `action`: "compose" (required)
- `subaction`: "list" (required)
- `host`: string (optional)

**Example:**

```json
{
  "action": "compose",
  "subaction": "list"
}
```

### up

Create and start compose services.

**Parameters:**

- `action`: "compose" (required)
- `subaction`: "up" (required)
- `project`: string (required) - Project name
- `host`: string (optional)
- `service`: string (optional) - Specific service
- `detach`: boolean (optional, default: true)
- `build`: boolean (optional) - Build images before starting

**Example:**

```json
{
  "action": "compose",
  "subaction": "up",
  "project": "media-stack"
}
```

### down

⚠️ **Destructive** - Stop and remove compose project.

**Parameters:**

- `action`: "compose" (required)
- `subaction`: "down" (required)
- `project`: string (required)
- `host`: string (optional)
- `force`: boolean (required) - Must be true
- `volumes`: boolean (optional) - Remove volumes too

**Example:**

```json
{
  "action": "compose",
  "subaction": "down",
  "project": "media-stack",
  "force": true
}
```

### restart

Restart compose services.

**Parameters:**

- `action`: "compose" (required)
- `subaction`: "restart" (required)
- `project`: string (required)
- `host`: string (optional)
- `service`: string (optional)

**Example:**

```json
{
  "action": "compose",
  "subaction": "restart",
  "project": "media-stack",
  "service": "plex"
}
```

### status

Show compose project status.

**Parameters:**

- `action`: "compose" (required)
- `subaction`: "status" (required)
- `project`: string (required)
- `host`: string (optional)

**Example:**

```json
{
  "action": "compose",
  "subaction": "status",
  "project": "media-stack"
}
```

### logs

Get compose project logs.

**Parameters:**

- `action`: "compose" (required)
- `subaction`: "logs" (required)
- `project`: string (required)
- `host`: string (optional)
- `service`: string (optional)
- `lines`: number (optional, default: 100)
- `follow`: boolean (optional)

**Example:**

```json
{
  "action": "compose",
  "subaction": "logs",
  "project": "media-stack",
  "lines": 50
}
```

### build

Build compose service images.

**Parameters:**

- `action`: "compose" (required)
- `subaction`: "build" (required)
- `project`: string (required)
- `host`: string (optional)
- `service`: string (optional)
- `no_cache`: boolean (optional)

**Example:**

```json
{
  "action": "compose",
  "subaction": "build",
  "project": "media-stack"
}
```

### pull

Pull compose service images.

**Parameters:**

- `action`: "compose" (required)
- `subaction`: "pull" (required)
- `project`: string (required)
- `host`: string (optional)
- `service`: string (optional)

**Example:**

```json
{
  "action": "compose",
  "subaction": "pull",
  "project": "media-stack"
}
```

### recreate

⚠️ **Destructive** - Recreate compose services.

**Parameters:**

- `action`: "compose" (required)
- `subaction`: "recreate" (required)
- `project`: string (required)
- `host`: string (optional)
- `force`: boolean (required) - Must be true

**Example:**

```json
{
  "action": "compose",
  "subaction": "recreate",
  "project": "media-stack",
  "force": true
}
```

### refresh

Manually refresh compose cache.

**Parameters:**

- `action`: "compose" (required)
- `subaction`: "refresh" (required)
- `host`: string (optional)

**Example:**

```json
{
  "action": "compose",
  "subaction": "refresh"
}
```

---

## Docker System

### images

List Docker images.

**Parameters:**

- `action`: "docker" (required)
- `subaction`: "images" (required)
- `host`: string (optional)
- `filter`: string (optional) - Name/tag filter
- `limit`: number (optional)

**Example:**

```json
{
  "action": "docker",
  "subaction": "images",
  "filter": "nginx"
}
```

### pull

Pull Docker image.

**Parameters:**

- `action`: "docker" (required)
- `subaction`: "pull" (required)
- `image`: string (required) - Image name:tag
- `host`: string (optional)

**Example:**

```json
{
  "action": "docker",
  "subaction": "pull",
  "image": "nginx:latest"
}
```

### build

Build image from Dockerfile.

**Parameters:**

- `action`: "docker" (required)
- `subaction`: "build" (required)
- `context`: string (required) - Build context path
- `tag`: string (required) - Image tag
- `host`: string (optional)
- `dockerfile`: string (optional, default: "Dockerfile")
- `no_cache`: boolean (optional)

**Example:**

```json
{
  "action": "docker",
  "subaction": "build",
  "context": "/opt/custom-app",
  "tag": "custom-app:v1"
}
```

### rmi

⚠️ **Destructive** - Remove image(s).

**Parameters:**

- `action`: "docker" (required)
- `subaction`: "rmi" (required)
- `image`: string (required)
- `host`: string (optional)
- `force`: boolean (required) - Must be true

**Example:**

```json
{
  "action": "docker",
  "subaction": "rmi",
  "image": "old-image:v1",
  "force": true
}
```

### info

Docker daemon information.

**Parameters:**

- `action`: "docker" (required)
- `subaction`: "info" (required)
- `host`: string (optional)

**Example:**

```json
{
  "action": "docker",
  "subaction": "info"
}
```

### df

Disk usage breakdown.

**Parameters:**

- `action`: "docker" (required)
- `subaction`: "df" (required)
- `host`: string (optional)

**Example:**

```json
{
  "action": "docker",
  "subaction": "df"
}
```

### networks

List Docker networks.

**Parameters:**

- `action`: "docker" (required)
- `subaction`: "networks" (required)
- `host`: string (optional)

**Example:**

```json
{
  "action": "docker",
  "subaction": "networks"
}
```

### volumes

List Docker volumes.

**Parameters:**

- `action`: "docker" (required)
- `subaction`: "volumes" (required)
- `host`: string (optional)

**Example:**

```json
{
  "action": "docker",
  "subaction": "volumes"
}
```

### prune

⚠️ **Destructive** - Remove unused Docker objects.

**Parameters:**

- `action`: "docker" (required)
- `subaction`: "prune" (required)
- `host`: string (optional)
- `force`: boolean (required) - Must be true
- `all`: boolean (optional) - Remove all unused images
- `volumes`: boolean (optional) - Prune volumes too

**Example:**

```json
{
  "action": "docker",
  "subaction": "prune",
  "force": true
}
```

---

## Host Operations

### status

✓ **Diagnostic** - Quick Docker connectivity health check.

**Parameters:**

- `action`: "host" (required)
- `subaction`: "status" (required)
- `host`: string (optional)

**Example:**

```json
{
  "action": "host",
  "subaction": "status"
}
```

### info

System information (OS, kernel, architecture).

**Parameters:**

- `action`: "host" (required)
- `subaction`: "info" (required)
- `host`: string (optional)

**Example:**

```json
{
  "action": "host",
  "subaction": "info"
}
```

### resources

CPU/memory/disk utilization.

**Parameters:**

- `action`: "host" (required)
- `subaction`: "resources" (required)
- `host`: string (optional)

**Example:**

```json
{
  "action": "host",
  "subaction": "resources"
}
```

### uptime

System uptime and load averages.

**Parameters:**

- `action`: "host" (required)
- `subaction`: "uptime" (required)
- `host`: string (optional)

**Example:**

```json
{
  "action": "host",
  "subaction": "uptime"
}
```

### services

systemd service status.

**Parameters:**

- `action`: "host" (required)
- `subaction`: "services" (required)
- `host`: string (optional)
- `service`: string (optional) - Specific systemd service name
- `state`: "running" | "failed" | "all" (optional, default: "all")

**Example:**

```json
{
  "action": "host",
  "subaction": "services",
  "service": "docker"
}
```

### network

Network interfaces and IP addresses.

**Parameters:**

- `action`: "host" (required)
- `subaction`: "network" (required)
- `host`: string (optional)

**Example:**

```json
{
  "action": "host",
  "subaction": "network"
}
```

### mounts

Mounted filesystems.

**Parameters:**

- `action`: "host" (required)
- `subaction`: "mounts" (required)
- `host`: string (optional)

**Example:**

```json
{
  "action": "host",
  "subaction": "mounts"
}
```

---

## Help System

### help

Auto-generated help documentation.

**Parameters:**

- `action`: "help" (required)
- `topic`: string (optional) - Specific operation (e.g., "container:restart")
- `format`: "markdown" | "json" (optional)

**Example:**

```json
{
  "action": "help",
  "topic": "container:restart"
}
```

---

## Common Parameters

All operations support these parameters:

| Parameter         | Type                 | Default     | Description                  |
| ----------------- | -------------------- | ----------- | ---------------------------- |
| `host`            | string               | (all hosts) | Target specific host         |
| `response_format` | "markdown" \| "json" | "markdown"  | Output format                |
| `limit`           | number               | 50          | Results per page (max: 1000) |
| `offset`          | number               | 0           | Pagination offset            |

---

## Destructive Operations

Operations requiring `force: true`:

- `container:recreate`
- `compose:down`
- `compose:recreate`
- `docker:rmi`
- `docker:prune`

These operations cannot be executed without explicit `force: true` parameter.

---

**Version:** 1.0.0
**Last Updated:** 2026-02-13
