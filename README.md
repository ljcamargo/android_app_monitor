# Google Play Vitals Monitor & LLM Reporter

**Turn Google Play Vitals into actionable insights — automatically.**

This tool pulls your apps' stability and performance data (ANRs, crashes, slow starts, background wakelocks) plus the latest user reviews from the Google Play APIs, then uses an LLM (Google Gemini, or any local model) to write a plain-language report with trends and concrete recommendations — no dashboard digging required.

## ✨ Highlights

- 📊 **One command, full summary** — a single `./weekly_report.sh` fetches all the data and produces an AI-written Markdown report per app.
- 🧠 **Vitals + user reviews in one report** — the AI correlates crash spikes with what users are actually complaining about.
- 💰 **AdMob monetization monitoring** — a standalone script tracks impressions, clicks, earnings, eCPM and fill rates per ad unit, with its own AI report (user-OAuth based).
- 🔀 **Flexible timeframes** — daily, weekly, or custom windows; reviews can be fetched as "latest N" or time-bounded.
- 🔒 **No secrets stored** — credentials live in your local `.env`; nothing is committed.
- 🧩 **Extensible** — designed so new data sources (ratings, subscriptions, etc.) can be added cleanly.

## 🚀 Quick demo

Once configured (see [Setup Guide](#setup-guide)), a single run gives you everything:

```bash
./weekly_report.sh --reviews
```

That one command: fetches 7 days of vitals + the latest user reviews for every app in your account, then generates a report like this per app:

```markdown
# App Vitals & User Review Report: `com.example.app`

- Crash rate: 0% across the whole period ✅
- ANR spikes on Aug 4–5 (0.01%–0.0115%) — single-user, persistent issue
- Cold start 3%–8% — main optimization opportunity
- User feedback: "too many ads" (1★) posted same day as an ANR spike → ad-loading may be blocking startup

**Top recommendations:**
1. Move non-critical init tasks off the main thread
2. Delay ad loading until after first frame
3. Investigate ANR correlation with launch sequence
```

Full sample output: [`examples/example_report.md`](examples/example_report.md) · Data structure: [`examples/example_data.json`](examples/example_data.json)

---

## Table of Contents

- [How It Works](#how-it-works)
- [Prerequisites](#prerequisites)
- [Setup Guide](#setup-guide)
  - [1. Google Cloud Project & Service Account](#1-google-cloud-project--service-account)
  - [2. Grant Play Console Access](#2-grant-play-console-access)
  - [3. Environment Variables](#3-environment-variables)
  - [4. Install Dependencies](#4-install-dependencies)
- [Usage](#usage)
  - [Quick Start](#quick-start)
  - [Custom Time Ranges](#custom-time-ranges)
  - [Including User Reviews](#including-user-reviews)
  - [Reviews Only (skip vitals entirely)](#reviews-only-skip-vitals-entirely)
  - [Using a Local LLM](#using-a-local-llm)
  - [Manual Invocation](#manual-invocation)
- [Examples](#examples)
- [User Reviews Feature (Optional)](#user-reviews-feature-optional)
- [AdMob Monitoring (Optional)](#admob-monitoring-optional)
  - [AdMob OAuth Setup](#admob-oauth-setup)
  - [AdMob Usage](#admob-usage)
  - [AdMob Ad Units Configuration](#admob-ad-units-configuration)
- [Output](#output)
- [Architecture & Extending](#architecture--extending)
  - [Current Structure](#current-structure)
  - [Planned Refactoring for New Data Sources](#planned-refactoring-for-new-data-sources)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## How It Works

The system is composed of two independent scripts orchestrated by a shell helper:

1. **`fetch_data.py`** — Queries the [Google Play Developer Reporting API](https://developers.google.com/play/developer/reporting/overview) for each of your apps and stores the raw metrics in a JSON file under `data/`.

2. **`generate_report.py`** — Reads the latest JSON data, formats it into a prompt, and sends it to an LLM (Gemini by default) to generate a Markdown report per app.

```
                     ┌──────────────────────┐
                     │ Google Play API      │
                     │ (Developer Reporting)│
                     └──────────┬───────────┘
                                │ daily vitals
                                ▼
                     ┌──────────────────────┐
                     │   fetch_data.py      │
                     │ → data/vitals_*.json │
                     └──────────┬───────────┘
                                │ JSON data
                                ▼
                     ┌──────────────────────┐
                     │  generate_report.py  │
                     │ (Gemini / local LLM) │
                     └──────────┬───────────┘
                                │ .md report per app
                                ▼
                     ┌──────────────────────┐
                     │ data/vitals_*_app.md │
                     └──────────────────────┘
```

---

## Prerequisites

Before using this tool you need:

- **A Google Play Developer account** with at least one published app.
- **A Google Cloud project** with the Play Developer Reporting API enabled.
- **A service account** (JSON key) with access to your Play Console data.
- **Python 3.9+** installed.
- **A Gemini API key** (free tier available at [aistudio.google.com](https://aistudio.google.com)) — or a local LLM like Ollama.

---

## Setup Guide

### 1. Google Cloud Project & Service Account

This is the most important step. Follow it carefully.

#### 1.1 Create or select a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Click the project dropdown at the top and select **New Project** (or choose an existing one).
3. Give it a name (e.g., `play-vitals-monitor`) and click **Create**.

#### 1.2 Enable the Play Developer Reporting API

1. In your project, go to **APIs & Services > Library**.
2. Search for **Google Play Developer Reporting API**.
3. Click **Enable**.

#### 1.3 Create a Service Account

1. Go to **APIs & Services > Credentials**.
2. Click **+ Create Credentials > Service Account**.
3. Give it a name (e.g., `play-vitals-reader`).
4. Click **Done** (skip granting roles for now — access is granted in Play Console).

#### 1.4 Generate a JSON Key

1. In the **Service Accounts** list, click on the account you just created.
2. Go to the **Keys** tab.
3. Click **Add Key > Create New Key**.
4. Choose **JSON** and click **Create**.
5. A `.json` file will be downloaded automatically — **keep this file safe**.

> **Where to place the file:**
> Place the downloaded JSON key file in the root of this project directory:
> ```
> <project_root>/service_account.json
> ```
> The default `.env.example` expects the file to be named `service_account.json` in the project root. You can use a different path by updating `GOOGLE_APPLICATION_CREDENTIALS` in `.env`.

### 2. Grant Play Console Access

The service account must be granted access to your apps inside the Google Play Console.

1. Go to the [Google Play Console](https://play.google.com/console/).
2. Navigate to **Users and permissions** (under Settings).
3. Click **Invite new user**.
4. Enter the **service account email** (it looks like `play-vitals-reader@your-project.iam.gserviceaccount.com`).
5. Under **App permissions**, select all apps you want to monitor.
6. Under **Account permissions**, grant at least:
   - **View app data (read-only)** — this allows reading vitals data.
7. Click **Invite**.

> It may take a few minutes for the permissions to propagate.

### 3. Environment Variables

Copy the example configuration and edit it:

```bash
cp .env.example .env
```

Edit `.env` with your values:

```ini
# Path to your service account JSON key file
GOOGLE_APPLICATION_CREDENTIALS=service_account.json

# Your LLM API key (Gemini)
GEMINI_API_KEY=AIzaSyYourActualKeyHere

# Comma-separated list of package names to monitor (find these in Play Console)
PACKAGE_NAMES=com.example.app1,com.example.app2,com.example.app3

# Optional: Local LLM command (if not using Gemini)
# LOCAL_LLM_COMMAND="ollama run llama3"
```

#### Where to find your package names:

- Open the [Google Play Console](https://play.google.com/console/).
- Go to **All apps** — each app's package name is listed under its icon (e.g., `com.example.transit`).
- You can also find it in the URL when viewing an app: `https://play.google.com/console/developers/.../app/com.example.transit/...`

#### Where to get a Gemini API key:

1. Go to [Google AI Studio](https://aistudio.google.com/).
2. Click **Get API Key**.
3. Create a new API key (free tier includes generous limits).
4. Copy the key into `GEMINI_API_KEY` in your `.env` file.

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

It's recommended to use a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## Usage

### Quick Start

```bash
./weekly_report.sh
```

This runs a 7-day report: fetch data, then generate LLM summaries.

### Custom Time Ranges

```bash
./run_reports.sh 14   # Last 14 days
./run_reports.sh 30   # Last 30 days
./run_reports.sh 1    # Last 1 day (latest available)
```

### Including User Reviews

```bash
./weekly_report.sh --reviews        # 7-day vitals + 7-day reviews (default)
./run_reports.sh 14 --reviews       # 14-day vitals + 14-day reviews
./run_reports.sh 7 --reviews-count 20  # 20 latest reviews per app, no time filter
./run_reports.sh 7 --reviews --reviews-days 30  # 7-day vitals + 30-day reviews
```

By default, when `--reviews` is used with vitals, reviews are filtered to the **same timeframe** as vitals (`--days`). Use `--reviews-days` to set an independent timeframe. Set `--reviews-days 0` to fetch the latest N reviews without time filtering.

### Reviews Only (skip vitals entirely)

```bash
./run_reports.sh --reviews-only                # Latest 50 reviews, no time filter
./run_reports.sh --reviews-only --reviews-days 7  # Reviews from last 7 days only

# Or directly, with more control:
python3 fetch_data.py --reviews-only --reviews-count 30 --reviews-days 14
python3 generate_report.py
```

When run in `--reviews-only` mode, the script only queries the Android Publisher API for user reviews, ignoring vitals entirely. The resulting data file is named `reviews_TIMESTAMP.json` instead of `vitals_TIMESTAMP.json`. The LLM report will contain a dedicated **User Reviews Summary** section.

### Using a Local LLM

If you prefer a local model (e.g., via Ollama), set the `LOCAL_LLM_COMMAND` in `.env`:

```ini
LOCAL_LLM_COMMAND="ollama run llama3"
```

Then run:

```bash
python3 generate_report.py --local
```

### Manual Invocation

Fetch data only:

```bash
python3 fetch_data.py --days 7
```

Generate reports from an existing data file:

```bash
# Use the latest data file
python3 generate_report.py

# Use a specific data file
python3 generate_report.py --file data/vitals_20260511_164757.json
```

---

## Examples

Sanitized example outputs are provided in the [`examples/`](examples/) directory to help you understand what the tool produces:

| File | Description |
|---|---|
| [`examples/example_report.md`](examples/example_report.md) | A sample AI-generated report (vitals + user reviews) with app names and user identities redacted |
| [`examples/example_data.json`](examples/example_data.json) | A synthetic sample of the JSON data structure produced by `fetch_data.py`, with fictional values |
| [`examples/example_admob_report.md`](examples/example_admob_report.md) | A sample AI-generated AdMob monetization report, with IDs and figures fictionalized |
| [`examples/example_admob_data.json`](examples/example_admob_data.json) | A synthetic sample of the JSON produced by `fetch_admob.py`, with fictional values |

> **Privacy note:** The examples are sanitized — app package names, user names, and metrics are fictional or redacted. Your real reports are stored locally in `data/`, which is gitignored and never committed.

---

## User Reviews Feature (Optional)

This tool can optionally fetch the latest user reviews from Google Play and include them in the AI report for a richer analysis that correlates user sentiment with app vitals.

### How it works

When `--reviews` is passed, `fetch_data.py` calls the **Google Play Android Publisher API** (`reviews.list`) to retrieve the most recent user reviews for each app.

The reviews are stored alongside vitals in the same JSON file under a `"reviews"` key. When `generate_report.py` runs, the LLM prompt is extended to ask the AI to:

- Provide a **dedicated `## User Reviews Summary` section** in the report with key themes and notable quotes
- Identify common praises and complaints
- Note sentiment trends (positive, negative, mixed)
- Correlate user feedback with vitals spikes where possible
- Suggest specific improvements based on actual user comments

The dedicated section ensures reviews are always visible in the output, even when the AI also integrates them into other parts of the report.

### Reviews-only mode

Use `--reviews-only` to fetch and analyze reviews without querying vitals at all. This is useful for quick check-ins or when you only care about user sentiment.

```bash
python3 fetch_data.py --reviews-only --reviews-count 30
python3 generate_report.py
```

The output file is named `reviews_TIMESTAMP.json` to distinguish it from combined data files.

### Usage

```bash
# Full pipeline with reviews (default 50 latest)
./weekly_report.sh --reviews

# Fetch vitals + latest 20 reviews
python3 fetch_data.py --days 7 --reviews --reviews-count 20
```

### Required Permissions

The service account needs the **`androidpublisher`** API scope. This is covered by the **"View app data (read-only)"** permission already granted in the Play Console (step 2 of Setup). No additional API enablement is required beyond what's already done for vitals.

### Notes

- Max `--reviews-count` is **100** (API limit per page).
- If `--reviews` is not passed, the report is generated from vitals only.
- The reviews API requires the service account to have the `androidpublisher` scope, which is separate from the `playdeveloperreporting` scope used for vitals.

---

## AdMob Monitoring (Optional)

A standalone script, [`fetch_admob.py`](fetch_admob.py), monitors your ad monetization: impressions, clicks, earnings, eCPM, match rate and more — per app and per ad unit — and generates an AI-written monetization report with actionable recommendations (e.g., low fill rates, underperforming ad units, placement suggestions).

It is fully independent from the vitals/reviews scripts (no shared code, no shared config beyond the same `.env` file).

### Why AdMob needs its own auth (important)

**AdMob does NOT support service accounts.** Unlike the Play Developer Reporting and Android Publisher APIs (which work with your `service_account.json`), the AdMob API requires **user-based OAuth 2.0**: a real Google Account with access to your AdMob account must authorize the tool once, generating a long-lived **refresh token** that the script reuses automatically.

### AdMob OAuth Setup

Follow these steps once. They are fiddly — read all of them before starting.

#### 1. Enable the AdMob API

1. In [Google Cloud Console](https://console.cloud.google.com/), select your project.
2. Go to **APIs & Services > Library** and enable the **Google AdMob API** (`admob.googleapis.com`).

#### 2. Create the OAuth consent screen (first time only)

> This is the step most people trip on. You must configure a consent screen even though this is a personal tool.

1. Go to **APIs & Services > OAuth consent screen**.
2. Choose **External** user type (required for any app using OAuth with a personal Google account; **Internal** is only available for Google Workspace organizations).
3. Fill in the required fields: app name, support email, and developer contact email.
4. **Add yourself as a test user** — see the caveat below.
5. Save.

**The tester caveat (critical):**

- Unless your project is submitted for **Google verification** (which requires logos, privacy policy, review, and is meant for public apps), the consent screen is in **"Testing"** mode. In testing mode, **only accounts you explicitly list as test users** can authorize.
- You are the owner of the AdMob account, the Cloud project, *and* the Google account — but that is **not enough**. You must **manually add your own email address to the test users list** in the OAuth consent screen, or the authorization will fail with an `access_denied` / "app not verified" error.
- Add your email under **Audience > Test users > Add users**, then save.

#### 3. Create an OAuth client ID

1. Go to **APIs & Services > Credentials > Create Credentials > OAuth client ID**.
2. Choose **Desktop app** as the application type (simplest for a local script — no redirect URIs needed).
3. Click **Create**, then **Download JSON**. Save it somewhere you can reference (e.g., `admob_oauth_client.json` in the project root).

#### 4. Invite your Google account in AdMob

1. Go to [apps.admob.com](https://apps.admob.com) > **Settings > Users**.
2. Click **Add user** and enter the email of the Google account you will authorize with (the same one you added as a test user).
3. Choose a role (e.g., "Read only" — this tool only reads).
4. Accept the invite from that email account.

#### 5. Generate the refresh token

```bash
python3 admob_oauth_setup.py --client-json admob_oauth_client.json
```

A browser opens → log in with the invited Google account → accept the consent. The script prints:

```
ADMOB_REFRESH_TOKEN=1//xxxx
ADMOB_CLIENT_ID=xxxx.apps.googleusercontent.com
ADMOB_CLIENT_SECRET=xxxx
```

**Add these keys manually to your `.env` file.** The script does not modify `.env` for you — copy the three lines into it yourself (see `.env.example` for the layout).

> **Heads-up:** For unverified (testing-mode) apps, Google may revoke refresh tokens that go unused for ~6 months, or when the test user list changes. If you later hit an `invalid_grant` / 401 error, just re-run this step.

### AdMob Usage

```bash
# Quick start: auto-discover apps & ad units, 7-day report + LLM summary
./run_admob.sh 7 --discover

# Fetch only (no LLM)
python3 fetch_admob.py --days 7 --discover --fetch-only

# LLM report from an existing JSON file
python3 fetch_admob.py --file data/admob_20260812_*.json

# Restrict to specific apps
python3 fetch_admob.py --days 7 --discover --packages com.example.app1,com.example.app2

# Use a local LLM instead of Gemini
python3 fetch_admob.py --days 7 --discover --local
```

Notes:
- The script **auto-discovers** all linked apps and ad units via the API (`--discover`), so you don't need to declare them.
- Report period is limited to **31 days** per request (API constraint). For longer periods, run in chunks.
- Money is reported in USD by default (`--currency` or `ADMOB_CURRENCY` to change). Ratios (CTR, match rate) are 0–1 (1.0 = 100%).

### AdMob Ad Units Configuration

Auto-discovery covers most cases. If you prefer to declare ad units explicitly (or restrict the report to specific units), create a JSON file like [`admob_ad_units.example.json`](admob_ad_units.example.json):

```json
{
  "com.example.app": [
    "ca-app-pub-1234567890123456/1234567890"
  ]
}
```

Then run:

```bash
python3 fetch_admob.py --days 7 --ad-units-config admob_ad_units.json
```

Declared ad unit IDs are validated against the API — a typo raises a clear error listing the available units.

### AdMob Metrics captured

Per day, per ad unit: `AD_REQUESTS`, `MATCHED_REQUESTS`, `IMPRESSIONS`, `CLICKS`, `ESTIMATED_EARNINGS`, `IMPRESSION_CTR`, `IMPRESSION_RPM` (eCPM), `MATCH_RATE`, `SHOW_RATE`, plus per-ad-unit and per-app totals (CTR, eCPM, match rate).

---

## Output

All output goes to the `data/` directory.

| File Pattern | Contents |
|---|---|
| `data/vitals_YYYYMMDD_HHMMSS.json` | Raw API response data for all apps, structured per metric |
| `data/vitals_YYYYMMDD_HHMMSS_com_example_app1.md` | AI-generated Markdown report for one app |
| `data/vitals_YYYYMMDD_HHMMSS_com_example_app2.md` | AI-generated Markdown report for another app |
| `data/reviews_YYYYMMDD_HHMMSS.json` | User reviews data (from `--reviews-only` mode) |
| `data/admob_YYYYMMDD_HHMMSS.json` | AdMob monetization data per app / ad unit (from `fetch_admob.py`) |
| `data/admob_YYYYMMDD_HHMMSS_com_example_app1.md` | AI-generated AdMob monetization report for one app |

### JSON data structure

```json
{
  "com.example.app1": {
    "package_name": "com.example.app1",
    "metrics": {
      "anrRate": {
        "rows": [
          {
            "startTime": {"year": 2026, "month": 5, "day": 5},
            "metrics": [
              {"decimalValue": {"value": "0.0023"}},
              {"integerValue": {"value": "1500"}}
            ]
          }
        ]
      },
      "crashRate": { ... },
      "slowStartRate": {
        "rows": [
          {
            "startTime": {"year": 2026, "month": 5, "day": 5},
            "dimensions": [{"dimension": "startType", "stringValue": "COLD"}],
            "metrics": [...]
          }
        ]
      },
      "stuckBackgroundWakelockRate": { ... },
      "excessiveWakeupRate": { ... },
      "errorCounts": { ... }
    },
    "period": {
      "start": "2026-05-03T00:00:00",
      "end": "2026-05-06T00:00:00"
    }
  }
}
```

### Metrics collected

| Metric | What it measures |
|---|---|
| `anrRate` | Application Not Responding rate per 100,000 users |
| `crashRate` | Crash rate per 100,000 users |
| `slowStartRate` | Slow start rate (broken down by COLD / WARM start type) |
| `stuckBackgroundWakelockRate` | Background wakelocks that exceed the allowed time |
| `excessiveWakeupRate` | Excessive wakeups (alarms, etc.) |
| `errorCounts` | Combined crash + ANR report count by type |

---

## Architecture & Extending

### Current Structure

```
.
├── fetch_data.py         # API fetcher: vitals + reviews, saves JSON
├── generate_report.py    # LLM reporter: reads JSON, generates .md per app
├── fetch_admob.py        # Standalone AdMob fetcher + LLM reporter (OAuth-based)
├── admob_oauth_setup.py  # One-time helper to generate an AdMob refresh token
├── admob_ad_units.example.json  # Template for declaring ad units per app
├── run_reports.sh        # Bash orchestrator: fetch + report (vitals/reviews)
├── run_admob.sh          # Bash wrapper for AdMob monitoring
├── weekly_report.sh      # Convenience: 7-day report shortcut
├── examples/             # Sanitized sample outputs (reports + JSON structures)
├── .env                  # Your credentials and configuration (gitignored)
├── .env.example          # Template for .env
├── service_account.json  # Google service account key for vitals/reviews (gitignored)
├── admob_oauth_client.json  # OAuth client JSON for AdMob (gitignored, optional)
├── requirements.txt      # Python dependencies
├── data/                 # All output files (gitignored)
└── README.md             # This file
```

### Planned Refactoring for New Data Sources

The current design is intentionally flat and single-purpose, focused on Google Play Vitals. As new data sources are added (e.g., **user reviews**, **ratings**, **in-app review data**, **subscription insights**), the architecture will be refactored into a more modular structure:

```
monitor/
  core/
    auth.py           # Authenticate to any Google API
    freshness.py      # Shared freshness retry logic
    storage.py        # JSON file management
    reporter.py       # Generic LLM prompt builder
  fetchers/
    base.py           # Abstract fetcher interface
    vitals.py         # Current vitals logic (extracted from fetch_data.py)
    reviews.py        # Future: user reviews / comments
    ratings.py        # Future: star ratings
  config.py           # Env + CLI handling
```

Key design principles for the refactored version:

- **Each fetcher is independent** — it registers itself, declares its own API scope, and produces its own output shape.
- **The reporter is source-agnostic** — each data source provides its own prompt builder, and the reporter only orchestrates the LLM call.
- **Shared utilities are extracted** — authentication, freshness retry, and file management are reused across all fetchers.
- **`main.py` discovers fetchers** — no manual wiring when adding a new source.

If you're interested in contributing, the current `fetch_data.py` is the best place to study the patterns before the refactoring.

---

## Troubleshooting

### `Google Play Developer Reporting API has not been used`

You need to enable the API in your Google Cloud project. See the [Setup Guide](#1-google-cloud-project--service-account) above, step 1.2.

After enabling, it may take a few minutes to propagate.

### `'timeline_spec.end_date' field should be at most the current freshness`

The API has a processing delay (typically 3–5 days). The script handles this automatically by parsing the error and retrying with the correct date. This is **normal** — you'll see a log message like:

```
Adjusting end_date to freshness: 2026-05-07
```

### `AttributeError: 'Resource' object has no attribute '...'`

Some metrics may not be available in your version of the API client library. The script only queries the metrics that are present. If a specific metric is missing from your API version, consider updating the client:

```bash
pip install --upgrade google-api-python-client
```

### No data returned for an app

- Make sure the service account has been granted access in the **Play Console** (see [step 2](#2-grant-play-console-access)).
- Verify the package name is correct.
- The app must have some user traffic — apps with no users will have no data.

### `GEMINI_API_KEY not found`

Set `GEMINI_API_KEY` in your `.env` file. See [section 3.2](#where-to-get-a-gemini-api-key).

---

## License

Released under the [Apache License 2.0](LICENSE).
