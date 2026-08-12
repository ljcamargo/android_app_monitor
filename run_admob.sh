#!/bin/bash
# AdMob monitoring wrapper (standalone — does not touch the vitals scripts).
#
# First-time setup (AdMob uses user OAuth, not service accounts):
#   python3 admob_oauth_setup.py --client-json <your_oauth_client.json>
# and paste the printed ADMOB_REFRESH_TOKEN into .env.
#
# Usage:
#   ./run_admob.sh [days] [extra-flags]
#   ./run_admob.sh 7                       # 7-day fetch + LLM report
#   ./run_admob.sh 7 --discover            # auto-discover apps & ad units
#   ./run_admob.sh 7 --ad-units-config admob_ad_units.json
#   ./run_admob.sh 7 --fetch-only          # only save JSON
set -e

if [ ! -f .env ]; then
    echo "Error: .env not found. Copy .env.example to .env and fill in credentials."
    exit 1
fi

DAYS=${1:-7}
EXTRA=${2:-}

python3 fetch_admob.py --days "$DAYS" $EXTRA
