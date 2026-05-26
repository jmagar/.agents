---
description: Download one or more YouTube URLs with yt-dlp
argument-hint: "<youtube-url> [youtube-url ...]"
allowed-tools: Bash
---

Download requested YouTube URLs immediately:

!`bash -c 'set -euo pipefail

if ! command -v yt-dlp >/dev/null 2>&1; then
  echo "yt-dlp is not installed or not on PATH." >&2
  exit 127
fi

if [ "$#" -eq 0 ]; then
  echo "Usage: /yt-dlp <youtube-url> [youtube-url ...]" >&2
  exit 2
fi

for url in "$@"; do
  case "$url" in
    https://youtube.com/*|http://youtube.com/*|https://www.youtube.com/*|http://www.youtube.com/*|https://m.youtube.com/*|http://m.youtube.com/*|https://music.youtube.com/*|http://music.youtube.com/*|https://youtu.be/*|http://youtu.be/*)
      ;;
    *)
      echo "Refusing non-YouTube URL argument: $url" >&2
      exit 2
      ;;
  esac
done

download_dir="${YT_DLP_DOWNLOAD_DIR:-$PWD/downloads/youtube}"
mkdir -p "$download_dir"

echo "Downloading to: $download_dir"
yt-dlp \
  --paths "$download_dir" \
  --output "%(upload_date>%Y-%m-%d)s-%(title).200B-%(id)s.%(ext)s" \
  --no-overwrites \
  --continue \
  -- "$@"
' yt-dlp-download $ARGUMENTS`
