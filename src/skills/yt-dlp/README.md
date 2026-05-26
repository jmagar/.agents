# yt-dlp

Unified yt-dlp workflow for MeTube/NAS downloads, local fallback downloads, audio extraction, playlists, channels, metadata preservation, and Plex library routing.

## What It Does

1. Defaults explicit URL downloads to MeTube at `https://metube.tootie.tv`.
2. Lands NAS video downloads in `/mnt/user/data/media/yt-dlp`, which Plex sees as the `yt-dlp` library.
3. Supports audio-only downloads through the same `/yt-dlp --audio` command.
4. Uses local `yt-dlp` for `--local`, search, inspection, debugging, or non-NAS destinations.
5. Preserves best practical quality plus metadata sidecars, thumbnails, descriptions, subtitles, and archive files.
6. Keeps the old `yt-dlp-music` name as a compatibility alias only.

## Invoke

Triggers include:

- "download this with yt-dlp"
- "download this YouTube playlist"
- "send this to MeTube"
- "download audio from this URL"
- "rip this playlist"
- "archive this channel"
- "what sites does yt-dlp support?"

## Slash Command

```text
/yt-dlp <url> [url ...]
/yt-dlp --audio <url> [url ...]
/yt-dlp --local <url> [url ...]
/yt-dlp --local --audio <url> [url ...]
```

## Files

- `SKILL.md` - agent instructions
