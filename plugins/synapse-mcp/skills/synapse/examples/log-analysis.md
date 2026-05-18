# Log Analysis Example

Comprehensive log aggregation and analysis workflow using Flux and Scout.

## Scenario

Investigate application errors across distributed infrastructure:

- Container logs (Docker)
- System logs (journal, syslog)
- Application logs (nginx, postgres)
- Authentication logs

## Analysis Workflow

### 1. Container Log Analysis

**Find all container errors (last hour):**

```
/flux logs --all --since 1h --grep "ERROR|FATAL|EXCEPTION"
```

Returns errors from all containers across all hosts.

**Focus on specific service:**

```
/flux logs nginx --lines 100 --since 1h --grep "error"
```

**Time-range analysis:**

```
/flux logs plex --since "2024-01-15T14:00:00" --until "2024-01-15T16:00:00"
```

Narrow to specific incident window.

**Follow real-time:**

```
/flux logs media-stack --follow
```

Monitor for new errors as they occur.

### 2. System Log Analysis

**Check systemd journal for errors:**

```
/scout show journal on production --since 1h --priority err
```

System-level errors from last hour.

**Service-specific logs:**

```
/scout show journal on production --unit docker.service --since 24h
```

Docker daemon logs for troubleshooting.

**Kernel messages:**

```
/scout show dmesg on production --level err
```

Hardware or kernel-level issues.

### 3. Authentication Audit

**Recent SSH activity:**

```
/scout show auth logs on production --lines 100 --grep "sshd"
```

**Failed login attempts:**

```
/scout show auth logs on production --grep "Failed password"
```

Identify brute-force attempts.

**Successful logins:**

```
/scout show auth logs on production --grep "Accepted"
```

Verify expected access patterns.

**Sudo usage:**

```
/scout show auth logs on production --grep "sudo.*COMMAND"
```

Administrative activity audit.

### 4. Application-Specific Analysis

**Nginx access patterns:**

```
/flux logs nginx --lines 500 | grep "GET\|POST"
```

**Nginx errors:**

```
/flux logs nginx --grep "upstream\|timeout\|502\|503\|504"
```

**Database errors:**

```
/flux logs postgres --grep "ERROR\|FATAL"
```

**Application stack trace:**

```
/flux logs app --lines 200 --grep -A 10 "Exception"
```

Context around exceptions.

### 5. Cross-Service Correlation

**Timeline of events:**

1. **Container errors:**

```
/flux logs --all --since "2024-01-15T14:00:00" --until "2024-01-15T14:05:00"
```

2. **System journal:**

```
/scout show journal on production --since "2024-01-15T14:00:00" --until "2024-01-15T14:05:00"
```

3. **Combine findings** to identify root cause.

## Common Analysis Patterns

### Pattern 1: Performance Issues

**Identify slow requests:**

```
/flux logs nginx --grep "request_time.*[5-9]\." --lines 100
```

Requests taking >5 seconds.

**Check for resource exhaustion:**

```
/scout show journal on production --grep "Out of memory\|OOM"
```

**Review container stats during issue:**

```
/flux stats | grep -E "CPU.*[8-9][0-9]%|Memory.*[8-9][0-9]%"
```

### Pattern 2: Connection Failures

**Database connection errors:**

```
/flux logs app --grep "connection refused\|timeout\|ECONNREFUSED"
```

**Network issues:**

```
/scout show journal on production --unit networking.service --since 1h
```

**DNS problems:**

```
/scout show dmesg on production --grep "DNS\|resolve"
```

### Pattern 3: Deployment Issues

**Check recent restarts:**

```
/flux logs --all --since 15m --grep "Starting\|Started\|Stopping"
```

**Identify crashlooping containers:**

```
/flux list containers where state is restarting
```

**Review startup errors:**

```
/flux logs problematic-app --lines 50
```

## Log Aggregation Script

Automated log collection:

```bash
#!/bin/bash
# log-aggregator.sh

OUTPUT_DIR="/var/log/homelab-analysis"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
mkdir -p "$OUTPUT_DIR"

echo "Collecting logs at $TIMESTAMP"

# Container errors
echo "Collecting container errors..."
/flux logs --all --since 1h --grep "ERROR|FATAL" \
    > "$OUTPUT_DIR/container-errors-$TIMESTAMP.log"

# System journals
echo "Collecting system journals..."
for host in production storage media; do
    /scout show journal on $host --since 1h --priority err \
        > "$OUTPUT_DIR/${host}-journal-$TIMESTAMP.log"
done

# Auth logs
echo "Collecting auth logs..."
for host in production storage media; do
    /scout show auth logs on $host --since 1h \
        > "$OUTPUT_DIR/${host}-auth-$TIMESTAMP.log"
done

# Kernel messages
echo "Collecting kernel messages..."
for host in production storage media; do
    /scout show dmesg on $host --level err \
        > "$OUTPUT_DIR/${host}-dmesg-$TIMESTAMP.log"
done

echo "Log collection complete: $OUTPUT_DIR"
```

