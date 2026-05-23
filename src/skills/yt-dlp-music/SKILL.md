---
name: yt-dlp-music
description: This skill should be used when the user asks to "search YouTube for music", "download an album", "download a track", "download songs with yt-dlp", "rip audio from YouTube", "find this album on YouTube", or mentions yt-dlp music, YouTube albums, playlists, tracks, MP3, M4A, Opus, FLAC, or audio metadata.
---

# yt-dlp Music

Use this skill for YouTube music search and audio download workflows with `yt-dlp`.

## Operating Rules

- Download only content the user is authorized to download, such as their own uploads, public-domain material, Creative Commons/licensed content, or content they otherwise have rights to keep.
- Prefer preview and confirmation before downloading when the requested source is ambiguous, especially for full albums, playlists, live recordings, remasters, or unofficial uploads.
- Do not invent metadata. Use `yt-dlp` metadata, user-provided metadata, or clearly label any unresolved fields.
- Avoid destructive file operations. Never overwrite an existing music directory without checking the target path first.
- Keep commands minimal. Do not add flags the user did not ask for unless required for reliable music extraction, metadata, or safe output paths.

## Initial Checks

Verify required tools before searching or downloading:

```bash
command -v yt-dlp
yt-dlp --version
command -v ffmpeg
```

If `ffmpeg` is missing, report that audio extraction/format conversion may fail and either install it only if asked or use `yt-dlp` without conversion when acceptable.

## Search Workflow

For a track or album query, search YouTube with `yt-dlp` and return candidate titles, channels, durations, and URLs. Use small result counts first.

```bash
yt-dlp "ytsearch10:<artist> <track or album>" --flat-playlist --print "%(title)s | %(channel)s | %(duration_string)s | %(webpage_url)s"
```

For album searches, include album terms such as `full album`, official artist name, release year, or label only when the user provided them or they are necessary to disambiguate.

When the search result is ambiguous:

1. Present the best candidates.
2. Ask which one to download.
3. Do not download until the user selects a candidate.

When the user provides an explicit URL, skip search and inspect the URL directly:

```bash
yt-dlp --dump-single-json --flat-playlist "<url>"
```

## Download Targets

Default to a user-owned music staging directory unless the user gives a destination:

```text
~/Downloads/yt-dlp-music/
```

Use stable subdirectories:

```text
~/Downloads/yt-dlp-music/%(artist,uploader|Unknown Artist)s/%(album,playlist_title|Singles)s/
```

Before downloading, check whether the destination exists and whether files with the intended names already exist.

## Track Download

Use this for a single selected track URL:

```bash
yt-dlp \
  --extract-audio \
  --audio-format m4a \
  --embed-metadata \
  --embed-thumbnail \
  --convert-thumbnails jpg \
  --no-overwrites \
  -o "$HOME/Downloads/yt-dlp-music/%(artist,uploader|Unknown Artist)s/%(album,playlist_title|Singles)s/%(title).200B.%(ext)s" \
  "<url>"
```

Use `--audio-format opus` when the user wants efficient/loss-minimizing YouTube audio. Use `--audio-format mp3` only when the user explicitly needs MP3 compatibility.

## Album or Playlist Download

Use playlist-aware output for selected album/playlist URLs:

```bash
yt-dlp \
  --extract-audio \
  --audio-format m4a \
  --embed-metadata \
  --embed-thumbnail \
  --convert-thumbnails jpg \
  --no-overwrites \
  --yes-playlist \
  -o "$HOME/Downloads/yt-dlp-music/%(playlist_title|Unknown Album)s/%(playlist_index|00)s - %(title).200B.%(ext)s" \
  "<playlist-or-album-url>"
```

If a playlist contains unrelated tracks, stop and ask before downloading the entire playlist. Prefer `--playlist-items` only when the user specifies a subset.

## Metadata and Organization

After download, inspect the resulting files:

```bash
find "$HOME/Downloads/yt-dlp-music" -maxdepth 3 -type f | sort
```

For metadata verification, use whichever tool is available:

```bash
ffprobe -hide_banner "<file>"
exiftool "<file>"
mediainfo "<file>"
```

If metadata is incomplete, report what is missing and ask before doing bulk tag edits. Do not retag files based on guessed album/track ordering.

## Troubleshooting

- `Requested format is not available`: retry with `-f bestaudio/best` or inspect formats with `yt-dlp -F "<url>"`.
- YouTube throttling or extractor errors: check `yt-dlp --version` and whether the stable release is current before changing options.
- Age-restricted or account-gated content: ask the user for the preferred cookie flow; do not use browser cookies without explicit approval.
- Duplicate filenames: keep `--no-overwrites`, inspect the target directory, and ask before replacing or renaming existing files.
- Bad search results: use `ytsearch20:` and refine with artist, album, release year, official channel, or label terms.

## Response Shape

When searching, return a compact list of candidates with title, channel, duration, and URL.

When downloading, report:

- source URL
- destination directory
- files created
- command outcome
- any missing metadata, skipped files, retries, or errors
