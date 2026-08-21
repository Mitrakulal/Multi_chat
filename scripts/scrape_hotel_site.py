from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

BASE = "https://www.hoteldeepacomforts.com/"
OUT = Path(__file__).resolve().parents[1] / "knowledge_base" / "raw"
OUT.mkdir(parents=True, exist_ok=True)

session = requests.Session()
session.headers.update({"User-Agent": "HotelDeepaComfortsRAG/1.0 (+public-site-corpus)"})

seed_urls = [BASE, urljoin(BASE, "about"), urljoin(BASE, "services"), urljoin(BASE, "gallery"), urljoin(BASE, "contact-us")]
for name in ("robots.txt", "sitemap.xml"):
    try:
        response = session.get(urljoin(BASE, name), timeout=30)
        (OUT / name).write_text(response.text, encoding="utf-8")
        if response.ok and name == "sitemap.xml":
            soup = BeautifulSoup(response.text, "xml")
            seed_urls.extend(loc.get_text(strip=True) for loc in soup.find_all("loc"))
    except requests.RequestException as exc:
        (OUT / f"{name}.error.txt").write_text(str(exc), encoding="utf-8")

# Discover internal links from known HTML pages, including query-string accommodation pages.
for url in list(seed_urls):
    try:
        response = session.get(url, timeout=30)
        if response.ok and "text/html" in response.headers.get("content-type", ""):
            soup = BeautifulSoup(response.text, "html.parser")
            for anchor in soup.find_all("a", href=True):
                candidate = urljoin(url, anchor["href"])
                parsed = urlparse(candidate)
                if parsed.netloc == urlparse(BASE).netloc:
                    seed_urls.append(candidate)
    except requests.RequestException:
        continue

# De-duplicate while preserving order and keep only public HTTP(S) pages on the hotel domain.
urls = []
seen = set()
for url in seed_urls:
    parsed = urlparse(url)
    normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path or '/'}"
    if parsed.query:
        normalized += f"?{parsed.query}"
    if parsed.netloc == urlparse(BASE).netloc and normalized not in seen and parsed.scheme in {"http", "https"}:
        seen.add(normalized)
        urls.append(normalized)

records = []
for index, url in enumerate(urls, start=1):
    try:
        response = session.get(url, timeout=30)
        content_type = response.headers.get("content-type", "")
        if response.status_code >= 400 or "text/html" not in content_type:
            continue
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "noscript", "svg"]):
            tag.decompose()
        title = soup.title.get_text(" ", strip=True) if soup.title else ""
        text = "\n".join(line.strip() for line in soup.get_text("\n").splitlines() if line.strip())
        links = sorted({urljoin(url, a.get("href")) for a in soup.find_all("a", href=True)})
        images = sorted({urljoin(url, img.get("src")) for img in soup.find_all("img", src=True)})
        slug = re.sub(r"[^a-zA-Z0-9._-]+", "_", url.replace("https://", "").replace("http://", "").strip("/")) or "homepage"
        record = {
            "url": url,
            "status_code": response.status_code,
            "title": title,
            "text": text,
            "links": links,
            "images": images,
        }
        records.append(record)
        (OUT / f"{slug}.json").write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    except requests.RequestException as exc:
        records.append({"url": url, "error": str(exc)})

(OUT / "site_manifest.json").write_text(json.dumps({"base_url": BASE, "pages": records}, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps({"discovered_urls": len(urls), "scraped_pages": sum("text" in record for record in records), "output": str(OUT)}, indent=2))
