# Docker Deployment Example

Complete workflow for deploying a Docker Compose application using Flux.

## Scenario

Deploy a new version of a media stack (Plex, Sonarr, Radarr) on production server.

## Prerequisites

- Compose project: `media-stack`
- Host: `production`
- Services: plex, sonarr, radarr, transmission

## Workflow

### 1. Pre-Deployment Checks

**Check current system health:**

```
/flux check host status on production
```

Expected response: Docker connectivity OK

**List running containers:**

```
/flux list containers on production where state is running
```

Review currently running media services.

**Check system resources:**

```
/flux show system resources on production
```

Ensure sufficient CPU, memory, and disk space.

### 2. Backup Current Configuration

**Read compose file:**

```
/scout read production:/opt/stacks/media/docker-compose.yml
```

**Backup to local:**

```
/scout copy production:/opt/stacks/media/docker-compose.yml to local:./backup/media-compose-backup.yml
```

### 3. Pull Latest Images

**Pull new images without disrupting services:**

```
/flux pull images for media-stack on production
```

This downloads new images while old containers run.

### 4. Review Recent Logs

**Check for any existing issues:**

```
/flux logs media-stack --lines 20
```

Look for errors or warnings before proceeding.

### 5. Stop Old Version

**Gracefully stop services:**

```
/flux stop media-stack on production
```

Confirmation required for `down` operation:

```
/flux down media-stack on production --confirm
```

### 6. Start New Version

**Bring up updated services:**

```
/flux up media-stack on production
```

Flux will:

- Create containers with new images
- Attach to networks
- Mount volumes
- Start services

### 7. Verify Deployment

**Check container status:**

```
/flux list containers on production where name contains media-stack
```

All services should show "running" state.

**Monitor startup logs:**

```
/flux logs media-stack --lines 50 --follow
```

Watch for successful initialization messages.

**Check resource usage:**

```
/flux stats on production where name contains media-stack
```

Verify containers aren't using excessive resources.

### 8. Health Checks

**Test individual services:**

```
/flux exec plex curl -f http://localhost:32400/web
/flux exec sonarr curl -f http://localhost:8989/api/v3/system/status
/flux exec radarr curl -f http://localhost:7878/api/v3/system/status
```

**Check network connectivity:**

```
/flux inspect media-stack
```

Review port mappings and network configuration.

### 9. Post-Deployment Monitoring

**Monitor for 5-10 minutes:**

```
/flux logs media-stack --follow
```

Watch for any errors or crashes.

**Check error logs:**

```
/flux logs media-stack --since 10m --grep "ERROR|FATAL|EXCEPTION"
```

Should return minimal or no errors.

## Rollback Procedure

If deployment fails:

1. **Stop new version:**

```
/flux down media-stack on production --confirm
```

2. **Restore backup configuration:**

```
/scout copy local:./backup/media-compose-backup.yml to production:/opt/stacks/media/docker-compose.yml
```

3. **Start old version:**

```
/flux up media-stack on production
```

4. **Verify rollback:**

```
/flux list containers on production where name contains media-stack
```

## Troubleshooting

### Container Won't Start

**Check logs:**

```
/flux logs plex --lines 100
```

**Inspect configuration:**

```
/flux inspect plex
```

**Verify image:**

```
/flux list images on production where name contains plex
```

### Port Conflicts

**Check port usage:**

```
/flux show ports on production
```

**Find conflicting container:**

```
/flux list containers on production where ports contain 32400
```

### Resource Issues

**Check available resources:**

```
/flux show resources on production
```

**Identify resource hogs:**

```
/scout show processes on production where cpu > 80
```

## Best Practices

✅ **Always backup configurations before deployment**
✅ **Pull images first to reduce downtime**
✅ **Monitor logs during and after deployment**
✅ **Have rollback plan ready**
✅ **Test in staging environment first**

❌ **Don't deploy during peak usage**
❌ **Don't skip health checks**
❌ **Don't ignore warning signs in logs**

## Automation

For automated deployments, combine operations:

```bash
#!/bin/bash
# Pre-deployment
/flux check host status on production || exit 1
/flux show resources on production

# Backup
/scout copy production:/opt/stacks/media/docker-compose.yml to ./backup/

# Deploy
/flux pull images for media-stack on production
/flux down media-stack on production --confirm
/flux up media-stack on production

# Verify
sleep 30
/flux list containers on production where name contains media-stack
/flux logs media-stack --lines 20 --grep "ERROR"

# Health check
/flux stats on production where name contains media-stack
```

---

**Deployment Time:** ~2-5 minutes (depending on image sizes)
**Downtime:** ~30-60 seconds (between down and up)
**Risk Level:** Medium (have rollback ready)
