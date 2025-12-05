# NoobBook

An educational NotebookLM clone built to teach AI/LLM integration patterns.

---

## What is NoobBook?

LocalMind is a learning project that demonstrates real-world AI/LLM use cases. Every service and file demonstrates an AI concept - not generic web development patterns.

**What you'll learn:**
- LLM API integration (Claude, OpenAI, Gemini)
- Prompt engineering and tool definitions
- Agentic loops and multi-step reasoning
- RAG pipeline with embeddings and citations
- Multi-modal AI (vision, audio, text-to-speech)
- Background task processing

**What we intentionally skip:** Authentication, databases, payments, production security. This is purely for learning LLMs.

---

## How It Works

LocalMind has 4 main concepts:

### 1. Projects

Everything is organized into projects. Each project has its own sources, chats, and studio outputs. Projects are stored as JSON files in `data/projects/`.

### 2. Sources (Left Panel)

Upload documents and the system processes them for AI understanding:

| Source Type | Processing |
|-------------|------------|
| PDF | AI vision extracts text page by page |
| DOCX | Python extraction |
| PPTX | Convert to PDF, then vision extraction |
| Images | AI vision describes content |
| Audio | ElevenLabs transcription |
| YouTube | Transcript API |
| URLs | Web agent fetches and extracts content |
| Text | Direct input |

**Processing Pipeline:**
```
Upload -> Raw file saved -> AI extracts text -> Chunked for RAG -> Embedded in Pinecone
```

Sources with 2500+ tokens get embeddings for semantic search. Smaller sources are searched directly.

### 3. Chat (Center Panel)

RAG-powered Q&A with your sources:

```
User question
    -> AI searches relevant sources (hybrid: keyword + semantic)
    -> AI generates response with citations
    -> Citations link to specific chunks
```

**Key features:**
- Chunk-based citations `[[cite:source_chunk_id]]`
- Memory system (user preferences + project context)
- Voice input via ElevenLabs WebSocket
- Conversation history per chat

### 4. Studio (Right Panel)

Generate content from your sources using AI agents:

| Category | Studio Items |
|----------|--------------|
| **Audio/Video** | Audio Overview, Video Generation |
| **Learning** | Flash Cards, Mind Maps, Quizzes |
| **Documents** | PRD, Blog Posts, Business Reports, Presentations |
| **Marketing** | Ad Creatives, Social Posts, Email Templates, Marketing Strategy |
| **Design** | Websites, Components, Wireframes, Flow Diagrams, Infographics |

**How Studio works:**
1. Main chat AI detects when to trigger studio generation
2. Sends a "signal" with context (source_ids, direction, etc.)
3. Specialized agent generates the content
4. Output saved and displayed in Studio panel

---

## Architecture Overview

```
Frontend (React + Vite)
    |
    v
Backend API (Flask)
    |
    ├── Source Processing (upload, extract, chunk, embed)
    ├── Chat Service (RAG search, Claude API, citations)
    ├── Studio Services (content generation agents)
    └── Integrations (Claude, OpenAI, Pinecone, ElevenLabs, Gemini)
    |
    v
Data Storage (JSON files in /data)
```

**AI Services Used:**
- **Claude** - Main LLM for chat, agents, content generation
- **OpenAI** - Embeddings for vector search
- **Pinecone** - Vector database for RAG
- **ElevenLabs** - Text-to-speech and transcription
- **Gemini** - Image generation (ads, infographics)
- **Google Veo** - Video generation

---

## Running the Project

### Prerequisites

Install these system dependencies:

```bash
# macOS
brew install libreoffice
brew install ffmpeg
npx playwright install

# Ubuntu/Debian
sudo apt install libreoffice ffmpeg
npx playwright install

# Windows
# Download and install LibreOffice, FFmpeg manually
npx playwright install
```

### Backend Setup

```bash
cd Localmind/backend

# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run backend
python run.py
```

### Frontend Setup

```bash
cd Localmind/frontend

# Install dependencies
npm install

# Run frontend
npm run dev
```

### API Keys

API keys are configured directly from the **Dashboard -> Project Settings** in the app.

Required keys:
- `ANTHROPIC_API_KEY` - Claude API
- `OPENAI_API_KEY` - Embeddings
- `PINECONE_API_KEY` + `PINECONE_INDEX_NAME` - Vector database

Optional keys (for extra features):
- `ELEVENLABS_API_KEY` - Audio overview, voice input
- `NANO_BANANA_API_KEY` - Gemini image generation
- `VEO_API_KEY` - Video generation
- `TAVILY_API_KEY` - Web search fallback
- `GOOGLE_CLIENT_ID` + `GOOGLE_CLIENT_SECRET` - Google Drive import

### Access the App

Open http://localhost:5173

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React + Vite + TypeScript |
| UI | shadcn/ui + Tailwind CSS |
| Icons | Phosphor Icons |
| Backend | Python Flask |
| AI/LLM | Claude (Anthropic), OpenAI Embeddings |
| Vector DB | Pinecone |
| Audio | ElevenLabs (TTS + Transcription) |
| Image Gen | Google Gemini |
| Video Gen | Google Veo 2.0 |
| Storage | JSON files |

---

## License

Only for learning purposes, if you plan to commercialise a copy or ideas from the project best of luck, enjoy
