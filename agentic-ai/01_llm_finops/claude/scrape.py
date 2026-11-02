#!/usr/bin/env python3
"""
Website scraper: crawls pages on one domain and saves everything it finds.

Uses only the Python standard library (3.8+), so there is nothing to install.

For each page it saves:
  - raw HTML                     -> <out>/html/<slug>.html
  - structured data (JSON)       -> <out>/pages/<slug>.json
      url, status, title, meta tags, headings, visible text,
      links, images, tables
Plus, for the whole run:
  - <out>/index.json   summary of every URL visited (ok or failed)
  - <out>/errors.json  every failure with its reason
  - <out>/scrape.log   full log

Error handling:
  - network errors, timeouts, DNS failures, SSL errors -> retried with backoff
  - HTTP 429 / 5xx -> retried (honours Retry-After); other 4xx -> recorded, not retried
  - non-HTML responses, oversized pages, decode problems -> recorded and skipped
  - parse errors on a single page never stop the crawl
  - robots.txt is respected (disable with --ignore-robots)
  - Ctrl+C stops cleanly and still writes index.json / errors.json

Usage:
  python3 scrape.py https://example.com
  python3 scrape.py https://example.com --max-pages 200 --depth 3 --delay 1 -o out
  python3 scrape.py https://example.com/page --max-pages 1      # single page
"""

import argparse
import hashlib
import json
import logging
import re
import socket
import ssl
import sys
import time
import urllib.error
import urllib.request
import urllib.robotparser
from collections import deque
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urldefrag, urljoin, urlparse

USER_AGENT = "Mozilla/5.0 (compatible; SimpleScraper/1.0)"
MAX_BYTES = 10 * 1024 * 1024  # skip pages larger than 10 MB
RETRYABLE_STATUS = {408, 425, 429, 500, 502, 503, 504}
SKIP_EXTENSIONS = (
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".ico", ".pdf", ".zip",
    ".gz", ".tar", ".mp3", ".mp4", ".avi", ".mov", ".css", ".js", ".woff",
    ".woff2", ".ttf", ".exe", ".dmg", ".xml", ".json",
)

log = logging.getLogger("scraper")


class FetchError(Exception):
    """A page could not be fetched; `retryable` says whether to try again."""

    def __init__(self, message, status=None, retryable=False, retry_after=None):
        super().__init__(message)
        self.status = status
        self.retryable = retryable
        self.retry_after = retry_after


