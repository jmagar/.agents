# Synapsis Skill

Homelab infrastructure management using Flux (Docker) and Scout (SSH) tools from synapse-mcp.

## What It Does

Synapsis provides comprehensive homelab infrastructure management through two specialized tools:

**Flux (Docker Management):**

- Container lifecycle (start, stop, restart, logs, stats, exec)
- Compose orchestration (up, down, recreate, auto-discovery)
- Image management (pull, build, prune)
- Host diagnostics (resources, uptime, services, network)

**Scout (SSH Operations):**

- Remote file operations (read, transfer, compare)
- Allowlisted command execution
- ZFS management (pools, datasets, snapshots)
- Log aggregation (syslog, journal, dmesg, auth)

**Key Features:**

- ✅ Multi-host orchestration with auto-discovery
- ✅ Intelligent caching (Compose projects, SSH connections)
- ✅ Security-first (command allowlisting, path validation)
- ✅ 59 total operations (43 Flux + 16 Scout)

## Prerequisites

- **synapse-mcp MCP server** (included in this repository)
- **Node.js** v20+ (for running MCP server)
- **SSH access** to managed hosts
- **Docker** installed on managed hosts
- **ZFS** (optional, for storage management features)

## Setup

### 1. Build the MCP Server

```bash
cd ~/workspace/synapse-mcp
npm install
npm run build
```

### 2. SSH Key Setup

If you don't already have SSH keys configured for your homelab hosts:

1. **Generate Ed25519 key** (if needed):

   ```bash
   ssh-keygen -t ed25519 -C "homelab-management"
   ```

2. **Add to ssh-agent**:

   ```bash
   eval "$(ssh-agent -s)"
   ssh-add ~/.ssh/id_ed25519
   ```

3. **Configure in `~/.ssh/config`**:

   ```ssh-config
   Host production
     HostName 192.168.1.100
     User admin
     IdentityFile ~/.ssh/id_ed25519

   Host storage
     HostName 192.168.1.101
     User admin
     IdentityFile ~/.ssh/id_ed25519
   ```

4. **Copy public key to hosts**:

   ```bash
   ssh-copy-id production
   ssh-copy-id storage
   ```

5. **Test connection**:
   ```bash
   ssh production "echo Connected successfully"
   ```

### 3. Configure Hosts

**Option A: Auto-Discovery (Recommended)**

Add hosts to `~/.ssh/config`:

```ssh-config
Host production
  HostName 192.168.1.100
  User admin
  IdentityFile ~/.ssh/id_ed25519

Host storage
  HostName nas.local
  User root
  IdentityFile ~/.ssh/id_rsa
```

Hosts are automatically discovered and available.

**Option B: Manual Configuration**

Create `synapse.config.json`:

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
      "tags": ["production"]
    }
  ]
}
```

Set location:

```bash
export SYNAPSE_CONFIG_FILE=/path/to/synapse.config.json
```

### 4. Install Claude Code Plugin

The plugin auto-installs when you use Claude Code in this repository, or install manually:

```bash
# Link plugin to Claude Code
ln -s ~/workspace/synapse-mcp ~/.claude/plugins/synapse-mcp

# Or copy to project
cp -r ~/workspace/synapse-mcp /your/project/.claude-plugin/
```

### 5. Verify Installation

In Claude Code:

```
/flux check host status
```

Should show Docker connectivity status for all hosts.

## Quick Start

### List All Hosts

```
/scout list hosts
```

### Check Docker Status

```
/flux check all hosts
```

### List Running Containers

```
/flux list containers where state is running
```

### Start Compose Project

```
/flux up media-stack
```

### Read Remote File

```
/scout read production:/etc/docker/daemon.json
```

### Check ZFS Pools

```
/scout show zfs pools on storage
```

### View Container Logs

```
/flux logs nginx --lines 50 --grep error
```

## Usage Examples

### Docker Deployment

```
1. /flux pull images for media-stack
2. /flux down media-stack --confirm
3. /flux up media-stack
4. /flux logs media-stack --lines 20
```

### Multi-Host Health Check

```
/flux show resources on all hosts
/scout show zfs pools on storage
/flux stats
```

### Log Analysis

```
/flux logs --all --since 1h --grep "ERROR"
/scout show journal on production --priority err
/scout show auth logs on production --grep "Failed"
```

## Configuration

### Environment Variables

Set these for customization:

```bash
# Host configuration
export SYNAPSE_CONFIG_FILE=/path/to/synapse.config.json
export SYNAPSE_DEFAULT_HOST=production

# SSH connection pooling
export SSH_POOL_MAX_CONNECTIONS=10

# Compose cache TTL (hours)
export COMPOSE_CACHE_TTL_HOURS=24
```

### Compose Search Paths

Default search paths for Docker Compose projects:

- `/compose`
- `/mnt/cache/compose`
- `/mnt/cache/code`

Customize per host in `synapse.config.json`:

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

## Troubleshooting

### "Failed to connect to host"

**Check SSH connectivity:**

```bash
ssh production
```

**Verify SSH config:**

```bash
cat ~/.ssh/config | grep -A 3 "Host production"
```

### "Compose project not found"

**Refresh cache:**

```
/flux refresh compose cache
```

**Check project location:**

```
/scout read production:/opt/stacks --tree
```

**Add to search paths** in `synapse.config.json`

### "Command not allowed"

Scout `exec` only allows safe commands (cat, grep, find, ls, etc.). Use Scout's specialized operations instead:

- Read file → `/scout read host:path`
- List files → `/scout read host:path --tree`
- Find files → `/scout find host:pattern`

### "Permission denied"

**Verify SSH key permissions:**

```bash
chmod 600 ~/.ssh/id_ed25519
chmod 700 ~/.ssh
```

**Check Docker socket access:**

```
/flux show services on production --filter docker
```

### Docker connection failed

**Check Docker status:**

```
/flux check host status on production
```

**Verify Docker running:**

```
/scout exec production ss -tlnp | grep 2375
```

## Documentation

**For Claude Code:**

- See `SKILL.md` - Complete skill documentation with workflows and best practices

**Detailed References:**

- `references/flux-operations.md` - All 43 Flux operations with parameters
- `references/scout-operations.md` - All 16 Scout operations with parameters
- `references/workflows.md` - Detailed workflow examples
- `references/best-practices.md` - Advanced usage patterns
- `references/troubleshooting.md` - Common issues and solutions

**Working Examples:**

- `examples/docker-deployment.md` - Complete deployment workflow
- `examples/multi-host-monitoring.md` - Health check automation
- `examples/log-analysis.md` - Centralized log aggregation

**MCP Server:**

- See main repository README.md for MCP server documentation
- Architecture docs in `docs/ARCHITECTURE.md`
- Security details in `SECURITY.md`

## Support

- **GitHub:** https://github.com/jmagar/synapse-mcp
- **Issues:** https://github.com/jmagar/synapse-mcp/issues
- **License:** MIT

## Version

**Skill Version:** 1.0.0
**MCP Server Version:** 1.0.0
**Last Updated:** 2026-02-13