## Analysis Tools Integration

### ELK Stack Integration

```bash
#!/bin/bash
# elk-shipper.sh

# Ship container logs to Logstash
/flux logs --all --since 5m --format json | \
    curl -X POST http://logstash:5000 \
    -H "Content-Type: application/json" \
    --data-binary @-

# Ship system journals
for host in production storage media; do
    /scout show journal on $host --since 5m --format json | \
        curl -X POST http://logstash:5000 \
        -H "Content-Type: application/json" \
        --data-binary @-
done
```

### Splunk Integration

```bash
#!/bin/bash
# splunk-shipper.sh

SPLUNK_HEC="https://splunk:8088/services/collector"
SPLUNK_TOKEN="your-hec-token"

# Ship logs
/flux logs --all --since 5m --format json | \
    jq -c '.[] | {
        "event": .,
        "sourcetype": "docker:container",
        "index": "homelab"
    }' | \
    curl -X POST "$SPLUNK_HEC" \
        -H "Authorization: Splunk $SPLUNK_TOKEN" \
        -H "Content-Type: application/json" \
        --data-binary @-
```

## Real-Time Monitoring

### Error Rate Dashboard

```bash
#!/bin/bash
# error-rate-monitor.sh

while true; do
    clear
    echo "=== Error Rate Monitor ==="
    echo "$(date)"
    echo

    # Container errors (last 5min)
    container_errors=$(/flux logs --all --since 5m --grep "ERROR" | wc -l)
    echo "Container errors: $container_errors"

    # System errors (last 5min)
    system_errors=$(/scout show journal on all-hosts --since 5m --priority err | wc -l)
    echo "System errors: $system_errors"

    # Failed auth (last 5min)
    auth_failures=$(/scout show auth logs on all-hosts --since 5m --grep "Failed" | wc -l)
    echo "Auth failures: $auth_failures"

    echo
    if [ $container_errors -gt 10 ]; then
        echo "⚠️  High container error rate!"
    fi

    if [ $system_errors -gt 5 ]; then
        echo "⚠️  High system error rate!"
    fi

    if [ $auth_failures -gt 3 ]; then
        echo "🚨 Multiple authentication failures!"
    fi

    sleep 60
done
```

## Incident Investigation

### Step-by-Step Procedure

**1. Identify incident time:**

```
# When was the issue first reported?
INCIDENT_START="2024-01-15T14:00:00"
INCIDENT_END="2024-01-15T14:30:00"
```

**2. Collect container logs:**

```
/flux logs --all \
    --since "$INCIDENT_START" \
    --until "$INCIDENT_END" \
    > incident-container-logs.txt
```

**3. Collect system logs:**

```
for host in production storage media; do
    /scout show journal on $host \
        --since "$INCIDENT_START" \
        --until "$INCIDENT_END" \
        > incident-${host}-journal.txt
done
```

**4. Check for patterns:**

```bash
# Most common errors
grep -o "ERROR.*" incident-*.txt | sort | uniq -c | sort -rn | head -10

# Timeline of events
grep -h "ERROR\|FATAL" incident-*.txt | sort
```

**5. Identify root cause:**

- Correlate timestamps
- Look for cascading failures
- Check for external triggers

**6. Document findings:**

```bash
cat > incident-report.md <<EOF
# Incident Report: $(date)

## Timeline
- $INCIDENT_START: Issue first reported
- [key events from logs]
- $INCIDENT_END: Issue resolved

## Root Cause
[Analysis from logs]

## Resolution
[Actions taken]

## Prevention
[Changes to prevent recurrence]
EOF
```

## Best Practices

✅ **Aggregate logs from all sources**
✅ **Use time-range filters for incidents**
✅ **Correlate container + system logs**
✅ **Monitor error rates, not just occurrences**
✅ **Archive logs for historical analysis**

❌ **Don't ignore warning-level logs**
❌ **Don't analyze without time context**
❌ **Don't skip authentication logs**
❌ **Don't overlook kernel messages**

---

**Analysis Frequency:** Real-time + periodic reviews
**Log Retention:** 30+ days (configurable)
**Alert Threshold:** >10 errors/5min
