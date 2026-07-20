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

# Number of days for the report (default to 7 if not provided)
DAYS=${1:-7}
# Set to "--reviews" to also fetch user reviews, leave empty to skip
REVIEWS=${2:-}

echo "Step 1: Fetching data for the last $DAYS days..."
python3 fetch_data.py --days "$DAYS" $REVIEWS

echo "Step 2: Generating LLM reports..."
python3 generate_report.py

echo "Process completed successfully!"
