#!/bin/bash
# check-line-counts.sh - Verify function line counts are under limit
# Usage: ./scripts/check-line-counts.sh [file] [function] [max_lines]
# Example: ./scripts/check-line-counts.sh src/services/docker.ts execContainer 50

set -e

FILE=${1:-""}
FUNC=${2:-""}
MAX=${3:-50}

if [ -z "$FILE" ] || [ -z "$FUNC" ]; then
  echo "Usage: $0 <file> <function_name> [max_lines]"
  echo "Example: $0 src/services/docker.ts execContainer 50"
  exit 1
fi

if [ ! -f "$FILE" ]; then
  echo "ERROR: File not found: $FILE"
  exit 1
fi

echo "=== Line Count Check ==="
echo "File: $FILE"
echo "Function: $FUNC"
echo "Max allowed: $MAX lines"
echo ""

# Find function start line
START=$(grep -n "async ${FUNC}\|function ${FUNC}\|${FUNC} = \|${FUNC}(" "$FILE" | grep -v "test\|describe\|it(" | head -1 | cut -d: -f1)

if [ -z "$START" ]; then
  echo "ERROR: Function '$FUNC' not found in $FILE"
  exit 1
fi

echo "Found at line: $START"

# Count braces to find function end
# This is a simplified approach - for complex cases, use a proper parser
TOTAL_LINES=$(wc -l < "$FILE")
BRACE_COUNT=0
FOUND_OPEN=0
END=$START

for ((i=START; i<=TOTAL_LINES; i++)); do
  LINE=$(sed -n "${i}p" "$FILE")

  # Count opening and closing braces
  OPENS=$(echo "$LINE" | tr -cd '{' | wc -c)
  CLOSES=$(echo "$LINE" | tr -cd '}' | wc -c)

  if [ "$OPENS" -gt 0 ]; then
    FOUND_OPEN=1
  fi

  BRACE_COUNT=$((BRACE_COUNT + OPENS - CLOSES))

  if [ "$FOUND_OPEN" -eq 1 ] && [ "$BRACE_COUNT" -eq 0 ]; then
    END=$i
    break
  fi
done

LINES=$((END - START + 1))

echo "End at line: $END"
echo "Line count: $LINES"
echo ""

if [ "$LINES" -gt "$MAX" ]; then
  echo "LIMIT EXCEEDED!"
  echo "Function: $FUNC"
  echo "Lines: $LINES (limit: $MAX)"
  echo "Over by: $((LINES - MAX)) lines"
  exit 1
else
  echo "WITHIN LIMIT"
  echo "Function: $FUNC"
  echo "Lines: $LINES (limit: $MAX)"
  echo "Remaining: $((MAX - LINES)) lines"
  exit 0
fi
