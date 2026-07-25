#!/usr/bin/env python3
"""
Fetch Google Scholar citation totals via SerpApi and write them to citations.json.

Reads two values from the environment:
  SERPAPI_KEY   - your SerpApi private API key
  SCHOLAR_ID    - the Google Scholar author id (e.g. ElQU3_0AAAAJ)

Writes citations.json in the current directory. Designed to be run on a
schedule (e.g. GitHub Actions). Exits non-zero on failure so a failed run
is visible, WITHOUT overwriting the last good citations.json.
"""

import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone

API_ENDPOINT = "https://serpapi.com/search"


def fail(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def main():
    api_key = os.environ.get("SERPAPI_KEY")
    scholar_id = os.environ.get("SCHOLAR_ID")

    if not api_key:
        fail("SERPAPI_KEY environment variable is not set.")
    if not scholar_id:
        fail("SCHOLAR_ID environment variable is not set.")

    params = {
        "engine": "google_scholar_author",
        "author_id": scholar_id,
        "api_key": api_key,
        "hl": "en",
    }
    url = API_ENDPOINT + "?" + urllib.parse.urlencode(params)

    try:
        with urllib.request.urlopen(url, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:  # noqa: BLE001 - we want any failure to stop here
        fail(f"Request to SerpApi failed: {e}")

    # Surface SerpApi-reported errors (bad key, quota, etc.)
    status = data.get("search_metadata", {}).get("status")
    if data.get("error"):
        fail(f"SerpApi returned an error: {data['error']}")
    if status and status != "Success":
        fail(f"SerpApi search status was '{status}', expected 'Success'.")

    # The citation totals table looks like:
    #   cited_by.table = [
    #     {"citations": {"all": 12345, "since_2020": 6789}},
    #     {"h_index":   {"all": 42, ...}},
    #     {"i10_index": {"all": 88, ...}},
    #   ]
    try:
        table = data["cited_by"]["table"]
        citations_all = None
        h_index_all = None
        i10_all = None
        for row in table:
            if "citations" in row:
                citations_all = row["citations"]["all"]
            elif "h_index" in row:
                h_index_all = row["h_index"]["all"]
            elif "i10_index" in row:
                i10_all = row["i10_index"]["all"]
        if citations_all is None:
            raise KeyError("citations.all not found in cited_by.table")
    except (KeyError, TypeError, IndexError) as e:
        fail(f"Could not find citation total in response ({e}). "
             f"Check that SCHOLAR_ID '{scholar_id}' is correct.")

    author_name = data.get("author", {}).get("name", "")

    out = {
        "citations": citations_all,
        "h_index": h_index_all,
        "i10_index": i10_all,
        "author": author_name,
        "scholar_id": scholar_id,
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    with open("citations.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
        f.write("\n")

    print(f"Wrote citations.json: {citations_all} citations "
          f"(h-index {h_index_all}, i10 {i10_all}) for {author_name or scholar_id}")


if __name__ == "__main__":
    main()
