---
description: Download audio from URLs with yt-dlp
argument-hint: "<url> [url ...]"
allowed-tools: Bash
---

Download requested audio URLs immediately:

!`bash -c 'set -euo pipefail

if ! command -v yt-dlp >/dev/null 2>&1; then
  echo "yt-dlp is not installed or not on PATH." >&2
  exit 127
fi

args_string="${1:-}"
if [ -z "${args_string//[[:space:]]/}" ]; then
  echo "Usage: /yt-dlp-audio <url> [url ...]" >&2
  exit 2
fi

read -r -a urls <<< "$args_string"

for url in "${urls[@]}"; do
  case "$url" in
    http://*|https://*)
      ;;
    *)
      echo "Refusing non-URL argument: $url" >&2
      exit 2
      ;;
  esac
done

download_dir="${YT_DLP_AUDIO_DOWNLOAD_DIR:-${YT_DLP_DOWNLOAD_DIR:-$PWD/downloads/yt-dlp-audio}}"
archive_file="${YT_DLP_AUDIO_ARCHIVE:-${YT_DLP_ARCHIVE:-$download_dir/.archive.txt}}"
audio_format="${YT_DLP_AUDIO_FORMAT:-m4a}"
output_template="${YT_DLP_AUDIO_OUTPUT_TEMPLATE:-%(playlist_title|singles)s/%(playlist_index|000)s-%(title).200B-%(id)s.%(ext)s}"

mkdir -p "$download_dir"

echo "Downloading audio to: $download_dir"
echo "Archive file: $archive_file"
yt-dlp \
  --extract-audio \
  --audio-format "$audio_format" \
  --paths "$download_dir" \
  --download-archive "$archive_file" \
  --output "$output_template" \
  --embed-metadata \
  --embed-thumbnail \
  --convert-thumbnails jpg \
  --write-info-json \
  --write-thumbnail \
  --restrict-filenames \
  --yes-playlist \
  --no-overwrites \
  --continue \
  -- "${urls[@]}"
' yt-dlp-audio-download "$ARGUMENTS"`
