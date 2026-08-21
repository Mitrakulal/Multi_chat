import re
from pathlib import Path

import requests

BASE = "https://www.hoteldeepacomforts.com/"
PATHS = [
    "accommodations",
    "accommodations?name=suite",
    "accommodations?name=premium",
    "accommodations?name=deluxe",
    "restaurants?name=chutney",
    "gallery",
    "contact-us",
]
OUTPUT_FILE = Path(__file__).resolve().parents[1] / "knowledge_base" / "raw" / "payload_inspection.txt"

rows = []
for path in PATHS:
    url = BASE + path
    response = requests.get(url, headers={"User-Agent": "HotelDeepaComfortsRAG/1.0"}, timeout=30)
    rows.append(f"URL: {url}\nSTATUS: {response.status_code}\nBYTES: {len(response.text)}\n")
    for needle in ["suite", "premium", "deluxe", "banquet", "chutney", "policy", "timing", "airport", "room"]:
        matches = list(re.finditer(needle, response.text, re.IGNORECASE))
        rows.append(f"  {needle}: {len(matches)} occurrences\n")
        for match in matches[:3]:
            start = max(0, match.start() - 180)
            end = min(len(response.text), match.end() + 280)
            snippet = re.sub(r"\s+", " ", response.text[start:end])[:500]
            rows.append(f"    {snippet}\n")
    rows.append("\n" + "=" * 80 + "\n")

OUTPUT_FILE.write_text("".join(rows), encoding="utf-8")
print(OUTPUT_FILE)

