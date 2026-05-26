---
description: View the latest screenshot from ~/Pictures/Screenshots
argument-hint: [optional: question about the screenshot]
allowed-tools: Read, Bash(ls:*, echo:*)
---

Latest screenshot: !`echo "$HOME/Pictures/Screenshots/$(ls -t "$HOME/Pictures/Screenshots/" | head -1)"`

Read and describe the image at that path. If the user provided additional instructions in the command arguments, apply them (e.g. "what's in the top right corner", "extract the text", "what error is shown").
