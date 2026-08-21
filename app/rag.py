from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CORPUS = ROOT / "knowledge_base" / "processed" / "chunks.json"
DEFAULT_INDEX = ROOT / "data" / "index.npz"

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

    def _load(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def encode(self, texts: list[str]) -> np.ndarray:
        model = self._load()
        vectors = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return np.asarray(vectors, dtype=np.float32)

class Retriever:
    def __init__(self, corpus_path: str | Path = DEFAULT_CORPUS, index_path: str | Path = DEFAULT_INDEX):
        self.corpus_path = Path(corpus_path)
        self.index_path = Path(index_path)
        raw = json.loads(self.corpus_path.read_text(encoding="utf-8"))
        self.chunks = [Chunk(**item) for item in raw]
        self.embedder = Embedder()
        self.embeddings = None
        if self.index_path.exists():
            try:
                data = np.load(self.index_path)
                matrix = data["embeddings"]
                if matrix.shape[0] == len(self.chunks):
                    self.embeddings = matrix
            except Exception:
                self.embeddings = None
        if self.embeddings is None:
            self.embeddings = self.embedder.encode([c.text for c in self.chunks])
            self.index_path.parent.mkdir(parents=True, exist_ok=True)
            np.savez_compressed(self.index_path, embeddings=self.embeddings)

    def search(self, query: str, top_k: int = 5) -> list[tuple[Chunk, float]]:
        query_embedding = self.embedder.encode([query])[0]
        scores = self.embeddings @ query_embedding
        # Add a small lexical signal so exact hotel terms such as “Chutney”, “Sky Lounge”,
        # “0824-2497101”, and room-category names are not lost among generic hospitality copy.
        query_terms = {term.lower() for term in re.findall(r"[a-zA-Z0-9-]+", query) if len(term) > 2}
        lexical = np.array([sum(term in chunk.text.lower() for term in query_terms) for chunk in self.chunks], dtype=np.float32)
        if lexical.max() > 0:
            lexical = lexical / lexical.max()
        scores = scores + 0.12 * lexical
        indices = np.argsort(scores)[::-1][:top_k]
        return [(self.chunks[int(i)], float(scores[int(i)])) for i in indices]

class LLMProvider:
    def answer(self, question: str, contexts: list[tuple[Chunk, float]]) -> str:
        raise NotImplementedError

class ExtractiveProvider(LLMProvider):
    """No-key fallback that returns grounded, citation-like snippets."""
    def answer(self, question: str, contexts: list[tuple[Chunk, float]]) -> str:
        if not contexts:
            return "I could not find that in the official Hotel Deepa Comforts website content. Please contact the hotel directly at 0824-2497101."
        query_terms = {term.lower() for term in re.findall(r"[a-zA-Z0-9]+", question) if len(term) > 2}
        selected: list[str] = []
        for chunk, score in contexts:
            sentences = re.split(r"(?<=[.!?])\s+", chunk.text)
            ranked = sorted(sentences, key=lambda s: sum(t in s.lower() for t in query_terms), reverse=True)
            if ranked and ranked[0].strip():
                selected.append(ranked[0].strip())
        body = " ".join(dict.fromkeys(selected[:3]))
        sources = "; ".join(f"{c.title} ({c.url})" for c, _ in contexts[:3])
        return f"{body}\n\nSource: {sources}"

class OpenAICompatibleProvider(LLMProvider):
    def __init__(self):
        from openai import OpenAI
        self.client = OpenAI(api_key=os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY"), base_url=os.getenv("LLM_BASE_URL") or os.getenv("OPENAI_API_BASE"))
        self.model = os.getenv("LLM_MODEL", "gpt-4o-mini")

    def answer(self, question: str, contexts: list[tuple[Chunk, float]]) -> str:
        context_text = "\n\n".join(f"[{i}] {c.title}\n{c.text}\nURL: {c.url}" for i, (c, _) in enumerate(contexts, 1))
        system = ("You are the official Hotel Deepa Comforts information assistant. Answer only from the supplied official website context. "
                  "If the answer is not present, say so and direct the guest to call 0824-2497101. Never invent rates, timings, policies, availability, capacities, or phone numbers. "
                  "Mention when the website does not publish a requested detail. Keep answers concise and cite source URLs inline.")
        response = self.client.chat.completions.create(model=self.model, temperature=0.1, max_tokens=500, messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": f"Official context:\n{context_text}\n\nGuest question: {question}"},
        ])
        return response.choices[0].message.content or ExtractiveProvider().answer(question, contexts)

def make_provider() -> LLMProvider:
    provider = os.getenv("LLM_PROVIDER", "extractive").lower()
    if provider in {"openai", "openai-compatible", "api"} and (os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")):
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
        results = self.retriever.search(question, top_k=top_k)
        answer = self.provider.answer(question, results)
        return {"answer": answer, "sources": [{"title": c.title, "url": c.url, "score": round(score, 4), "text": c.text} for c, score in results]}
