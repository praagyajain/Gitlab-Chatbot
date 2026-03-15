"""
Web scraper for GitLab Handbook and Direction pages.

Crawls curated seed URLs, extracts main content, and saves each page
as a JSON file for downstream processing.

Usage:
    python scraper.py
"""

import json
import os
import re
import time
import hashlib
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from config import (
    HANDBOOK_SEED_URLS,
    DIRECTION_SEED_URLS,
    RAW_DATA_DIR,
    REQUEST_DELAY,
    MAX_HANDBOOK_PAGES,
    MAX_DIRECTION_PAGES,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _slug(url: str) -> str:
    """Create a filesystem-safe slug from a URL."""
    return hashlib.md5(url.encode()).hexdigest()


def _clean_text(text: str) -> str:
    """Collapse whitespace and strip leading/trailing blanks."""
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


# ── Content extraction ────────────────────────────────────────────────────────

def extract_handbook_content(soup: BeautifulSoup) -> str:
    """Extract main content from a handbook.gitlab.com page."""
    # Try common content containers
    main = (
        soup.find("main")
        or soup.find("article")
        or soup.find("div", {"class": re.compile(r"content|markdown|handbook", re.I)})
        or soup.find("div", {"id": re.compile(r"content|main", re.I)})
    )
    if main is None:
        main = soup.body or soup

    # Remove noise elements
    for tag in main.find_all(["nav", "footer", "header", "script", "style", "noscript", "aside"]):
        tag.decompose()
    for tag in main.find_all("div", {"class": re.compile(r"sidebar|breadcrumb|toc|nav|menu|footer", re.I)}):
        tag.decompose()

    return _clean_text(main.get_text(separator="\n"))


def extract_direction_content(soup: BeautifulSoup) -> str:
    """Extract main content from an about.gitlab.com/direction page."""
    main = (
        soup.find("main")
        or soup.find("article")
        or soup.find("div", {"class": re.compile(r"content|direction|markdown", re.I)})
    )
    if main is None:
        main = soup.body or soup

    for tag in main.find_all(["nav", "footer", "header", "script", "style", "noscript", "aside"]):
        tag.decompose()
    for tag in main.find_all("div", {"class": re.compile(r"sidebar|breadcrumb|toc|nav|menu|footer", re.I)}):
        tag.decompose()

    return _clean_text(main.get_text(separator="\n"))


def extract_title(soup: BeautifulSoup) -> str:
    """Extract the page title."""
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    h1 = soup.find("h1")
    if h1:
        return h1.get_text(strip=True)
    return "Untitled"


# ── Discovery ────────────────────────────────────────────────────────────────

def discover_links(soup: BeautifulSoup, base_url: str, domain_prefix: str) -> list[str]:
    """Find internal links on a page that stay within the allowed domain prefix."""
    links = set()
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        full_url = urljoin(base_url, href)
        # Strip fragment
        full_url = full_url.split("#")[0].rstrip("/") + "/"
        parsed = urlparse(full_url)
        if full_url.startswith(domain_prefix) and parsed.scheme in ("http", "https"):
            links.add(full_url)
    return list(links)


# ── Main scraper ──────────────────────────────────────────────────────────────

def scrape_pages(seed_urls: list[str], domain_prefix: str, source_type: str, max_pages: int) -> int:
    """
    BFS-crawl starting from seed_urls, staying within domain_prefix.
    Returns the number of pages successfully scraped.
    """
    os.makedirs(RAW_DATA_DIR, exist_ok=True)

    visited: set[str] = set()
    queue: list[str] = list(seed_urls)
    count = 0

    headers = {
        "User-Agent": (
            "GitLabHandbookBot/1.0 "
            "(Educational project; polite crawling; +https://github.com)"
        )
    }

    while queue and count < max_pages:
        url = queue.pop(0)
        if url in visited:
            continue
        visited.add(url)

        # Check local cache to avoid re-downloading if already scraped
        filepath = os.path.join(RAW_DATA_DIR, f"{_slug(url)}.json")
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if "links" in data:
                    count += 1
                    print(f"  ⏭ [{count}] Cached — {url}")
                    for link in data["links"]:
                        if link not in visited:
                            queue.append(link)
                    continue
            except Exception:
                pass

        try:
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code != 200:
                print(f"  ⚠ {resp.status_code} — {url}")
                continue

            soup = BeautifulSoup(resp.text, "html.parser")
            title = extract_title(soup)

            if "handbook.gitlab.com" in url:
                content = extract_handbook_content(soup)
            else:
                content = extract_direction_content(soup)

            # Discover and enqueue new links (limited BFS)
            new_links = discover_links(soup, url, domain_prefix)
            for link in new_links:
                if link not in visited:
                    queue.append(link)
                
            # Skip pages with very little content
            if len(content) < 40:
                print(f"  ⏭ Skipping (too short) — {url}")
                continue

            # Save as JSON
            page_data = {
                "url": url,
                "title": title,
                "source_type": source_type,
                "content": content,
                "links": new_links,
                "scraped_at": datetime.now(timezone.utc).isoformat(),
            }
            filepath = os.path.join(RAW_DATA_DIR, f"{_slug(url)}.json")
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(page_data, f, ensure_ascii=False, indent=2)

            count += 1
            print(f"  ✓ [{count}] {title[:60]} — {url}")

        except requests.RequestException as e:
            print(f"  ✗ Error — {url}: {e}")

        time.sleep(REQUEST_DELAY)

    return count


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  GitLab Handbook & Direction Scraper")
    print("=" * 60)

    print("\n📘 Scraping GitLab Handbook pages...")
    handbook_count = scrape_pages(
        seed_urls=HANDBOOK_SEED_URLS,
        domain_prefix="https://handbook.gitlab.com/handbook/",
        source_type="handbook",
        max_pages=MAX_HANDBOOK_PAGES
    )

    print(f"\n📗 Scraping GitLab Direction pages...")
    direction_count = scrape_pages(
        seed_urls=DIRECTION_SEED_URLS,
        domain_prefix="https://about.gitlab.com/direction/",
        source_type="direction",
        max_pages=MAX_DIRECTION_PAGES
    )

    total = handbook_count + direction_count
    print(f"\n{'=' * 60}")
    print(f"  Done! Scraped {total} pages ({handbook_count} handbook + {direction_count} direction)")
    print(f"  Data saved to: {RAW_DATA_DIR}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
