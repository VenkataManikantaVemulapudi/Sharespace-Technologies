"""
Async logo downloader

Features:
- Input: list of company website URLs (CLI or edit URLs list)
- Detects main logo or favicon via <link rel="icon"|"shortcut icon">, common selectors, or fallback /favicon.ico
- Asynchronous fetching with aiohttp for speed
- Saves images using a safe filename derived from the domain/company name
- Robust to http/https and redirects
- Continues on errors; prints summary

Usage (examples):
  python download_logos.py https://example.com https://github.com
  # Or from a file (one URL per line):
  python download_logos.py --file urls.txt

Requires: aiohttp, beautifulsoup4, requests (optional), pillow (optional for format normalization)
"""

import asyncio
import aiohttp
from aiohttp import ClientTimeout
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import os
import sys
from typing import List, Optional, Tuple

# --------------- Config ---------------
TIMEOUT = ClientTimeout(total=20)
HEADERS = {"User-Agent": "Mozilla/5.0 (LogoFetcher/1.0)"}
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "img", "clients_downloaded")
SUPPORTED_IMAGE_EXTS = {"ico", "png", "jpg", "jpeg", "svg", "gif", "webp"}

# --------------- Helpers ---------------

def safe_name_from_url(url: str) -> str:
    """Generate a filesystem-safe base name from a company URL (domain without TLD)."""
    host = urlparse(url).netloc.lower()
    host = host.split(":")[0]
    if host.startswith("www."):
        host = host[4:]
    base = host.split(".")
    # Prefer second-level domain if available, else the host
    if len(base) >= 2:
        name = base[-2]
    else:
        name = base[0]
    name = re.sub(r"[^a-z0-9_-]", "-", name)
    return name or "company"

async def fetch(session: aiohttp.ClientSession, url: str) -> Tuple[Optional[str], Optional[bytes]]:
    """GET a URL and return (content_type, content_bytes)."""
    try:
        async with session.get(url, timeout=TIMEOUT, allow_redirects=True) as resp:
            if resp.status >= 400:
                return None, None
            ctype = resp.headers.get("Content-Type", "").split(";")[0].strip().lower()
            data = await resp.read()
            return ctype, data
    except Exception:
        return None, None

async def fetch_text(session: aiohttp.ClientSession, url: str) -> Optional[str]:
    ctype, data = await fetch(session, url)
    if data is None:
        return None
    # Try to decode as text; default to utf-8 with errors ignored
    try:
        return data.decode("utf-8", errors="ignore")
    except Exception:
        return None

def candidate_logo_links(soup: BeautifulSoup, base_url: str) -> List[str]:
    """Extract candidate logo URLs from HTML soup in order of preference."""
    links: List[str] = []
    # <link rel> icons
    for rel in ["icon", "shortcut icon", "apple-touch-icon", "mask-icon"]:
        for tag in soup.find_all("link", rel=lambda r: r and rel in r):
            href = tag.get("href")
            if href:
                links.append(urljoin(base_url, href))

    # Common selectors for logos in header/nav
    for sel in [
        "img[alt*='logo' i]",
        "img[src*='logo' i]",
        "header img",
        "nav img",
        ".site-logo img, .navbar-brand img, .brand img, .logo img",
    ]:
        for tag in soup.select(sel):
            src = tag.get("src")
            if src:
                links.append(urljoin(base_url, src))

    # Deduplicate preserving order
    seen = set()
    uniq = []
    for u in links:
        if u not in seen:
            seen.add(u)
            uniq.append(u)
    return uniq

def guess_ext(content_type: str, url: str) -> str:
    if content_type:
        if "svg" in content_type:
            return "svg"
        if "png" in content_type:
            return "png"
        if "jpeg" in content_type or "jpg" in content_type:
            return "jpg"
        if "gif" in content_type:
            return "gif"
        if "webp" in content_type:
            return "webp"
        if "ico" in content_type or "x-icon" in content_type:
            return "ico"
    # Fallback to URL extension
    path = urlparse(url).path.lower()
    m = re.search(r"\.([a-z0-9]{2,4})$", path)
    if m:
        ext = m.group(1)
        if ext in SUPPORTED_IMAGE_EXTS:
            return ext
    return "ico"

async def find_logo_url(session: aiohttp.ClientSession, base_url: str) -> Optional[str]:
    """Try to find a logo URL by scanning the HTML; fallback to /favicon.ico."""
    html = await fetch_text(session, base_url)
    if html:
        soup = BeautifulSoup(html, "html.parser")
        candidates = candidate_logo_links(soup, base_url)
        for u in candidates:
            # quick HEAD/GET to validate image
            ctype, _ = await fetch(session, u)
            if ctype and ("image" in ctype or any(x in ctype for x in ("svg", "icon"))):
                return u
    # Fallbacks: /favicon.ico (try both http/https if scheme not specified)
    parsed = urlparse(base_url)
    scheme = parsed.scheme or "https"
    host = parsed.netloc
    for path in ["/favicon.ico", "/favicon.png", "/static/favicon.ico"]:
        test_url = f"{scheme}://{host}{path}"
        ctype, _ = await fetch(session, test_url)
        if ctype and ("image" in ctype or "icon" in ctype):
            return test_url
    return None

async def download_logo(session: aiohttp.ClientSession, url: str) -> Tuple[str, bool, Optional[str]]:
    """Download a single site's logo. Returns (name_base, success, saved_path or error)."""
    # Normalize URL (ensure scheme)
    if not re.match(r"^https?://", url, flags=re.I):
        url = "https://" + url
    name_base = safe_name_from_url(url)

    # Ensure output dir
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    logo_url = await find_logo_url(session, url)
    if not logo_url:
        return name_base, False, "logo not found"

    ctype, data = await fetch(session, logo_url)
    if not data:
        return name_base, False, f"failed to fetch logo: {logo_url}"

    ext = guess_ext(ctype or "", logo_url)
    filename = f"{name_base}.{ext}"
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "wb") as f:
        f.write(data)
    return name_base, True, path

async def main(urls: List[str]) -> None:
    # Clean and dedup URLs
    urls = [u.strip() for u in urls if u.strip()]
    seen = set()
    uniq_urls = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            uniq_urls.append(u)

    if not uniq_urls:
        print("No URLs provided.")
        return

    async with aiohttp.ClientSession(headers=HEADERS) as session:
        tasks = [download_logo(session, u) for u in uniq_urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    # Report
    success = 0
    for u, res in zip(uniq_urls, results):
        if isinstance(res, Exception):
            print(f"[FAIL] {u} -> exception: {res}")
            continue
        name_base, ok, info = res
        if ok:
            success += 1
            print(f"[OK]   {u} -> {info}")
        else:
            print(f"[MISS] {u} -> {info}")
    print(f"Done. {success}/{len(uniq_urls)} succeeded. Saved to: {OUTPUT_DIR}")

if __name__ == "__main__":
    # CLI parsing: accept URLs as args or --file file.txt
    args = sys.argv[1:]
    urls: List[str] = []
    if not args:
        print(__doc__)
        sys.exit(0)
    if args and args[0] == "--file" and len(args) >= 2:
        file_path = args[1]
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            sys.exit(1)
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            urls = [line.strip() for line in f if line.strip()]
    else:
        urls = args

    asyncio.run(main(urls))
