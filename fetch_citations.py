#!/usr/bin/env python3
"""
Fetch per-paper Google Scholar citation counts via SerpApi and write them
to citations.json.

Reads two values from the environment:
  SERPAPI_KEY   - your SerpApi private API key
  SCHOLAR_ID    - the Google Scholar author id (e.g. ElQU3_0AAAAJ)

Writes citations.json (a per-paper list) in the current directory. Designed
to run on a schedule (e.g. GitHub Actions). Exits non-zero on failure so a
failed run is visible, WITHOUT overwriting the last good citations.json.
"""

import json
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone

API_ENDPOINT = "https://serpapi.com/search"
PAGE_SIZE = 100  # SerpApi max articles per page for the author engine


def fail(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def get(url):
    try:
        with urllib.request.urlopen(url, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:  # noqa: BLE001
        fail(f"Request to SerpApi failed: {e}")


def make_slug(title):
    """Stable, URL-safe id derived from the paper title. Used to match a
    paper to its count on the website."""
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug[:80]


def main():
    api_key = os.environ.get("SERPAPI_KEY")
    scholar_id = os.environ.get("SCHOLAR_ID")
    if not api_key:
        fail("SERPAPI_KEY environment variable is not set.")
    if not scholar_id:
        fail("SCHOLAR_ID environment variable is not set.")

    base_params = {
        "engine": "google_scholar_author",
        "author_id": scholar_id,
        "api_key": api_key,
        "hl": "en",
        "sort": "pubdate",     # newest first
        "num": str(PAGE_SIZE),
    }

    # First page (also surfaces any API error / bad key / quota).
    first = get(API_ENDPOINT + "?" + urllib.parse.urlencode(dict(base_params, start="0")))
    if first.get("error"):
        fail(f"SerpApi returned an error: {first['error']}")
    status = first.get("search_metadata", {}).get("status")
    if status and status != "Success":
        fail(f"SerpApi search status was '{status}', expected 'Success'.")

    author_name = first.get("author", {}).get("name", "")

    # Collect all article pages.
    articles = list(first.get("articles", []))
    start = PAGE_SIZE
    for _ in range(10):  # safety cap: 1000 papers
        if len(articles) < start:
            break
        page = get(API_ENDPOINT + "?" + urllib.parse.urlencode(dict(base_params, start=str(start))))
        batch = page.get("articles", [])
        if not batch:
            break
        articles.extend(batch)
        if len(batch) < PAGE_SIZE:
            break
        start += PAGE_SIZE

    if not articles:
        fail(f"No articles returned. Check that SCHOLAR_ID '{scholar_id}' is correct.")

    papers = []
    for a in articles:
        cited = a.get("cited_by", {}).get("value")
        title = a.get("title", "")
        papers.append({
            "id": make_slug(title),
            "title": title,
            "authors": a.get("authors", ""),
            "publication": a.get("publication", ""),
            "year": a.get("year", ""),
            "citations": cited if isinstance(cited, int) else 0,
            "link": a.get("link", ""),
        })

    out = {
        "author": author_name,
        "scholar_id": scholar_id,
        "paper_count": len(papers),
        "papers": papers,
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    with open("citations.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Wrote citations.json: {len(papers)} papers for {author_name or scholar_id}")


if __name__ == "__main__":
    main()