# --------------------------------------------------------------------------- #
# HTML parsing
# --------------------------------------------------------------------------- #
class PageParser(HTMLParser):
    """Extracts title, meta, headings, text, links, images and tables."""

    SKIP_TEXT_TAGS = {"script", "style", "noscript", "template", "svg"}
    HEADINGS = {"h1", "h2", "h3", "h4", "h5", "h6"}

    def __init__(self, base_url):
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.title = ""
        self.meta = {}
        self.headings = []
        self.text_parts = []
        self.links = []
        self.images = []
        self.tables = []

        self._skip_depth = 0
        self._in_title = False
        self._heading = None          # [tag, [text parts]]
        self._link = None             # {"href":..., "text": [parts]}
        self._table_stack = []        # list of tables, each a list of rows
        self._row = None
        self._cell = None

    def handle_starttag(self, tag, attrs):
        a = {k: (v or "") for k, v in attrs}

        if tag in self.SKIP_TEXT_TAGS:
            self._skip_depth += 1
        elif tag == "title":
            self._in_title = True
        elif tag == "base" and a.get("href"):
            self.base_url = urljoin(self.base_url, a["href"])
        elif tag == "meta":
            key = a.get("name") or a.get("property") or a.get("http-equiv")
            if key and "content" in a:
                self.meta[key.lower()] = a["content"]
            elif "charset" in a:
                self.meta["charset"] = a["charset"]
        elif tag in self.HEADINGS:
            self._heading = [tag, []]
        elif tag == "a" and a.get("href"):
            self._link = {"href": urljoin(self.base_url, a["href"]), "text": []}
        elif tag == "img":
            src = a.get("src") or a.get("data-src")
            if src:
                self.images.append({"src": urljoin(self.base_url, src),
                                    "alt": a.get("alt", "")})
        elif tag == "table":
            self._table_stack.append([])
        elif tag == "tr" and self._table_stack:
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell = []
        elif tag in ("br", "p", "div", "li", "section", "article"):
            self.text_parts.append("\n")

    def handle_endtag(self, tag):
        if tag in self.SKIP_TEXT_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)
        elif tag == "title":
            self._in_title = False
        elif tag in self.HEADINGS and self._heading and self._heading[0] == tag:
            text = _clean(" ".join(self._heading[1]))
            if text:
                self.headings.append({"level": tag, "text": text})
            self._heading = None
        elif tag == "a" and self._link is not None:
            self._link["text"] = _clean(" ".join(self._link["text"]))
            self.links.append(self._link)
            self._link = None
        elif tag in ("td", "th") and self._cell is not None and self._row is not None:
            self._row.append(_clean(" ".join(self._cell)))
            self._cell = None
        elif tag == "tr" and self._row is not None and self._table_stack:
            if self._row:
                self._table_stack[-1].append(self._row)
            self._row = None
        elif tag == "table" and self._table_stack:
            table = self._table_stack.pop()
            if table:
                self.tables.append(table)

    def handle_data(self, data):
        if self._skip_depth:
            return
        if self._in_title:
            self.title += data
            return
        self.text_parts.append(data)
        if self._heading is not None:
            self._heading[1].append(data)
        if self._link is not None:
            self._link["text"].append(data)
        if self._cell is not None:
            self._cell.append(data)

    def result(self):
        text = "".join(self.text_parts)
        text = "\n".join(_clean(line) for line in text.splitlines())
        text = re.sub(r"\n{3,}", "\n\n", text).strip()
        return {
            "title": _clean(self.title),
            "meta": self.meta,
            "headings": self.headings,
            "text": text,
            "links": self.links,
            "images": self.images,
            "tables": self.tables,
        }


def _clean(s):
    return re.sub(r"\s+", " ", s).strip()


# --------------------------------------------------------------------------- #
# Fetching
# --------------------------------------------------------------------------- #
def fetch_once(url, timeout):
    """Fetch a URL once. Returns (final_url, status, headers, text). Raises FetchError."""
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.5",
        "Accept-Language": "en;q=0.9,*;q=0.5",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.status
            headers = dict(resp.headers.items())
            ctype = resp.headers.get_content_type()
            if ctype not in ("text/html", "application/xhtml+xml"):
                raise FetchError(f"not HTML (content-type: {ctype})", status=status)

            length = resp.headers.get("Content-Length")
            if length and length.isdigit() and int(length) > MAX_BYTES:
                raise FetchError(f"page too large ({length} bytes)", status=status)
            body = resp.read(MAX_BYTES + 1)
            if len(body) > MAX_BYTES:
                raise FetchError("page too large (> %d bytes)" % MAX_BYTES, status=status)

            charset = resp.headers.get_content_charset() or _sniff_charset(body) or "utf-8"
            try:
                text = body.decode(charset, errors="replace")
            except LookupError:  # unknown charset name
                text = body.decode("utf-8", errors="replace")
            return resp.geturl(), status, headers, text

    except FetchError:
        raise
    except urllib.error.HTTPError as e:
        retry_after = e.headers.get("Retry-After") if e.headers else None
        raise FetchError(f"HTTP {e.code} {e.reason}", status=e.code,
                         retryable=e.code in RETRYABLE_STATUS,
                         retry_after=_parse_retry_after(retry_after))
    except urllib.error.URLError as e:
        reason = e.reason
        if isinstance(reason, ssl.SSLError):
            raise FetchError(f"SSL error: {reason}", retryable=False)
        if isinstance(reason, socket.gaierror):
            raise FetchError(f"DNS lookup failed: {reason}", retryable=True)
        raise FetchError(f"connection error: {reason}", retryable=True)
    except (socket.timeout, TimeoutError):
        raise FetchError(f"timed out after {timeout}s", retryable=True)
    except (ConnectionError, OSError) as e:
        raise FetchError(f"network error: {e}", retryable=True)
    except ValueError as e:  # malformed URL
        raise FetchError(f"invalid URL: {e}")


