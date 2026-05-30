# 🎬 YouTube Q&A Chatbot — Backend

> Backend for a YouTube Q&A chatbot built to showcase LangChain RAG concepts — transcript ingestion, FAISS vector search, conversational memory, and a FastAPI REST API designed for Chrome Extension integration.

---

## 📌 Overview

This is the backend service for a YouTube Q&A Chrome Extension. Given any YouTube video, it fetches the transcript, builds a vector search index, and lets users ask questions about the video in a conversational way — with full chat history support per session.

Each user session gets isolated memory, while the FAISS vector store is shared across users watching the same video — so the transcript is only embedded once per video regardless of how many users are asking questions.

---

## 🧠 Concepts Covered

- **RAG (Retrieval-Augmented Generation)** — retrieve relevant transcript chunks before answering
- **FAISS Vector Store** — in-memory vector search for fast chunk retrieval
- **Conversational Memory** — per-session chat history stored in a simple dict
- **Question Rewriting** — condenses follow-up questions into standalone questions using chat history before hitting FAISS
- **LCEL (LangChain Expression Language)** — building chains using the modern `|` pipe syntax
- **FastAPI** — async REST API with auto-generated Swagger docs

---

## 🗂️ Project Structure

```
backend/
├── main.py              # FastAPI app, routes, cache management
├── rag_pipeline.py      # LangChain RAG logic — vectorstore, retrieval, answering
├── transcript.py        # YouTube transcript fetcher
├── pyproject.toml       # Dependencies
├── .env                 # API keys (not committed)
└── README.md
```

---

## ⚙️ How It Works

```
POST /ask  (video_id + question + session_id)
        │
        ▼
1. Fetch YouTube transcript (cached per video)
        │
        ▼
2. Chunk → Embed → Store in FAISS (cached per video, shared across users)
        │
        ▼
3. If chat history exists → rewrite question as standalone using LLM
        │
        ▼
4. Retrieve top-k relevant chunks from FAISS
        │
        ▼
5. Answer using context + chat history (isolated per session)
        │
        ▼
6. Save (question, answer) to session memory
        │
        ▼
        Return answer
```

### Caching Strategy

| Cache | Key | Shared? |
|---|---|---|
| `vectorstore_cache` | `video_id` | ✅ Shared across all users |
| `message_store` | `session_id:video_id` | ❌ Isolated per user |

100 users watching the same video = **1 vectorstore** but **100 separate memory stores for chat history**.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| API Framework | FastAPI |
| LLM | OpenAI GPT-3.5-turbo |
| Embeddings | OpenAI Embeddings |
| Vector Store | FAISS (in-memory) |
| RAG Framework | LangChain (LCEL) |
| Transcript | youtube-transcript-api |
| Runtime | Python 3.13 |
| Package Manager | uv |

---

## 🚀 Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/jishnusaha/youtube-chatbot-ext-backend.git
cd youtube-chatbot-ext-backend
```

### 2. Install dependencies

```bash
uv sync
```

### 3. Set up environment variables

Create a `.env` file in the root:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

### 4. Run the server

```bash
uv run uvicorn main:app --reload
```

Server runs at `http://localhost:8000`

### 5. Open Swagger UI

Visit `http://localhost:8000/docs` to explore and test the API interactively.

---

## 📡 API Reference

### `POST /ask`

Ask a question about a YouTube video.

**Request Body**

```json
{
  "video_id": "dQw4w9WgXcQ",
  "question": "What is this video about?",
  "session_id": "unique-session-id"
}
```

**Response**

```json
{
  "answer": "This video is about..."
}
```

| Field | Type | Description |
|---|---|---|
| `video_id` | string | YouTube video ID (from the URL) |
| `question` | string | Question to ask about the video |
| `session_id` | string | Unique ID per user session for isolated memory |

---

### `GET /health`

Health check endpoint.

```json
{ "status": "ok" }
```

---

## 🧪 Test with curl

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "video_id": "dQw4w9WgXcQ",
    "question": "What is this video about?",
    "session_id": "test-session-001"
  }'
```

---

## ⚠️ Limitations

- **In-memory only** — all vectorstores and chat history are lost on server restart
- **No authentication** — `session_id` is trust-based, not verified
- **OpenAI cost** — every question makes 1-2 LLM calls (rewrite + answer)
- **Transcript availability** — only works for videos with captions/transcripts enabled

---

## 🗺️ Future Improvements

- [ ] Persist vectorstores with Pinecone or pgvector
- [ ] Persist chat history with Redis
- [ ] Add rate limiting per session

---
