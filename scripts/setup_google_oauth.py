#!/usr/bin/env python3
"""One-time Google OAuth2 consent flow — run once to generate .google_token.json."""
import os
import sys
import json
import argparse

# Add backend to path so we can load config
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from google_auth_oauthlib.flow import InstalledAppFlow
from core.config import get_settings

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def main():
    parser = argparse.ArgumentParser(description="Set up Google OAuth2 credentials")
    parser.add_argument(
        "--credentials-file",
        default="credentials.json",
        help="Path to Google OAuth2 credentials JSON downloaded from Google Cloud Console",
    )
    args = parser.parse_args()

    settings = get_settings()
    token_file = settings.google_token_file

    if not os.path.exists(args.credentials_file):
        # Try building credentials from env vars
        if settings.google_client_id and settings.google_client_secret:
            creds_data = {
                "installed": {
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "redirect_uris": ["http://localhost"],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            }
            args.credentials_file = "_tmp_credentials.json"
            with open(args.credentials_file, "w") as f:
                json.dump(creds_data, f)
            print("Built credentials from environment variables.")
        else:
            print(
                f"ERROR: {args.credentials_file} not found and GOOGLE_CLIENT_ID/SECRET not set.\n"
                "Download credentials.json from Google Cloud Console → APIs & Services → Credentials."
            )
            sys.exit(1)

    flow = InstalledAppFlow.from_client_secrets_file(args.credentials_file, SCOPES)
    creds = flow.run_local_server(port=0)

    with open(token_file, "w") as f:
        f.write(creds.to_json())

    print(f"\nGoogle OAuth token saved to: {token_file}")
    print("You can now start the backend server.")

    # Clean up temp file
    if args.credentials_file == "_tmp_credentials.json":
        os.remove(args.credentials_file)


if __name__ == "__main__":
    main()
