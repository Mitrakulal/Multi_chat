import json
from pathlib import Path

from app.rag import ExtractiveProvider

ROOT = Path(__file__).resolve().parents[1]


def test_corpus_contains_expected_hotel_topics():
    chunks = json.loads((ROOT / "knowledge_base/processed/chunks.json").read_text())
    corpus = " ".join(chunk["text"] for chunk in chunks).lower()
    for term in ["suite", "premium", "deluxe", "chutney", "shehnai", "senate", "travel desk", "airport", "0824-2497101"]:
        assert term in corpus


def test_extractive_provider_is_grounded():
    chunks = json.loads((ROOT / "knowledge_base/processed/chunks.json").read_text())
    objects = [type("Chunk", (), chunk)() for chunk in chunks]
    answer = ExtractiveProvider().answer("What rooms do you have?", [(objects[0], 0.9), (objects[1], 0.8)])
    assert answer
    assert "Source:" in answer


def test_coverage_note_mentions_unpublished_operational_details():
    chunks = json.loads((ROOT / "knowledge_base/processed/chunks.json").read_text())
    gaps = " ".join(chunk["text"] for chunk in chunks if chunk["source_type"] == "coverage_note").lower()
    assert "restaurant opening and closing times" in gaps
    assert "room rates" in gaps
    assert "airport distance" in gaps
