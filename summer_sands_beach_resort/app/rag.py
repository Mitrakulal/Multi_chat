from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "hotel_config.json").read_text(encoding="utf-8"))
CORPUS = ROOT / "knowledge_base" / "processed" / "chunks.json"
INDEX = ROOT / "data" / "index.npz"


@dataclass
class Chunk:
    id: str
    title: str
    text: str
    url: str
    source_type: str = "website"


class Embedder:
    def __init__(self, model_name: str | None = None):
        self.model_name = model_name or os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        self._model = None

    def encode(self, texts: list[str]) -> np.ndarray:
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
        return np.asarray(self._model.encode(texts, normalize_embeddings=True, show_progress_bar=False), dtype=np.float32)


class Retriever:
    def __init__(self):
        self.chunks = [Chunk(**x) for x in json.loads(CORPUS.read_text(encoding="utf-8"))]
        self.embedder = Embedder()
        self.embeddings = None
        if INDEX.exists():
            try:
                a = np.load(INDEX)["embeddings"]
                if a.shape[0] == len(self.chunks):
                    self.embeddings = a
            except Exception:
                pass
        if self.embeddings is None:
            self.embeddings = self.embedder.encode([c.text for c in self.chunks])
            INDEX.parent.mkdir(exist_ok=True)
            np.savez_compressed(INDEX, embeddings=self.embeddings)

    def search(self, query: str, top_k: int = 5) -> list[tuple[Chunk, float]]:
        q = self.embedder.encode([query])[0]
        scores = self.embeddings @ q
        terms = {t.lower() for t in re.findall(r"[a-zA-Z0-9-]+", query) if len(t) > 2}
        lexical = np.array([sum(t in c.text.lower() for t in terms) for c in self.chunks], dtype=np.float32)
        if lexical.max() > 0:
            scores = scores + 0.12 * lexical / lexical.max()
        return [(self.chunks[int(i)], float(scores[int(i)])) for i in np.argsort(scores)[::-1][:top_k]]


class ExtractiveProvider:
    def answer(self, question: str, contexts: list[tuple[Chunk, float]]) -> str:
        if not contexts:
            return f"I could not find that in the approved {CONFIG['name']} content. Please contact the hotel through its official channels."
        terms = {t.lower() for t in re.findall(r"[a-zA-Z0-9-]+", question) if len(t) > 2}
        selected = []
        for chunk, _ in contexts:
            sentences = re.split(r"(?<=[.!?])\s+", chunk.text)
            ranked = sorted(sentences, key=lambda s: sum(t in s.lower() for t in terms), reverse=True)
            if ranked and ranked[0].strip():
                selected.append(ranked[0].strip())
        body = " ".join(dict.fromkeys(selected[:3]))
        sources = "; ".join(f"{c.title} ({c.url})" for c, _ in contexts[:3])
        return f"{body}\n\nSource: {sources}"


class OpenAICompatibleProvider:
    def __init__(self):
        from openai import OpenAI

        self.client = OpenAI(
            api_key=os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("LLM_BASE_URL") or os.getenv("OPENAI_API_BASE"),
        )
        self.model = os.getenv("LLM_MODEL")
        if not self.model:
            raise RuntimeError("Set LLM_MODEL to enable the configurable LLM provider.")

    def answer(self, question: str, contexts: list[tuple[Chunk, float]]) -> str:
        context = "\n\n".join(f"[{i}] {c.title}\n{c.text}\nURL: {c.url}" for i, (c, _) in enumerate(contexts, 1))
        system = (
            f"You are the approved information assistant for {CONFIG['name']}. Answer only from the supplied context. "
            "If absent, say so. Never invent rates, availability, policies, capacities, timings, payment instructions or contact details. "
            "Mention website gaps and cite source URLs."
        )
        r = self.client.chat.completions.create(
            model=self.model,
            temperature=0.1,
            max_tokens=500,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": f"Approved context:\n{context}\n\nGuest question: {question}"},
            ],
        )
        return r.choices[0].message.content or ExtractiveProvider().answer(question, contexts)


def make_provider():
    if os.getenv("LLM_PROVIDER", "extractive").lower() in {"openai", "openai-compatible", "api"} and (
        os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
    ):
        try:
            return OpenAICompatibleProvider()
        except Exception:
            pass
    return ExtractiveProvider()


class HotelRAG:
    def __init__(self):
        self.retriever = Retriever()
        self.provider = make_provider()

    def ask(self, question: str, top_k: int = 5) -> dict[str, Any]:
        results = self.retriever.search(question, top_k)
        return {
            "answer": self.provider.answer(question, results),
            "sources": [
                {
                    "title": c.title,
                    "url": c.url,
                    "score": round(s, 4),
                    "text": c.text,
                }
                for c, s in results
            ],
        }
