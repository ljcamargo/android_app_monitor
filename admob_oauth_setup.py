#!/usr/bin/env python3
"""
admob_oauth_setup.py — One-time helper to generate an AdMob API refresh token.

AdMob does NOT support service accounts: the API requires user-based OAuth 2.0
authorized by a Google Account that has access to the target AdMob account.

Prerequisites (do these once):
  1. In Google Cloud Console: APIs & Services > Credentials > Create Credentials
     > OAuth client ID > choose "Desktop app" (simplest) and download the JSON.
  2. In apps.admob.com: Settings > Users > Add user -> invite the Google Account
     you will log in with below (choose an appropriate role). Accept the invite.
  3. Make sure the AdMob API is enabled in Cloud Console.

Usage:
  python3 admob_oauth_setup.py --client-json path/to/client_secret.json
  python3 admob_oauth_setup.py                       # uses ADMOB_CLIENT_CREDENTIALS env or ./oauth_client.json
  python3 admob_oauth_setup.py --console             # headless: paste URL + code manually
  python3 admob_oauth_setup.py --out refresh.txt     # also write the token to a file

On success it prints an ADMOB_REFRESH_TOKEN you can paste into .env.
"""

import os
import json
import argparse
import sys

from dotenv import load_dotenv

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/admob.readonly"]
DEFAULT_CLIENT_FILES = ["oauth_client.json", "admob_oauth_client.json", "client_secret.json"]


def resolve_client_config(client_json):
    """Returns (client_id, client_secret, client_config_dict)."""
    path = client_json or os.getenv("ADMOB_CLIENT_CREDENTIALS")
    if not path:
        for candidate in DEFAULT_CLIENT_FILES:
            if os.path.exists(candidate):
                path = candidate
                break
    if path and os.path.exists(path):
        with open(path) as f:
            config = json.load(f)
        oauth = config.get("installed") or config.get("web") or {}
        return oauth.get("client_id"), oauth.get("client_secret"), config

    client_id = os.getenv("ADMOB_CLIENT_ID")
    client_secret = os.getenv("ADMOB_CLIENT_SECRET")
    if client_id and client_secret:
        return client_id, client_secret, None

    raise ValueError(
        "No OAuth client credentials found. Pass --client-json <file> (downloaded from "
        "Cloud Console > Credentials > OAuth client ID), set ADMOB_CLIENT_CREDENTIALS to "
        "that file path, or set ADMOB_CLIENT_ID / ADMOB_CLIENT_SECRET in .env."
    )


def main():
    parser = argparse.ArgumentParser(description="Generate an AdMob API refresh token.")
    parser.add_argument("--client-json", type=str, default=None,
                        help="Path to the OAuth client JSON downloaded from Cloud Console")
    parser.add_argument("--console", action="store_true",
                        help="Use manual console flow (for headless servers, no browser)")
    parser.add_argument("--out", type=str, default=None,
                        help="Also write the refresh token to this file")
    args = parser.parse_args()

    client_id, client_secret, client_config = resolve_client_config(args.client_json)

    if client_config is not None:
        from google_auth_oauthlib.flow import InstalledAppFlow

        flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
        app_type = "installed" if "installed" in client_config else ("web" if "web" in client_config else "?")
        print(f"Using OAuth client config (type: {app_type})")
    else:
        from google_auth_oauthlib.flow import InstalledAppFlow

        flow = InstalledAppFlow.from_client_config(
            {
                "installed": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            SCOPES,
        )
        print("Using ADMOB_CLIENT_ID / ADMOB_CLIENT_SECRET from environment.")

    print("A browser window will open. Log in with the Google Account that was")
    print("invited to the AdMob account (Settings > Users), then accept the consent.")
    print()

    if args.console:
        credentials = flow.run_console()
    else:
        credentials = flow.run_local_server(port=0)

    refresh_token = credentials.refresh_token
    if not refresh_token:
        sys.exit("ERROR: No refresh token returned. If this is a 'Web application' client, "
                 "you may need to use the Desktop app type or the --console flow.")

    print()
    print("=" * 70)
    print("SUCCESS! Add this line to your .env file:")
    print(f"ADMOB_REFRESH_TOKEN={refresh_token}")
    print("=" * 70)
    print()
    print("Also add (if not already present):")
    print(f"ADMOB_CLIENT_ID={client_id}")
    print(f"ADMOB_CLIENT_SECRET={client_secret}")
    print()
    print("Then run: python3 fetch_admob.py --days 7 --discover")

    if args.out:
        with open(args.out, "w") as f:
            f.write(refresh_token + "\n")
        print(f"\nRefresh token also saved to {args.out}")


if __name__ == "__main__":
    main()
