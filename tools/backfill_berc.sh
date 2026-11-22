#!/usr/bin/env bash
# Backfill BERC decisions from 26 Apr 2026 back to 1 Jan 2024, one folder per year, newest first.
# Safe pace: <= 0.3 requests/s shared by 2 workers, 30 min pause on any block-like failure, stop after 3.
# Stops the whole sequence as soon as one run ends early (block or expired token); rerun to resume.
# Usage: bash backfill_berc.sh <token-file> [categories]   (categories default: decision categories; "all" for every category)
TOKEN="$1"
CATS="${2:-CERERE265,INMATRIC265,AUTO_AMANARI,CERERE_HJ265}"
ROOT="${ONRC_ARTICLES_DIR:-data/berc_articles}"
LOG="${ONRC_CRAWL_LOG:-data/articles_backfill.log}"
cd "$(dirname "$0")/.." || exit 1

# Labels: day D holds publications of D+1, so each year runs from 31 Dec of the previous year to 30 Dec
for range in "2025-12-31 2026-04-26 2026" "2024-12-31 2025-12-30 2025" "2023-12-31 2024-12-30 2024"; do
  set -- $range
  echo "$(date +%T) $3: labels $1 .. $2 ($CATS)"
  ${PYTHON:-python} tools/crawlBercArticles.py --start "$1" --end "$2" --reverse --workers 2 --rate 0.3 \
    --pause-min 30 --max-trips 3 --page-size 500 --categories "$CATS" --categories-from "$ROOT/2026" \
    --out "$ROOT/$3" --token-file "$TOKEN" --log "$LOG" > /dev/null 2>&1
  if [ $? -ne 0 ]; then
    echo "$(date +%T) $3 stopped early; not continuing. See $LOG"
    exit 2
  fi
  echo "$(date +%T) $3 done"
done
echo "$(date +%T) backfill complete"