def fetch(url, timeout, retries):
    """Fetch with exponential backoff on retryable errors."""
    attempt = 0
    while True:
        try:
            return fetch_once(url, timeout)
        except FetchError as e:
            if not e.retryable or attempt >= retries:
                raise
            wait = e.retry_after if e.retry_after is not None else min(2 ** attempt, 30)
            attempt += 1
            log.warning("  retry %d/%d in %.1fs (%s)", attempt, retries, wait, e)
            time.sleep(wait)


def _sniff_charset(body):
    m = re.search(rb'<meta[^>]+charset=["\']?([\w-]+)', body[:4096], re.I)
    return m.group(1).decode("ascii", "ignore") if m else None


def _parse_retry_after(value):
    if value and value.strip().isdigit():
        return min(int(value), 120)
    return None


# --------------------------------------------------------------------------- #
# Crawler
# --------------------------------------------------------------------------- #
def normalize(url):
    url, _ = urldefrag(url)
    p = urlparse(url)
    if p.scheme not in ("http", "https"):
        return None
    path = p.path or "/"
    return p._replace(scheme=p.scheme.lower(), netloc=p.netloc.lower(), path=path).geturl()


def slug_for(url):
    p = urlparse(url)
    base = re.sub(r"[^A-Za-z0-9]+", "_", (p.netloc + p.path).strip("/"))[:80].strip("_")
    digest = hashlib.sha1(url.encode()).hexdigest()[:8]
    return f"{base or 'index'}_{digest}"


def load_robots(start_url, timeout):
    rp = urllib.robotparser.RobotFileParser()
    robots_url = urljoin(start_url, "/robots.txt")
    try:
        req = urllib.request.Request(robots_url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            rp.parse(resp.read().decode("utf-8", errors="replace").splitlines())
        log.info("Loaded %s", robots_url)
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            log.warning("robots.txt returned %d; treating whole site as disallowed", e.code)
            rp.disallow_all = True
        else:
            rp.allow_all = True  # 404 etc. => no restrictions
    except Exception as e:  # network trouble: don't block the crawl on it
        log.warning("Could not read robots.txt (%s); proceeding without it", e)
        rp.allow_all = True
    return rp


def write_json(path, data):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)  # atomic: never leaves a half-written file


