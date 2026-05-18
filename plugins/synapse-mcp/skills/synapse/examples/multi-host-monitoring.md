# Multi-Host Monitoring Example

Comprehensive monitoring workflow across distributed homelab infrastructure.

## Scenario

Monitor health across 3 hosts:

- `production` - Main application server
- `storage` - NAS with ZFS
- `media` - Media processing server

## Monitoring Dashboard Workflow

### 1. Infrastructure Overview

**List all managed hosts:**

```
/scout list hosts
```

Expected: 3 hosts (production, storage, media)

**Check Docker status across all hosts:**

```
/flux check all hosts
```

Quick health check for Docker connectivity.

### 2. System Resources

**Production server:**

```
/flux show system resources on production
```

Review:

- CPU usage %
- Memory usage (used/total)
- Disk usage per mount

**Storage server:**

```
/flux show system resources on storage
```

Focus on disk usage for data mounts.

**Media server:**

```
/flux show system resources on media
```

Monitor for encoding/processing workloads.

### 3. Container Health

**List all running containers:**

```
/flux list containers where state is running
```

Returns containers from all hosts with their status.

**Check for exited containers:**

```
/flux list containers where state is exited
```

Investigate any unexpected exits.

**Resource consumption across fleet:**

```
/flux stats
```

Real-time CPU, memory, network, and I/O for all containers.

### 4. Storage Health (ZFS)

**Check pool status:**

```
/scout show zfs pools on storage
```

Review:

- Pool health (ONLINE, DEGRADED, FAULTED)
- Capacity usage
- Fragmentation percentage

**Dataset usage:**

```
/scout show zfs datasets on storage
```

Identify datasets approaching capacity limits.

**Recent snapshots:**

```
/scout show zfs snapshots on storage
```

Verify backup snapshots are being created.

### 5. Network Status

**Check network interfaces:**

```
/flux show network on production
/flux show network on storage
/flux show network on media
```

Verify:

- All interfaces UP
- IP addresses correct
- No errors/drops

**Container port mappings:**

```
/flux show ports
```

Review exposed ports across all hosts.

### 6. Service Status

**Check critical services:**

```
/flux show services on production where name contains docker
/flux show services on storage where name contains smb
/flux show services on media where name contains plex
```

Ensure critical services are active and enabled.

### 7. Disk Usage

**All mounts across infrastructure:**

```
/flux show mounts
```

Review disk usage for:

- Root filesystems
- Data mounts
- Backup locations

**Parallel disk check:**

```
/scout exec all-hosts df -h | grep -v tmpfs
```

Quick overview of all filesystem usage.

## Alerting Thresholds

### Resource Alerts

**High CPU (>80%):**

```
/flux show resources | grep "CPU.*[8-9][0-9]%\|CPU.*100%"
```

**High Memory (>85%):**

```
/flux show resources | grep "Memory.*8[5-9]%\|Memory.*9[0-9]%"
```

**Low Disk (<10% free):**

```
/scout exec all-hosts df -h | grep -E " [0-9]%| 9[0-9]%"
```

### Container Alerts

**Crashed containers:**

```
/flux list containers where state is exited
```

**High restart count:**

```
/flux list containers | grep "restart"
```

**Resource-hogging containers:**

```
/flux stats | grep -E "CPU.*[8-9][0-9]%|Memory.*[8-9][0-9]%"
```

### Storage Alerts

**ZFS pool degraded:**

```
/scout show zfs pools on storage | grep -v ONLINE
```

**High dataset usage (>80%):**

```
/scout show zfs datasets on storage | grep -E " [8-9][0-9]%| 100%"
```

**Missing snapshots (check last 24h):**

```
/scout show zfs snapshots on storage --since 24h
```

## Monitoring Script

Automated monitoring with Bash:

```bash
#!/bin/bash
# homelab-monitor.sh

echo "=== Infrastructure Health Check ==="
echo

echo "1. Host Status"
/flux check all hosts

echo
echo "2. System Resources"
for host in production storage media; do
    echo "--- $host ---"
    /flux show resources on $host
done

echo
echo "3. Container Health"
/flux list containers where state is running | wc -l
echo "running containers"

exited=$(/flux list containers where state is exited | wc -l)
if [ "$exited" -gt 0 ]; then
    echo "⚠️  $exited containers exited"
    /flux list containers where state is exited
fi

echo
echo "4. Storage (ZFS)"
/scout show zfs pools on storage

echo
echo "5. Disk Usage"
/scout exec all-hosts df -h | grep -E "^/dev" | awk '$5 > "80%" {print "⚠️ " $0}'

echo
echo "6. Error Check (last hour)"
errors=$(/flux logs --all --since 1h --grep "ERROR|FATAL" | wc -l)
echo "$errors errors found in logs"

echo
echo "=== Health Check Complete ==="
```

## Grafana Integration

For visualization, collect metrics:

```bash
#!/bin/bash
# metrics-collector.sh

# Collect stats in JSON format
/flux stats --format json > /tmp/container-stats.json

# Collect host resources
for host in production storage media; do
    /flux show resources on $host --format json > /tmp/${host}-resources.json
done

# Collect ZFS metrics
/scout show zfs pools on storage --format json > /tmp/zfs-pools.json

# Push to Prometheus pushgateway
curl -X POST http://localhost:9091/metrics/job/homelab \
    --data-binary @/tmp/container-stats.json
```

## Log Aggregation

Centralized log collection:

```bash
#!/bin/bash
# log-aggregation.sh

# Collect container errors (last hour)
/flux logs --all --since 1h --grep "ERROR" > /var/log/homelab/container-errors.log

# Collect system journal errors
for host in production storage media; do
    /scout show journal on $host --since 1h --priority err \
        > /var/log/homelab/${host}-journal.log
done

# Collect auth logs
for host in production storage media; do
    /scout show auth logs on $host --since 1h \
        > /var/log/homelab/${host}-auth.log
done
```

## Response Procedures

### High CPU Alert

1. Identify culprit: `/flux stats | sort by CPU`
2. Check processes: `/flux top container-name`
3. Review logs: `/flux logs container-name --since 1h`
4. Consider scaling or optimization

### Container Crash

1. Check exit reason: `/flux inspect crashed-container`
2. Review logs: `/flux logs crashed-container --lines 100`
3. Check resources: `/flux show resources on host`
4. Restart if appropriate: `/flux start crashed-container`

### Storage Full

1. Identify large datasets: `/scout show zfs datasets on storage`
2. Clean up old snapshots: (manual ZFS operation)
3. Move data to other pools
4. Increase capacity

### ZFS Pool Degraded

1. Check pool status: `/scout show zfs pools on storage`
2. Identify failed drive: (use zpool status directly)
3. Replace drive procedure
4. Resilver and verify

## Best Practices

✅ **Run health checks every 5-15 minutes**
✅ **Alert on threshold violations**
✅ **Aggregate logs for correlation**
✅ **Monitor trends, not just point-in-time**
✅ **Document response procedures**

❌ **Don't ignore transient alerts**
❌ **Don't wait for multiple failures**
❌ **Don't skip ZFS scrubs**
❌ **Don't overlook authentication logs**

---

**Monitoring Frequency:** 5-15 minutes
**Alert Response Time:** <5 minutes
**Dashboard Refresh:** Real-time
