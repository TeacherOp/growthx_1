# NoobBook

**NotebookLM, but make it noob-friendly.**

> **Codebase Cleanup In-progress** - Live demo sessions completed. Code cleanup in progress. Do not use current code - its incomplete - wait for commit - "NoobBook now Live"

---

## What is NoobBook?
Gugal's Dream
NoobBook is an educational project designed to teach **all possible AI/LLM API use cases** through building a full-featured NotebookLM clone. Built by noobs, for noobs. Every service, every file demonstrates a real AI/LLM concept - not generic web development patterns.
Not a single line of code write by hand only enter enter because tab is for developers, we love ClaudeCode Pro Max
And you can't even code this, buddy forget VibeCode

## What You'll Learn

| Concept | Implementation |
|---------|----------------|
| **LLM API Integration** | Claude, OpenAI, Gemini API patterns |
| **Prompt Engineering** | System prompts, tool definitions, JSON configs |
| **Tool Use & Agents** | Agentic loops, tool execution, multi-step reasoning |
| **RAG Pipeline** | Embeddings, vector search, chunk-based citations |
| **Multi-Modal AI** | Vision (PDF/Image), Audio transcription, Text-to-Speech |
| **Real-time AI** | WebSocket streaming, background task processing |

## What We Intentionally Skip

- User authentication (you can't login on my http://localhost:5173/ now we understand that joke ok )
- Database systems (JSON go brrr)
- Payment/billing (we're broke)
- Production security (YOLO)
- Horizontal scaling (what even is that)

**Why?** Because we're here to learn LLMs, not to build the next startup.

---

## Application Overview

```
┌───────────────────┬─────────────────────────────────────┬────────────────────────────┐
│  SOURCES          │  CHAT                               │  STUDIO                    │
│                   │                                     │                            │
│  Throw your       │  Ask dumb questions,                │  Generate stuff from       │
│  docs here        │  get smart answers                  │  your sources              │
│                   │                                     │                            │
│  - PDF            │  AI searches your sources           │  - Audio Overview          │
│  - DOCX/PPTX      │  and cites them (fancy!)            │  - Ad Creatives            │
│  - Images         │                                     │  - Video Generation        │
│  - Audio          │  Memory system remembers            │  - Flash Cards             │
│  - YouTube        │  you (creepy but useful)            │  - Mind Maps               │
│  - URLs           │                                     │  - Quiz, Social, Emails... │
└───────────────────┴─────────────────────────────────────┴────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React + Vite + TypeScript |
| **UI** | shadcn/ui + Tailwind CSS |
| **Icons** | Phosphor Icons |
| **Backend** | Python Flask |
| **AI/LLM** | Claude (Anthropic), OpenAI Embeddings |
| **Vector DB** | Pinecone |
| **Audio** | ElevenLabs (TTS + Transcription) |
| **Image Gen** | Google Gemini |
| **Video Gen** | Google Veo 2.0 (10-20 min wait, worth it) |
| **Storage** | JSON files (databases are for pros) |

---

## Quick Start (for fellow noobs)

### Prerequisites

- Python 3.10+ (yes, you need Python)
- Node.js 18+ (JavaScript things)
- API Keys (the expensive part)

### 1. Clone & Install

```bash
# Clone it
git clone https://github.com/anthropics/noobbooklm.git
cd noobbooklm

# Backend stuff
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend stuff
cd ../frontend
npm install
```

### 2. API Keys (the pay-to-play part)

Create `backend/.env`:

```env
# Required (sorry, not free)
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
PINECONE_API_KEY=...
PINECONE_INDEX_NAME=noobbooklm

# Optional (for extra features)
ELEVENLABS_API_KEY=...          # Audio overview, voice input
NANO_BANANA_API_KEY=...         # Ad creatives (Gemini)
VEO_API_KEY=...                 # Video generation (make AI movies!)
TAVILY_API_KEY=...              # Web search
GOOGLE_CLIENT_ID=...            # Google Drive import
GOOGLE_CLIENT_SECRET=...

# Rate limiting tier (1-4, pick your wallet size)
ANTHROPIC_TIER=2
```

### 3. Run It

```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate
python run.py

# Terminal 2: Frontend
cd frontend
npm run dev
```

Open http://localhost:5173 and prepare to be underwhelmed.

---

## Key AI Patterns (the actual learning part)

### 1. RAG (Retrieval Augmented Generation)
- Chunk documents into bite-sized pieces
- Turn text into numbers (embeddings)
- Find relevant chunks when asked
- Make AI cite its sources like a good student

### 2. Tool Use / Function Calling
- Tell AI what tools exist
- AI decides when to use them
- We run the tools, send results back
- Repeat until AI is satisfied

### 3. Agentic Loops
- AI thinks, acts, observes, repeats
- Like a toddler learning, but faster

### 4. Multi-Modal Processing
- PDFs: Look at them with AI eyes
- Audio: Turn speech into text
- Images: Describe what's in them
- YouTube: Steal their transcripts

### 5. Memory System
- Remember user preferences
- Remember project context
- Merge memories with AI (fancy)

### 6. Two-Step AI Pipelines
- Claude reads your docs and crafts a movie script (well, a 2-4 sentence prompt)
- Google Veo turns it into an actual 5-8 second video
- Wait 10-20 minutes (go touch grass)
- Get a sick video you didn't make yourself
- Pretend you're Steven Spielberg

**Real talk**: Video generation uses a dual-AI approach:
1. Claude analyzes your source and generates an optimized prompt with cinematography details
2. Google Veo 2.0 uses that prompt to generate actual video (aspect ratio, duration, lighting, the works)
3. Background task handles the long wait so you can keep working
4. Download MP4s when ready

This pattern shows how to chain different AI services for complex outputs. Also shows how to handle *really* long-running tasks (because video generation is S L O W).

---

## Learning Sessions

This masterpiece was built across live coding sessions:

1. **Session 1**: API Basics - "Hello Claude"
2. **Session 2**: Chat & Agents - "Claude does things"
3. **Session 3**: The Full Thing - "It actually works?!"

---

## Contributing

Found a bug? That's a feature.

But seriously, contributions welcome. We're all noobs here.

## License

MIT (do whatever you want, we don't care)

---

**Built with Claude Code by noobs, for noobs.**
