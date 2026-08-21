from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "knowledge_base" / "raw"
OUT = ROOT / "knowledge_base" / "processed"
OUT.mkdir(parents=True, exist_ok=True)

# The official site does not publish every operational detail requested by guests.
# These notes are intentionally explicit so the assistant does not hallucinate.
GAPS = {
    "title": "Official website coverage and published-data gaps",
    "url": "https://www.hoteldeepacomforts.com/",
    "text": (
        "The official website lists room categories Suite, Premium, and Deluxe, but the scraped public page text does not publish room rates, occupancy, bed configuration, room-size measurements, or live availability. "
        "The official website describes Chutney and states that food service covers breakfast, lunch, and dinner, but it does not publish restaurant opening and closing times in the scraped content. "
        "The official website describes banquet venues and event support, but it does not publish hall-wise capacities, package prices, or a step-by-step booking form in the scraped content. "
        "The official website describes airport pickup and drop-off through its travel desk, but it does not publish an airport distance, fixed fare, or route estimate. "
        "No separate cancellation, check-in, check-out, payment, or general guest policy text was found on the discovered public pages. For any unpublished operational detail, contact the hotel through the official channels."
    ),
}


def clean(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text


def chunk_text(text: str, max_chars: int = 900, overlap: int = 120) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n+", text) if p.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        paragraph = clean(paragraph)
        if not paragraph:
            continue
        if current and len(current) + len(paragraph) + 1 > max_chars:
            chunks.append(current)
            current = current[-overlap:] + " " + paragraph
        else:
            current = (current + " " + paragraph).strip()
    if current:
        chunks.append(current)
    return chunks

records = []
for path in sorted(RAW.glob("*.json")):
    if path.name in {"site_manifest.json"}:
        continue
    record = json.loads(path.read_text(encoding="utf-8"))
    if not record.get("text"):
        continue
    url = record["url"]
    title = record.get("title") or url
    # Remove repeated navigation/footer boilerplate while retaining meaningful facts.
    text = record["text"]
    text = re.sub(r"Home \| Hotel Deepa Comforts|About \| Hotel Deepa Comforts|Services \| Hotel Deepa Comforts|Gallery \| Hotel Deepa Comforts|Contact Us \| Hotel Deepa Comforts|Restaurants \| Hotel Deepa Comforts|Banquet Halls \| Hotel Deepa Comforts", "", text)
    text = re.sub(r"Home About Amenities Services Gallery Contact Us", "", text)
    text = re.sub(r"Contact Details Luxury Business Hotel, M\\.G\\. ROAD, Mangalore - 575 003, Karnataka, India\\. info@hoteldeepacomforts\\.com 0824 411 7101 / 02 / 03 0824 249 7101 / 02 / 03 Booking Celebration Conference Leisure Contact Us ©Deepa comforts, 2024\\. All Rights Reserved\\.", "", text)
    text = re.sub(r"We have identified a fraudulent activity.*?0824-2497101\\.", "", text, flags=re.IGNORECASE)
    text = re.sub(r"Contact Details.*?©Deepa comforts, 2024\\. All Rights Reserved\\.", "", text, flags=re.IGNORECASE)
    for i, part in enumerate(chunk_text(text)):
        records.append({"id": f"{path.stem}-{i}", "title": title, "text": part, "url": url, "source_type": "official_website"})

faq_chunks = [
    ("FAQ — room categories", "The official Hotel Deepa Comforts website shows three accommodation categories: Suite, Premium, and Deluxe. It also lists centralized AC, breakfast, WiFi, safety lockers, room service, mini refrigerator, laundry, and valet parking as amenities. The website does not publish rates, occupancy, bed configuration, room size, or live availability in the scraped content."),
    ("FAQ — banquet enquiry", "Hotel Deepa Comforts describes two high-capacity banquet halls, Shehnai and Senate, three customizable medium-capacity halls, Moments, Baithak, and Board Room, and a very large-capacity open-air terrace venue, Sky Lounge. The venue offers in-house catering and dedicated event planning. To enquire or book, contact the hotel through its official channels at 0824 249 7101 / 02 / 03 or 0824 411 7101 / 02 / 03, or info@hoteldeepacomforts.com. The website does not publish hall-wise capacities or package prices."),
    ("FAQ — Chutney timing", "Chutney is described on the official Hotel Deepa Comforts website as a vegetarian Pan-Indian dining destination. The website says the hotel serves breakfast, lunch, and dinner, but the scraped public content does not publish exact restaurant opening and closing times. Ask the hotel directly for today’s timing."),
    ("FAQ — airport travel", "Hotel Deepa Comforts’ travel desk offers airport pick-up and drop-off, city sightseeing, air-ticket reconfirmation, car rentals, reservations outside Mangalore, and multilingual guides on request. The official website does not publish airport distance, route duration, or a fixed transfer fare, so contact the travel desk or hotel directly for current arrangements."),
    ("FAQ — official phone and fraud warning", "The official Hotel Deepa Comforts website warns that an unauthorized person added a mobile number to its Google Maps listing and accepted room-booking payments under false pretenses. It says to book through official channels and gives 0824-2497101 for reservations. The website footer also lists 0824 411 7101 / 02 / 03 and 0824 249 7101 / 02 / 03. Guests should verify any number against the official website before paying."),
]
for i, (title, text) in enumerate(faq_chunks):
    records.append({"id": f"faq-{i}", "title": title, "text": text, "url": GAPS["url"], "source_type": "official_website_normalized"})

for i, part in enumerate(chunk_text(GAPS["text"])):
    records.append({"id": f"coverage-gaps-{i}", "title": GAPS["title"], "text": part, "url": GAPS["url"], "source_type": "coverage_note"})

(OUT / "chunks.json").write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
summary = {
    "source": "https://www.hoteldeepacomforts.com/",
    "scraped_at": "2026-08-19",
    "source_pages": len({r["url"] for r in records if r["source_type"] == "official_website"}),
    "chunk_count": len(records),
    "embedding_model_default": "sentence-transformers/all-MiniLM-L6-v2",
    "coverage_note": "Explicitly records website data gaps to prevent fabricated answers.",
}
(OUT / "README.md").write_text("# Hotel Deepa Comforts knowledge base\n\nThis directory contains cleaned retrieval chunks derived from the official Hotel Deepa Comforts website, plus an explicit coverage note for operational details not published in the scraped pages. The source manifest and raw page JSON are in `../raw/`.\n\n" + json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2))
