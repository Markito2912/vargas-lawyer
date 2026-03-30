#!/usr/bin/env python3
"""
Google Search Console post-deploy helper.

What this script does:
1) Submits a sitemap to Search Console.
2) Runs URL Inspection API checks for important URLs.
3) Prints direct Search Console inspection links so you can click
   "Request indexing" manually in the UI.

Why manual click is still needed:
- Search Console API does not expose a "request indexing" endpoint for
  normal web pages. URL Inspection API is read/inspect only.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
import webbrowser
from pathlib import Path
from typing import Iterable

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = [
    "https://www.googleapis.com/auth/webmasters",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Automate GSC post-deploy actions (sitemap + URL inspection)."
    )
    parser.add_argument(
        "--site-url",
        default="sc-domain:vargaslawyer.com",
        help="Search Console property URL (e.g. sc-domain:example.com or https://example.com/).",
    )
    parser.add_argument(
        "--sitemap-url",
        default="https://vargaslawyer.com/sitemap.xml",
        help="Full sitemap URL to submit.",
    )
    parser.add_argument(
        "--inspect-url",
        action="append",
        dest="inspect_urls",
        default=[],
        help="URL to inspect. Repeat for multiple URLs.",
    )
    parser.add_argument(
        "--client-secret",
        default="client_secret.json",
        help="OAuth client secret JSON from Google Cloud OAuth credentials.",
    )
    parser.add_argument(
        "--token-file",
        default=".gsc-token.json",
        help="Token cache path (created after first login).",
    )
    parser.add_argument(
        "--open-links",
        action="store_true",
        help="Open Search Console inspection links in browser after checks.",
    )
    return parser.parse_args()


def ensure_default_urls(urls: Iterable[str]) -> list[str]:
    cleaned = [u.strip() for u in urls if u and u.strip()]
    if cleaned:
        return cleaned
    return [
        "https://vargaslawyer.com/abogados-en-santo-domingo.html",
        "https://vargaslawyer.com/",
    ]


def load_credentials(client_secret_path: Path, token_path: Path) -> Credentials:
    creds: Credentials | None = None

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not client_secret_path.exists():
                raise FileNotFoundError(
                    f"OAuth client secret not found: {client_secret_path}"
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                str(client_secret_path), SCOPES
            )
            creds = flow.run_local_server(port=0)

        token_path.write_text(creds.to_json(), encoding="utf-8")

    return creds


def submit_sitemap(webmasters_service, site_url: str, sitemap_url: str) -> None:
    webmasters_service.sitemaps().submit(
        siteUrl=site_url, feedpath=sitemap_url
    ).execute()


def inspect_url(searchconsole_service, site_url: str, url: str) -> dict:
    body = {
        "inspectionUrl": url,
        "siteUrl": site_url,
    }
    return (
        searchconsole_service.urlInspection().index().inspect(body=body).execute()
    )


def inspection_link(site_url: str, inspect_url_value: str) -> str:
    resource = urllib.parse.quote(site_url, safe="")
    inspect = urllib.parse.quote(inspect_url_value, safe="")
    return (
        "https://search.google.com/search-console/inspect"
        f"?resource_id={resource}&id={inspect}"
    )


def print_inspection_summary(url: str, response: dict) -> None:
    result = response.get("inspectionResult", {})
    idx = result.get("indexStatusResult", {})

    summary = {
        "url": url,
        "verdict": idx.get("verdict"),
        "coverageState": idx.get("coverageState"),
        "indexingState": idx.get("indexingState"),
        "pageFetchState": idx.get("pageFetchState"),
        "lastCrawlTime": idx.get("lastCrawlTime"),
        "googleCanonical": idx.get("googleCanonical"),
        "userCanonical": idx.get("userCanonical"),
        "inspectionResultLink": result.get("inspectionResultLink"),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def main() -> int:
    args = parse_args()
    inspect_urls = ensure_default_urls(args.inspect_urls)

    client_secret = Path(args.client_secret).resolve()
    token_file = Path(args.token_file).resolve()

    try:
        creds = load_credentials(client_secret, token_file)
        webmasters_service = build(
            "webmasters", "v3", credentials=creds, cache_discovery=False
        )
        searchconsole_service = build(
            "searchconsole", "v1", credentials=creds, cache_discovery=False
        )

        print(f"[1/3] Submitting sitemap: {args.sitemap_url}")
        submit_sitemap(webmasters_service, args.site_url, args.sitemap_url)
        print("Sitemap submitted successfully.")

        print("[2/3] Inspecting URLs")
        for url in inspect_urls:
            print(f"\nInspecting: {url}")
            response = inspect_url(searchconsole_service, args.site_url, url)
            print_inspection_summary(url, response)

        print("\n[3/3] Manual 'Request indexing' links")
        for url in inspect_urls:
            link = inspection_link(args.site_url, url)
            print(f"- {url}\n  {link}")
            if args.open_links:
                webbrowser.open(link)

        print(
            "\nDone. Open each inspection link above and click 'Request indexing'."
        )
        return 0

    except FileNotFoundError as err:
        print(f"ERROR: {err}", file=sys.stderr)
        print(
            "Create OAuth Desktop credentials JSON in Google Cloud and save it "
            "as client_secret.json next to this script, or pass --client-secret.",
            file=sys.stderr,
        )
        return 2
    except HttpError as err:
        status = getattr(err, "status_code", None) or getattr(err.resp, "status", "n/a")
        print(f"HTTP ERROR ({status}): {err}", file=sys.stderr)
        print(
            "Check that:\n"
            "- Search Console API is enabled in Google Cloud\n"
            "- Logged-in Google account has owner/full access on the property\n"
            "- --site-url matches your Search Console property exactly",
            file=sys.stderr,
        )
        return 3
    except Exception as err:  # noqa: BLE001
        print(f"UNEXPECTED ERROR: {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