def crawl(args):
    out = Path(args.output)
    (out / "html").mkdir(parents=True, exist_ok=True)
    (out / "pages").mkdir(parents=True, exist_ok=True)

    start = normalize(args.url)
    if not start:
        raise SystemExit(f"error: URL must start with http:// or https:// (got {args.url!r})")
    domain = urlparse(start).netloc

    robots = None if args.ignore_robots else load_robots(start, args.timeout)

    queue = deque([(start, 0)])
    seen = {start}
    index, errors = [], []
    saved_hashes = {}  # content hash -> URL, to skip identical pages (e.g. / vs /index.html)
    ok_count = 0

    def record_error(url, depth, reason, status=None):
        log.error("  FAILED: %s", reason)
        entry = {"url": url, "depth": depth, "status": status, "error": reason,
                 "time": datetime.now(timezone.utc).isoformat()}
        errors.append(entry)
        index.append({**entry, "ok": False})

    try:
        while queue and ok_count < args.max_pages:
            url, depth = queue.popleft()
            log.info("[%d/%d] depth=%d %s", ok_count + 1, args.max_pages, depth, url)

            if robots and not robots.can_fetch(USER_AGENT, url):
                record_error(url, depth, "blocked by robots.txt")
                continue

            try:
                final_url, status, headers, html = fetch(url, args.timeout, args.retries)
            except FetchError as e:
                record_error(url, depth, str(e), e.status)
                time.sleep(args.delay)
                continue

            content_hash = hashlib.sha1(html.encode("utf-8", "replace")).hexdigest()
            if content_hash in saved_hashes:
                log.info("  duplicate of %s - skipped", saved_hashes[content_hash])
                index.append({"url": url, "final_url": final_url, "status": status,
                              "depth": depth, "ok": True,
                              "duplicate_of": saved_hashes[content_hash]})
                time.sleep(args.delay)
                continue
            saved_hashes[content_hash] = final_url

            try:
                parser = PageParser(final_url)
                parser.feed(html)
                parser.close()
                data = parser.result()
            except Exception as e:  # malformed HTML should never kill the crawl
                log.exception("  parse error")
                data = {"parse_error": f"{type(e).__name__}: {e}"}

            slug = slug_for(final_url)
            try:
                (out / "html" / f"{slug}.html").write_text(html, encoding="utf-8")
                page = {
                    "url": url,
                    "final_url": final_url,
                    "status": status,
                    "depth": depth,
                    "fetched_at": datetime.now(timezone.utc).isoformat(),
                    "headers": headers,
                    **data,
                }
                write_json(out / "pages" / f"{slug}.json", page)
            except OSError as e:
                record_error(url, depth, f"could not save to disk: {e}", status)
                continue

            ok_count += 1
            index.append({"url": url, "final_url": final_url, "status": status,
                          "depth": depth, "ok": True, "title": data.get("title", ""),
                          "file": f"pages/{slug}.json"})
            log.info("  saved: %r (%d links, %d images, %d tables)",
                     data.get("title", "")[:60], len(data.get("links", [])),
                     len(data.get("images", [])), len(data.get("tables", [])))

            if depth < args.depth:
                for link in data.get("links", []):
                    nxt = normalize(link["href"])
                    if (nxt and nxt not in seen
                            and urlparse(nxt).netloc == domain
                            and not urlparse(nxt).path.lower().endswith(SKIP_EXTENSIONS)):
                        seen.add(nxt)
                        queue.append((nxt, depth + 1))

            time.sleep(args.delay)

    except KeyboardInterrupt:
        log.warning("Interrupted by user - saving progress...")
    finally:
        write_json(out / "index.json", {
            "start_url": start,
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "pages_saved": ok_count,
            "pages_failed": len(errors),
            "pages_not_visited": len(queue),
            "pages": index,
        })
        write_json(out / "errors.json", errors)
        log.info("Done: %d saved, %d failed, %d left in queue. Output: %s",
                 ok_count, len(errors), len(queue), out.resolve())

    return 0 if ok_count else 1


def main():
    ap = argparse.ArgumentParser(description="Crawl a website and save all page data.")
    ap.add_argument("url", help="start URL, e.g. https://example.com")
    ap.add_argument("-o", "--output", default="scraped_data", help="output directory")
    ap.add_argument("--max-pages", type=int, default=50, help="max pages to save (default 50)")
    ap.add_argument("--depth", type=int, default=2, help="max link depth from start (default 2)")
    ap.add_argument("--delay", type=float, default=1.0, help="seconds between requests (default 1)")
    ap.add_argument("--timeout", type=float, default=15, help="request timeout in seconds")
    ap.add_argument("--retries", type=int, default=3, help="retries for transient errors")
    ap.add_argument("--ignore-robots", action="store_true", help="do not check robots.txt")
    args = ap.parse_args()

    Path(args.output).mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-7s %(message)s",
        datefmt="%H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout),
                  logging.FileHandler(Path(args.output) / "scrape.log", encoding="utf-8")],
    )
    sys.exit(crawl(args))


if __name__ == "__main__":
    main()
