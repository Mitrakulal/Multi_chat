"""Minimal local adapter for the static UI. Run with: uvicorn api:app --port 8000"""
import json
import os
import sys
from pathlib import Path
from fastapi import FastAPI
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).parent))
from app.rag import HotelRAG

app = FastAPI(title="Hotel RAG Demo API")
rag = HotelRAG()


class Query(BaseModel):
    question: str


@app.post("/api/ask")
def ask(q: Query):
    return rag.ask(q.question)
