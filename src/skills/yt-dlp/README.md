# yt-dlp

Unified audio-first yt-dlp workflow for MeTube/NAS downloads, local fallback downloads, video downloads, playlists, channels, metadata preservation, and Plex library routing.

## What It Does

1. Defaults explicit URL downloads to audio-only MeTube jobs at `https://metube.tootie.tv`.
2. Lands NAS audio downloads in `/mnt/user/data/media/yt-dlp-audio`.
3. Supports video downloads through the same `/yt-dlp --video` command.
4. Uses local `yt-dlp` for `--local`, search, inspection, debugging, or non-NAS destinations.
5. Preserves best practical quality plus metadata sidecars, thumbnails, descriptions, subtitles, and archive files.
6. Uses only the `yt-dlp` skill name; the old `yt-dlp-music` alias has been removed.

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
/yt-dlp --video <url> [url ...]
/yt-dlp --local <url> [url ...]
/yt-dlp --local --video <url> [url ...]
```

Local archive state defaults to `downloads/.archive.txt` so audio and video reruns share one skip list unless overridden.

## Files

- `SKILL.md` - agent instructions
