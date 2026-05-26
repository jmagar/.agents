---
description: Download audio, videos, both, or playlists with yt-dlp/MeTube
argument-hint: "[--audio|--video|--both] [--local|--nas] <url> [url ...]"
allowed-tools: Bash
---

Download requested media immediately. Default is audio-only through NAS/MeTube; use `--video` for video, `--both` for audio and video, and `--local` to run local `yt-dlp`.

!`bash -c 'set -euo pipefail

args_string="${1:-}"
if [ -z "${args_string//[[:space:]]/}" ]; then
  echo "Usage: /yt-dlp [--audio|--video|--both] [--local|--nas] <url> [url ...]" >&2
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
    --both|-b)
      mode="both"
      ;;
    --local)
      route="local"
      ;;
    --nas|--metube)
      route="nas"
      ;;
    --help|-h)
      echo "Usage: /yt-dlp [--audio|--video|--both] [--local|--nas] <url> [url ...]"
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
  if [ "$mode" = "both" ] && [ "${METUBE_BOTH_ROUTE:-direct}" = "direct" ]; then
    if ! command -v ssh >/dev/null 2>&1; then
      echo "ssh is required for NAS --both direct downloads." >&2
      exit 127
    fi

    nas_host="${YT_DLP_NAS_HOST:-tootie}"
    container="${METUBE_CONTAINER:-metube}"
    audio_archive="${METUBE_AUDIO_ARCHIVE:-/config/state/download-archive-audio.txt}"
    video_archive="${METUBE_VIDEO_ARCHIVE:-/config/state/download-archive-video.txt}"
    audio_format="${METUBE_AUDIO_FORMAT:-m4a}"
    video_format="${METUBE_FORMAT_SELECTOR:-${YT_DLP_FORMAT:-bestvideo*+bestaudio/best}}"
    audio_template="${METUBE_AUDIO_OUTPUT_TEMPLATE:-%(playlist_title|singles)s/%(playlist_index|000)s-%(title).200B-%(id)s.%(ext)s}"
    video_template="${METUBE_OUTPUT_TEMPLATE:-%(playlist_title|single)s/%(playlist_index|000)s-%(upload_date>%Y-%m-%d)s-%(title).200B-%(id)s.%(ext)s}"

    run_remote() {
      remote_cmd=$(printf "%q " "$@")
      ssh -o BatchMode=yes "$nas_host" "$remote_cmd"
    }

    echo "Downloading NAS audio and video through $nas_host/$container"
    echo "Audio archive: $audio_archive"
    run_remote docker exec "$container" yt-dlp \
      --extract-audio \
      --audio-format "$audio_format" \
      --paths /audio \
      --download-archive "$audio_archive" \
      --output "$audio_template" \
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

    echo "Video archive: $video_archive"
    run_remote docker exec "$container" yt-dlp \
      --format "$video_format" \
      --paths /downloads \
      --download-archive "$video_archive" \
      --output "$video_template" \
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
    exit 0
  fi

  if ! command -v curl >/dev/null 2>&1; then
    echo "curl is not installed or not on PATH." >&2
    exit 127
  fi

  metube_url="${METUBE_URL:-https://metube.tootie.tv}"
  submit_metube_job() {
    job_mode="$1"
    url="$2"

    quality="${METUBE_QUALITY:-best}"
    format="${METUBE_FORMAT:-any}"
    folder="${METUBE_FOLDER:-}"

    if [ "$job_mode" = "audio" ]; then
      quality="audio"
      format="${METUBE_AUDIO_FORMAT:-m4a}"
      folder="${METUBE_AUDIO_FOLDER:-}"
    fi

    echo "Submitting $job_mode: $url"
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
  }

  echo "Submitting to MeTube: $metube_url"
  echo "Mode: $mode"
  for url in "${urls[@]}"; do
    if [ "$mode" = "both" ]; then
      submit_metube_job audio "$url"
      submit_metube_job video "$url"
    else
      submit_metube_job "$mode" "$url"
    fi
  done
  exit 0
fi

if ! command -v yt-dlp >/dev/null 2>&1; then
  echo "yt-dlp is not installed or not on PATH." >&2
  exit 127
fi

download_audio() {
  download_dir="${YT_DLP_AUDIO_DOWNLOAD_DIR:-${YT_DLP_DOWNLOAD_DIR:-$PWD/downloads/yt-dlp-audio}}"
  archive_default="$PWD/downloads/.archive.txt"
  if [ "$mode" = "both" ]; then
    archive_default="$PWD/downloads/.archive-audio.txt"
  fi
  archive_file="${YT_DLP_AUDIO_ARCHIVE:-${YT_DLP_ARCHIVE:-$archive_default}}"
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
}

download_video() {
  download_dir="${YT_DLP_DOWNLOAD_DIR:-$PWD/downloads/yt-dlp}"
  archive_default="$PWD/downloads/.archive.txt"
  if [ "$mode" = "both" ]; then
    archive_default="$PWD/downloads/.archive-video.txt"
  fi
  archive_file="${YT_DLP_VIDEO_ARCHIVE:-${YT_DLP_ARCHIVE:-$archive_default}}"
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
}

case "$mode" in
  audio)
    download_audio
    ;;
  video)
    download_video
    ;;
  both)
    download_audio
    download_video
    ;;
esac
' yt-dlp-download "$ARGUMENTS"`
