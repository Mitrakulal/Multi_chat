# Hotel BMS RAG demo

Open `web/index.html` directly for the static hotel-background/chatbot mockup. For grounded live answers, install `requirements.txt`, run `uvicorn api:app --port 8000`, and serve the `web/` directory from the same origin or configure a reverse proxy for `/api/ask`.

The UI uses the hotel's official URL as an iframe background when available; browser security headers may prevent framing, in which case the branded fallback background remains visible. The corpus is in `knowledge_base/processed/chunks.json`. The RAG provider is pluggable through `LLM_PROVIDER`, `LLM_MODEL`, `LLM_API_KEY`, and `LLM_BASE_URL`, with an extractive fallback. Never invent rates, availability, payments, capacities or unverified policies.
