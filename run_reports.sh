#!/bin/bash

# Exit on error
set -e

# Load environment variables
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        echo ".env file not found, creating from .env.example. Please edit it with your credentials."
        cp .env.example .env
        exit 1
    else
        echo "Error: .env file and .env.example not found."
        exit 1
    fi
fi

# Usage:
#   ./run_reports.sh [days] [extra-flags]
#   ./run_reports.sh 7 --reviews         # vitals + reviews
#   ./run_reports.sh 7 --reviews-only    # reviews only (ignores days)
#   ./run_reports.sh 7 --reviews-count 20
DAYS=${1:-7}
EXTRA=${2:-}

echo "Step 1: Fetching data..."
python3 fetch_data.py --days "$DAYS" $EXTRA

echo "Step 2: Generating LLM reports..."
python3 generate_report.py

echo "Process completed successfully!"
