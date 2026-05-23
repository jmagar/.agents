---
name: tracearr
description: Use when working with Tracearr media-server monitoring for Plex, Jellyfin, or Emby, including real-time sessions, stream analytics, account-sharing detection, trust scores, alerts, imports from Tautulli/Jellystat, Docker deployment, configuration, or Tracearr's public API.
---

# Tracearr

Use this skill for Tracearr media-server monitoring workflows.

## What Tracearr Is

Tracearr is an open-source, self-hosted monitoring platform for Plex, Jellyfin,
and Emby. It unifies multiple media servers into one dashboard and tracks active
streams, historical playback, geolocation, bandwidth, transcodes, device usage,
library metrics, trust scores, and account-sharing signals.

## Common Tasks

- Deploy Tracearr with Docker, TimescaleDB/PostgreSQL, and Redis.
- Connect Plex through Plex sign-in, or connect Jellyfin/Emby with server URL,
  friendly name, and API key.
- Investigate active streams, stream map location patterns, transcodes, device
  health, bandwidth, live TV, and music sessions.
- Review account-sharing detection rules: impossible travel, simultaneous
  locations, device velocity, concurrent streams, geo restrictions, and account
  inactivity.
- Configure alerts through Discord webhooks or custom notifications.
- Import history from Tautulli or Jellystat.
- Use Tracearr's read-only public REST API once an API key is generated in
  settings; Swagger UI is available at `/api-docs`.

## Workflow

1. Identify the Tracearr URL, deployment mode, and whether an API key is
   available. If not, use container logs and the web UI as the fallback surface.
2. For active-stream or sharing investigations, collect the account, server,
   session id, device/client, IP/geolocation, timestamp range, and rule that
   triggered the signal before drawing conclusions.
3. For imports from Tautulli or Jellystat, confirm source URL, token, history
   range, and duplicate-handling expectations before starting an import.
4. For alert changes, verify destination, trigger threshold, and test-delivery
   behavior. Do not silently enable noisy account-sharing alerts.
5. For deployment failures, inspect app logs, PostgreSQL/TimescaleDB reachability,
   Redis reachability, environment variables, migrations, and reverse-proxy base
   path settings.

## Configuration Notes

- Required runtime services: TimescaleDB/PostgreSQL and Redis.
- Common Docker tags: `supervised` for all-in-one, `latest` for app with
  external DB/Redis, plus `next` and `nightly` variants.
- Required environment variables include `DATABASE_URL` and `REDIS_URL`.
- Deployment docs generate `JWT_SECRET` and `COOKIE_SECRET` as random
  64-character hexadecimal values.
- Optional environment variables include `PORT`, `NODE_ENV`, `LOG_LEVEL`, `TZ`,
  `CORS_ORIGIN`, `CLAIM_CODE`, `BASE_PATH`, `DNS_CACHE_MAX_TTL`,
  `GZIP_ENABLED`, and `BACKUP_DIR`.

## Fallbacks

Prefer a Tracearr MCP tool if one is available in the active environment. When
there is no MCP server, use Tracearr's public API for read-only integrations and
Docker/log inspection for operational diagnostics. For writes, state the exact
UI or API operation and confirm the affected server, user, rule, or import
before changing it.
