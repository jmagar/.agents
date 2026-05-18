# Workflow Guide

Detailed workflows for common homelab infrastructure management tasks.

## Table of Contents

- [Docker Deployment](#docker-deployment)
- [Multi-Host Monitoring](#multi-host-monitoring)
- [Log Aggregation & Analysis](#log-aggregation--analysis)
- [Troubleshooting](#troubleshooting)
- [Backup & Recovery](#backup--recovery)
- [Performance Optimization](#performance-optimization)

---

## Docker Deployment

### Complete Deployment Workflow

**Scenario:** Deploy new version of multi-service application

**Steps:**

1. **Pre-deployment health check**

```json
{
  "action": "host",
  "subaction": "status",
  "host": "production"
}
```

2. **Check current container status**

```json
{
  "action": "container",
  "subaction": "list",
  "host": "production",
  "state": "running"
}
```

3. **Pull latest images**

```json
{
  "action": "compose",
  "subaction": "pull",
  "project": "media-stack",
  "host": "production"
}
```

4. **Review recent logs before update**

```json
{
  "action": "compose",
  "subaction": "logs",
  "project": "media-stack",
  "lines": 20
}
```

5. **Stop old version gracefully**

```json
{
  "action": "compose",
  "subaction": "down",
  "project": "media-stack",
  "host": "production",
  "force": true
}
```

6. **Start new version**

```json
{
  "action": "compose",
  "subaction": "up",
  "project": "media-stack",
  "host": "production"
}
```

7. **Verify containers started**

```json
{
  "action": "container",
  "subaction": "list",
  "host": "production",
  "name_filter": "media-stack"
}
```

8. **Monitor startup logs**

```json
{
  "action": "compose",
  "subaction": "logs",
  "project": "media-stack",
  "lines": 50,
  "follow": true
}
```

9. **Check resource usage**

```json
{
  "action": "container",
  "subaction": "stats",
  "host": "production"
}
```

10. **Post-deployment health check**

```json
{
  "action": "host",
  "subaction": "doctor",
  "host": "production"
}
```

### Rolling Restart

**Scenario:** Restart services with minimal downtime

**Steps:**

1. **Check service status**

```json
{
  "action": "compose",
  "subaction": "status",
  "project": "media-stack"
}
```

2. **Restart one service at a time**

```json
{
  "action": "compose",
  "subaction": "restart",
  "project": "media-stack",
  "service": "plex"
}
```

3. **Verify service health**

```json
{
  "action": "container",
  "subaction": "logs",
  "container_id": "plex",
  "lines": 20
}
```

4. **Repeat for other services**

### Blue-Green Deployment

**Scenario:** Zero-downtime deployment with fallback

**Steps:**

1. **Deploy green version alongside blue**

```json
{
  "action": "compose",
  "subaction": "up",
  "project": "media-stack-green",
  "host": "production"
}
```

2. **Verify green version health**

```json
{
  "action": "container",
  "subaction": "stats",
  "host": "production",
  "name_filter": "green"
}
```

3. **Switch traffic (update reverse proxy)**

```json
{
  "action": "container",
  "subaction": "exec",
  "container_id": "nginx",
  "command": "nginx -s reload"
}
```

4. **Monitor green version**

```json
{
  "action": "compose",
  "subaction": "logs",
  "project": "media-stack-green",
  "lines": 50
}
```

5. **Decommission blue version after validation**

```json
{
  "action": "compose",
  "subaction": "down",
  "project": "media-stack-blue",
  "force": true
}
```

---

## Multi-Host Monitoring

### Infrastructure Overview

**Scenario:** Get health snapshot across all hosts

**Steps:**

1. **List all managed hosts**

```json
{
  "action": "nodes"
}
```

2. **Check Docker status on all hosts**

```json
{
  "action": "host",
  "subaction": "status"
}
```

3. **Get system resources for each host**

```json
{
  "action": "host",
  "subaction": "resources",
  "host": "host1"
}
```

Repeat for each host or omit `host` parameter for all

4. **Check critical services**

```json
{
  "action": "host",
  "subaction": "services",
  "filter": "docker"
}
```

5. **View network status**

```json
{
  "action": "host",
  "subaction": "network"
}
```

### Storage Health Monitoring

**Scenario:** Monitor ZFS pools and disk usage

**Steps:**

1. **Check ZFS pool health**

```json
{
  "action": "zfs",
  "subaction": "pools",
  "host": "storage-server"
}
```

2. **Review dataset usage**

```json
{
  "action": "zfs",
  "subaction": "datasets",
  "host": "storage-server"
}
```

3. **Check snapshot status**

```json
{
  "action": "zfs",
  "subaction": "snapshots",
  "host": "storage-server"
}
```

4. **Disk usage across hosts**

```json
{
  "action": "exec",
  "command": "df -h"
}
```

Use `/scout emit` for parallel execution

5. **Check mount points**

```json
{
  "action": "host",
  "subaction": "mounts"
}
```

### Container Health Dashboard

**Scenario:** Monitor running containers across infrastructure

**Steps:**

1. **List all running containers**

```json
{
  "action": "container",
  "subaction": "list",
  "state": "running"
}
```

2. **Check resource consumption**

```json
{
  "action": "container",
  "subaction": "stats"
}
```

3. **Identify unhealthy containers**

```json
{
  "action": "container",
  "subaction": "list",
  "state": "exited"
}
```

4. **Review logs for errors**

```json
{
  "action": "container",
  "subaction": "logs",
  "grep": "error|fatal|exception"
}
```

---

## Log Aggregation & Analysis

### Centralized Error Tracking

**Scenario:** Find errors across all services and hosts

**Steps:**

1. **Search container logs for errors**

```json
{
  "action": "container",
  "subaction": "logs",
  "lines": 100,
  "since": "1h",
  "grep": "ERROR|FATAL|EXCEPTION"
}
```

2. **Check system journal for errors**

```json
{
  "action": "logs",
  "subaction": "journal",
  "host": "production",
  "since": "1h",
  "priority": "err"
}
```

3. **Review syslog for issues**

```json
{
  "action": "logs",
  "subaction": "syslog",
  "host": "production",
  "lines": 100,
  "grep": "error|fail"
}
```

4. **Check kernel messages**

```json
{
  "action": "logs",
  "subaction": "dmesg",
  "host": "production",
  "level": "err"
}
```

### Authentication Audit

**Scenario:** Review authentication attempts

**Steps:**

1. **Check recent SSH logins**

```json
{
  "action": "logs",
  "subaction": "auth",
  "host": "production",
  "lines": 100,
  "grep": "sshd"
}
```

2. **Find failed login attempts**

```json
{
  "action": "logs",
  "subaction": "auth",
  "host": "production",
  "grep": "Failed password"
}
```

3. **Review sudo usage**

```json
{
  "action": "logs",
  "subaction": "auth",
  "host": "production",
  "grep": "sudo"
}
```

### Service-Specific Log Analysis

**Scenario:** Deep dive into specific service logs

**Steps:**

1. **Get service logs with context**

```json
{
  "action": "logs",
  "subaction": "journal",
  "host": "production",
  "unit": "nginx.service",
  "lines": 200,
  "since": "24h"
}
```

2. **Filter by keyword**

```json
{
  "action": "logs",
  "subaction": "journal",
  "host": "production",
  "unit": "docker.service",
  "grep": "restart"
}
```

3. **Time-range analysis**

```json
{
  "action": "logs",
  "subaction": "journal",
  "host": "production",
  "unit": "docker.service",
  "since": "2024-01-15T14:00:00",
  "until": "2024-01-15T16:00:00"
}
```

---

## Troubleshooting

### Container Won't Start

**Steps:**

1. **Check container status**

```json
{
  "action": "container",
  "subaction": "list",
  "name_filter": "problematic-service"
}
```

2. **Review startup logs**

```json
{
  "action": "container",
  "subaction": "logs",
  "container_id": "problematic-service",
  "lines": 100
}
```

3. **Inspect configuration**

```json
{
  "action": "container",
  "subaction": "inspect",
  "container_id": "problematic-service"
}
```

4. **Check for port conflicts**

```json
{
  "action": "host",
  "subaction": "ports",
  "host": "production"
}
```

5. **Verify image exists**

```json
{
  "action": "docker",
  "subaction": "images",
  "filter": "problematic-service"
}
```

6. **Check system resources**

```json
{
  "action": "host",
  "subaction": "resources",
  "host": "production"
}
```

### Performance Degradation

**Steps:**

1. **Check container resource usage**

```json
{
  "action": "container",
  "subaction": "stats"
}
```

2. **Identify resource hogs**

```json
{
  "action": "ps",
  "host": "production",
  "cpu_threshold": 50.0,
  "sort_by": "cpu"
}
```

3. **Check system load**

```json
{
  "action": "host",
  "subaction": "uptime",
  "host": "production"
}
```

4. **Review disk I/O**

```json
{
  "action": "container",
  "subaction": "top",
  "container_id": "slow-service"
}
```

5. **Check for OOM kills**

```json
{
  "action": "logs",
  "subaction": "dmesg",
  "host": "production",
  "grep": "Out of memory"
}
```

### Network Connectivity Issues

**Steps:**

1. **Check container network**

```json
{
  "action": "container",
  "subaction": "inspect",
  "container_id": "service",
  "summary": true
}
```

2. **List Docker networks**

```json
{
  "action": "docker",
  "subaction": "networks",
  "host": "production"
}
```

3. **Check host network interfaces**

```json
{
  "action": "host",
  "subaction": "network",
  "host": "production"
}
```

4. **Test connectivity**

```json
{
  "action": "exec",
  "host": "production",
  "command": "ping -c 4 google.com"
}
```

---

## Backup & Recovery

### Configuration Backup

**Steps:**

1. **Read compose configuration**

```json
{
  "action": "peek",
  "target": "production:/opt/stacks/media/docker-compose.yml"
}
```

2. **Transfer to backup host**

```json
{
  "action": "beam",
  "source": "production:/opt/stacks/media/docker-compose.yml",
  "destination": "backup-server:/backups/configs/media-compose.yml"
}
```

3. **Verify transfer**

```json
{
  "action": "delta",
  "source": "production:/opt/stacks/media/docker-compose.yml",
  "target": "backup-server:/backups/configs/media-compose.yml"
}
```

### Disaster Recovery

**Steps:**

1. **Assess system state**

```json
{
  "action": "host",
  "subaction": "doctor",
  "host": "production"
}
```

2. **Stop affected services**

```json
{
  "action": "compose",
  "subaction": "down",
  "project": "affected-stack",
  "force": true
}
```

3. **Restore configurations from backup**

```json
{
  "action": "beam",
  "source": "backup-server:/backups/configs/compose.yml",
  "destination": "production:/opt/stacks/restored/docker-compose.yml"
}
```

4. **Verify configurations**

```json
{
  "action": "peek",
  "target": "production:/opt/stacks/restored/docker-compose.yml"
}
```

5. **Restart services**

```json
{
  "action": "compose",
  "subaction": "up",
  "project": "restored-stack"
}
```

---

## Performance Optimization

### Image Cleanup

**Steps:**

1. **Check disk usage**

```json
{
  "action": "docker",
  "subaction": "df",
  "host": "production"
}
```

2. **List unused images**

```json
{
  "action": "docker",
  "subaction": "images",
  "host": "production"
}
```

3. **Prune unused images**

```json
{
  "action": "docker",
  "subaction": "prune",
  "host": "production",
  "force": true
}
```

4. **Verify space reclaimed**

```json
{
  "action": "docker",
  "subaction": "df",
  "host": "production"
}
```

### Resource Optimization

**Steps:**

1. **Identify resource-heavy containers**

```json
{
  "action": "container",
  "subaction": "stats"
}
```

2. **Check container processes**

```json
{
  "action": "container",
  "subaction": "top",
  "container_id": "heavy-container"
}
```

3. **Review container limits** (via inspect)

4. **Consider scaling or optimization** based on findings

---

**Version:** 1.0.0
**Last Updated:** 2026-02-13
