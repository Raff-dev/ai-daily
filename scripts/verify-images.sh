#!/usr/bin/env bash
# verify-images.sh — check every card-image URL in a briefing returns HTTP 200.
#
# Why this exists:
#   Briefs link to external image hosts (TechCrunch, BMW press, CNBC, etc.).
#   Those URLs go stale, get re-pathed, or 403 to non-browser clients.
#   The runtime onerror handler hides broken images, but the user still sees
#   a flash of nothing — and on social previews they see a broken thumbnail.
#   This script lets the editor agent catch all of that before saving.
#
# Usage:
#   bash scripts/verify-images.sh path/to/ai-daily-YYYY-MM-DD.html
#
# Exit codes:
#   0 — every image URL returns HTTP 200
#   1 — at least one URL failed; replace it (use the fallback chain in
#       agents/editor.md) and re-run
#   2 — argument missing or file not found
#
# No dependencies beyond bash, grep, sed and curl — all standard on macOS
# and Linux. No Python, no Node, no npm install.

set -u  # fail on unset variables; we do NOT use -e because curl failures
        # are expected and we handle them per-line.

file="${1:-}"

if [[ -z "$file" ]]; then
  echo "usage: bash scripts/verify-images.sh <path-to-brief.html>" >&2
  exit 2
fi

if [[ ! -f "$file" ]]; then
  echo "error: file not found: $file" >&2
  exit 2
fi

# Pull every src= URL that's tagged class="card-image" (the brief's hero
# image per card). Decode the HTML entity &amp; back to & so curl gets a
# clean URL.
urls=$(
  grep -oE 'class="card-image" src="[^"]+"' "$file" \
    | sed -E 's/class="card-image" src="//' \
    | sed 's/"$//' \
    | sed 's/&amp;/\&/g'
)

if [[ -z "$urls" ]]; then
  echo "no card-image URLs found in $file — nothing to check"
  exit 0
fi

# Pretend to be a real browser. Some CDNs 403 generic User-Agent strings,
# which would produce false negatives.
ua="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"

total=0
failed=0

while IFS= read -r url; do
  total=$((total + 1))
  http=$(curl -sIL -A "$ua" -o /dev/null -w "%{http_code}" --max-time 10 "$url" 2>/dev/null || echo "ERR")
  if [[ "$http" == "200" ]]; then
    printf 'OK   %s  %s\n' "$http" "$url"
  else
    printf 'FAIL %s  %s\n' "$http" "$url"
    failed=$((failed + 1))
  fi
done <<< "$urls"

echo "---"
echo "checked: $total"
echo "failed:  $failed"

if (( failed > 0 )); then
  echo
  echo "Fix the failed URLs using the fallback chain in agents/editor.md:" >&2
  echo "  1. og:image / twitter:image from the primary source" >&2
  echo "  2. Microlink API as a proxy" >&2
  echo "  3. Body image scan (first hero <img> in the article)" >&2
  echo "  4. Alternative outlet covering the same story" >&2
  echo "  5. Drop the <img> entirely (and remove has-image from the wrapper)" >&2
  exit 1
fi

exit 0
