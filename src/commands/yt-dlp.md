---
description: Download audio, videos, or playlists with yt-dlp/MeTube
argument-hint: "[--video] [--local|--nas] <url> [url ...]"
allowed-tools: Bash
---

Download requested media immediately. Default is audio-only through NAS/MeTube; use `--video` for video and `--local` to run local `yt-dlp`.

!`bash -c 'set -euo pipefail

args_string="${1:-}"
if [ -z "${args_string//[[:space:]]/}" ]; then
  echo "Usage: /yt-dlp [--video|--audio] [--local|--nas] <url> [url ...]" >&2
  exit 2
fi

read -r -a tokens <<< "$args_string"

mode="audio"
route="nas"
urls=()

for token in "${tokens[@]}"; do
  case "$token" in
    --audio|-a)
      mode="audio"
      ;;
    --video|-v)
      mode="video"
      ;;
    --local)
      route="local"
      ;;
    --nas|--metube)
      route="nas"
      ;;
    --help|-h)
      echo "Usage: /yt-dlp [--video|--audio] [--local|--nas] <url> [url ...]"
      exit 0
      ;;
    http://*|https://*)
      urls+=("$token")
      ;;
    *)
      echo "Refusing unknown argument: $token" >&2
      exit 2
      ;;
  esac
done

if [ "${#urls[@]}" -eq 0 ]; then
  echo "No URLs provided." >&2
  exit 2
fi

if [ "$route" = "nas" ]; then
  if ! command -v curl >/dev/null 2>&1; then
    echo "curl is not installed or not on PATH." >&2
    exit 127
  fi

  metube_url="${METUBE_URL:-https://metube.tootie.tv}"
  quality="${METUBE_QUALITY:-best}"
  format="${METUBE_FORMAT:-any}"
  folder="${METUBE_FOLDER:-}"

  if [ "$mode" = "audio" ]; then
    quality="audio"
    format="${METUBE_AUDIO_FORMAT:-m4a}"
    folder="${METUBE_AUDIO_FOLDER:-}"
  fi

  echo "Submitting to MeTube: $metube_url"
  echo "Mode: $mode"
  for url in "${urls[@]}"; do
    python3 - "$url" "$quality" "$format" "$folder" <<'"'"'PY'"'"' | curl -fsS -X POST "$metube_url/add" -H "Content-Type: application/json" --data-binary @-
import json
import sys

url, quality, fmt, folder = sys.argv[1:5]
payload = {
    "url": url,
    "quality": quality,
    "format": fmt,
    "folder": folder or None,
    "playlist_strict_mode": False,
    "auto_start": True,
}
print(json.dumps(payload))
PY
    echo
  done
  exit 0
fi

if ! command -v yt-dlp >/dev/null 2>&1; then
  echo "yt-dlp is not installed or not on PATH." >&2
  exit 127
fi

if [ "$mode" = "audio" ]; then
  download_dir="${YT_DLP_AUDIO_DOWNLOAD_DIR:-${YT_DLP_DOWNLOAD_DIR:-$PWD/downloads/yt-dlp-audio}}"
  archive_file="${YT_DLP_AUDIO_ARCHIVE:-${YT_DLP_ARCHIVE:-$PWD/downloads/.archive.txt}}"
  audio_format="${YT_DLP_AUDIO_FORMAT:-m4a}"
  output_template="${YT_DLP_AUDIO_OUTPUT_TEMPLATE:-%(playlist_title|singles)s/%(playlist_index|000)s-%(title).200B-%(id)s.%(ext)s}"

  mkdir -p "$download_dir"
  mkdir -p "$(dirname "$archive_file")"
  echo "Downloading local audio to: $download_dir"
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
    --write-description \
    --restrict-filenames \
    --yes-playlist \
    --no-overwrites \
    --continue \
    -- "${urls[@]}"
else
  download_dir="${YT_DLP_DOWNLOAD_DIR:-$PWD/downloads/yt-dlp}"
  archive_file="${YT_DLP_ARCHIVE:-$PWD/downloads/.archive.txt}"
  format_selector="${YT_DLP_FORMAT:-bestvideo*+bestaudio/best}"
  output_template="${YT_DLP_OUTPUT_TEMPLATE:-%(playlist_title|single)s/%(playlist_index|000)s-%(upload_date>%Y-%m-%d)s-%(title).200B-%(id)s.%(ext)s}"

  mkdir -p "$download_dir"
  mkdir -p "$(dirname "$archive_file")"
  echo "Downloading local video to: $download_dir"
  echo "Archive file: $archive_file"
  yt-dlp \
    --format "$format_selector" \
    --paths "$download_dir" \
    --download-archive "$archive_file" \
    --output "$output_template" \
    --embed-metadata \
    --embed-thumbnail \
    --convert-thumbnails jpg \
    --write-info-json \
    --write-thumbnail \
    --write-description \
    --write-subs \
    --write-auto-subs \
    --sub-langs "all,-live_chat" \
    --embed-subs \
    --restrict-filenames \
    --yes-playlist \
    --no-overwrites \
    --continue \
    --merge-output-format mkv \
    -- "${urls[@]}"
fi
' yt-dlp-download "$ARGUMENTS"`
