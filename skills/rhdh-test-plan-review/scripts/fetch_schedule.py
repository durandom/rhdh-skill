#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "google-api-python-client>=2.0",
#   "google-auth>=2.0",
#   "google-auth-httplib2>=0.2",
# ]
# ///
"""Fetch RHDH milestone dates (Feature Freeze, Code Freeze, GA) from the RHDH schedule Google Sheet."""

import argparse
import json
import os
import re
import sys
from datetime import datetime

_no_color = os.environ.get("NO_COLOR") is not None
_is_tty = sys.stderr.isatty() and not _no_color


def log(msg):
    """Write to stderr — keeps stdout clean for JSON output."""
    if _is_tty:
        print(msg, file=sys.stderr)


def error_exit(error_key, extra=None):
    result = {"error": error_key}
    if extra:
        result.update(extra)
    json.dump(result, sys.stdout, indent=2)
    print()
    sys.exit(1)


def get_gcloud_token():
    """Get an access token from gcloud auth print-access-token."""
    import shutil
    import subprocess

    gcloud = shutil.which("gcloud")
    if not gcloud:
        error_exit(
            "gcloud_not_found",
            {"hint": "Install the Google Cloud CLI and ensure gcloud is on your PATH"},
        )

    result = subprocess.run([gcloud, "auth", "print-access-token"], capture_output=True, text=True)
    token = result.stdout.strip()
    return token if token else None


def get_sheets_service():
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    token = get_gcloud_token()
    if not token:
        error_exit(
            "credentials_not_found",
            {"hint": "Run 'gcloud auth login --enable-gdrive-access' to authenticate"},
        )

    creds = Credentials(token=token)
    return build("sheets", "v4", credentials=creds)


def get_sheet_tabs(service, spreadsheet_id):
    from googleapiclient.errors import HttpError

    try:
        meta = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    except HttpError as e:
        if e.resp.status == 404:
            error_exit(
                "spreadsheet_not_found",
                {
                    "spreadsheet_id": spreadsheet_id,
                    "hint": "The spreadsheet was not found. Pass the correct ID with --sheet-id or share the sheet URL.",
                },
            )
        raise
    return [s["properties"]["title"] for s in meta.get("sheets", [])]


def find_schedule_tab(tabs):
    """Find the best 'Schedule' tab — tries current year, then next, then previous."""
    current_year = datetime.now().year
    for year in [current_year, current_year + 1, current_year - 1]:
        candidates = [t for t in tabs if str(year) in t and "schedule" in t.lower()]
        if candidates:
            return candidates[0]
    # Fallback: any tab with "schedule"
    fallback = [t for t in tabs if "schedule" in t.lower()]
    return fallback[0] if fallback else None


def normalize_version(v):
    """Extract major.minor from strings like 'RHDH 1.6', 'rhdh-1.6', 'v1.6', '1.6'."""
    m = re.search(r"(\d+)\.(\d+)", v)
    if m:
        return f"{m.group(1)}.{m.group(2)}"
    return v.strip()


def parse_date(raw):
    """Try common date formats found in Google Sheets."""
    raw = raw.strip()
    for fmt in (
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%B %d, %Y",
        "%b %d, %Y",
        "%d %b %Y",
        "%d %B %Y",
        "%m/%d/%y",
    ):
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None  # unparseable


def row_date(cells):
    """Return the first parseable date found in a row's cells, or None."""
    for cell in cells:
        parsed = parse_date(str(cell))
        if parsed:
            return parsed
    return None


def find_milestones(rows, version):
    """
    Search sheet rows for RHDH version milestones.

    The sheet is chronological. Milestone rows (Code Freeze, Feature Freeze)
    may or may not include the version name — they precede the GA row.

    Strategy:
    1. Find the GA row for the target version (must contain version string + GA keyword).
    2. Walk backwards from the GA row to find the closest Code Freeze and
       Feature Freeze rows. Stop when we hit a GA row for a different version
       (those milestones belong to the previous release, not this one).
    """
    ver = normalize_version(version)

    ga_keywords = ["ga ", "ga\t", "ga\n", "ga announce", "general availability", "ga date"]
    freeze_keywords = {
        "code_freeze": ["code freeze", "code-freeze", "codefreeze"],
        "feature_freeze": ["feature freeze", "feature-freeze", " ff "],
    }

    # Step 1: find the index of the GA row for this version
    ga_index = None
    for i, row in enumerate(rows):
        cells = [str(c) for c in row]
        row_text = " " + " ".join(cells).lower() + " "
        version_match = ver in row_text or (version.lower().replace("rhdh", "").strip() in row_text)
        ga_match = any(kw in row_text for kw in ga_keywords)
        if version_match and ga_match:
            ga_index = i
            break

    if ga_index is None:
        return {}

    ga_date = row_date([str(c) for c in rows[ga_index]])
    milestones = {"ga_date": ga_date} if ga_date else {}

    # Step 2: walk backwards from the GA row to find freeze dates
    found = {}
    for i in range(ga_index - 1, -1, -1):
        cells = [str(c) for c in rows[i]]
        row_text = " " + " ".join(cells).lower() + " "

        # Stop if we hit a GA row for a different version (we've gone too far back)
        if any(kw in row_text for kw in ga_keywords):
            break

        for milestone, keywords in freeze_keywords.items():
            if milestone in found:
                continue
            if any(kw in row_text for kw in keywords):
                d = row_date(cells)
                if d:
                    found[milestone] = d

        if len(found) == len(freeze_keywords):
            break  # found all freeze dates, no need to go further back

    milestones.update(found)
    return milestones


def main():
    parser = argparse.ArgumentParser(
        description="Fetch RHDH milestone dates from the RHDH schedule Google Sheet."
    )
    parser.add_argument(
        "--version",
        required=True,
        help="RHDH version to look up (e.g. '1.6', 'RHDH 1.6', 'rhdh-1.6')",
    )
    parser.add_argument(
        "--sheet-id",
        default="1knVzlMW0l0X4c7gkoiuaGql1zuFgEGwHHBsj-ygUTnc",
        help="RHDH Release Schedule spreadsheet ID",
    )
    args = parser.parse_args()

    version = normalize_version(args.version)
    sheet_id = args.sheet_id
    log(f"Looking up milestones for RHDH {version}...")

    service = get_sheets_service()
    tabs = get_sheet_tabs(service, sheet_id)
    log(f"Found tabs: {tabs}")

    tab = find_schedule_tab(tabs)
    if not tab:
        error_exit("no_schedule_tab_found", {"tabs": tabs, "spreadsheet_id": sheet_id})

    log(f"Reading tab: {tab}")
    result = service.spreadsheets().values().get(spreadsheetId=sheet_id, range=tab).execute()
    rows = result.get("values", [])

    milestones = find_milestones(rows, version)

    if not milestones.get("code_freeze") and not milestones.get("ga_date"):
        error_exit(
            "version_not_found",
            {
                "version": version,
                "tab": tab,
                "spreadsheet_id": sheet_id,
                "hint": "Check that the version string matches the sheet exactly",
            },
        )

    output = {
        "version": version,
        "tab": tab,
        "feature_freeze": milestones.get("feature_freeze"),
        "code_freeze": milestones.get("code_freeze"),
        "ga_date": milestones.get("ga_date"),
    }

    json.dump(output, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
