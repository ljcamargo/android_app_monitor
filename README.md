# Google Play Vitals Monitor & LLM Reporter

This set of scripts allows you to fetch Google Play Vitals data (ANRs, Crashes, etc.) and generate an automated report using an LLM (Gemini or local).

## Setup

1.  **Google Cloud Project**:
    *   Enable the **Google Play Developer Reporting API**.
    *   Create a **Service Account** and download the JSON key.
    *   Grant the Service Account access to your app(s) in the **Google Play Console** (Users and permissions).

2.  **Environment Variables**:
    *   Copy `.env.example` to `.env`.
    *   Fill in `GOOGLE_APPLICATION_CREDENTIALS` (path to your JSON key).
    *   Fill in `GEMINI_API_KEY` (if using Gemini).
    *   Add your app package names to `PACKAGE_NAMES` (comma-separated).

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

### Run everything (7-day report)
```bash
./weekly_report.sh
```

### Custom range
```bash
./run_reports.sh 14  # For 14 days
```

### Script details

*   `fetch_data.py`: Fetches metrics from Google Play and stores them in `data/vitals_TIMESTAMP.json`.
*   `generate_report.py`: Takes the latest JSON data, creates a Markdown report for each app using an LLM, and saves it as `data/vitals_TIMESTAMP_PACKAGE.md`.

### Using Local LLM
If you want to use a local LLM (e.g., via Ollama), set `LOCAL_LLM_COMMAND` in `.env` and run:
```bash
python3 generate_report.py --local
```
