# LocalNotebook — Project Overview

## What We're Building

A local Mac application that combines the core functionality of three popular AI tools into one unified product:

- **NotebookLM** — The hub. Upload documents, create projects, take notes, chat with your knowledge base.
- **Wispr Flow** — Global voice dictation. Hold a hotkey, speak, and text appears wherever your cursor is — any app.
- **Granola** — Meeting intelligence. Capture meeting audio, get transcripts, and enhance notes automatically.

---

## Why This Exists

- **For learning**: Users can explore the codebase, understand how these tools work under the hood, and use it as a starting point for their own projects.
- **For personal use**: A private, local-first productivity tool where users control their own data and API costs.
- **No subscriptions**: Users bring their own API keys and pay only for what they use.

---

## Target Platform

- **macOS only** (native Mac app)
- Not published on App Store — users download and allow it manually
- Requires one-time permission grants: Microphone, Accessibility, Screen Recording (for system audio)

---

## Core Features

### NotebookLM-Style Hub
- Create and manage projects
- Upload documents (PDF, text, markdown, URLs, YouTube videos)
- Chat with project documents (RAG with citations)
- Take and organize notes within projects
- User-editable prompt templates

### Wispr Flow-Style Dictation
- Global hotkey (works even when app is not focused)
- Hold to record, release to transcribe
- Text is typed into whatever app is currently focused
- Works in any application — Claude.ai, Slack, VS Code, browser, etc.

### Granola-Style Meeting Capture
- Capture system audio from any meeting app (Zoom, Google Meet, Teams, Slack)
- Real-time transcription display
- Speaker diarization with manual labeling (Speaker A, B, C → assign names post-meeting)
- Auto-save transcript and notes to project
- Optional LLM enhancement: summaries, action items, key decisions

---

## Tech Stack

### Frontend
- React
- Shadcn/ui component library
- Tailwind CSS
- Vite

### Backend
- Python Flask
- Flask-SocketIO for real-time features

### Storage
- JSON files for all data (projects, documents, notes, meetings, chats)
- No MySQL or PostgreSQL — keeps it simple and teachable
- Data stored locally in user's home directory

### External APIs

| Service | Provider | Purpose |
|---------|----------|---------|
| LLM / Chat | Claude API (Anthropic) | RAG, summarization, chat |
| Voice Transcription | OpenAI Whisper API | Dictation and meeting transcripts |
| Vector Embeddings | Pinecone | Document search and retrieval |
| PDF / Image OCR | DeepSeek | Extract text before chunking |
| YouTube Data | YouTube API | Fetch video metadata and transcripts |
| Image Generation | Google Gemini | Generate images |
| Video Generation | Veo 3 | Generate videos |

Users generate their own API keys and bear the cost — this is for personal use.

---

## System Audio Capture (How Meeting Recording Works)

Since browsers cannot access system audio, the native Mac app uses **BlackHole** (a virtual audio driver):

1. User installs BlackHole once (`brew install blackhole-2ch`)
2. User creates a Multi-Output Device in Audio MIDI Setup (one-time setup)
3. The app captures all system audio — any meeting app works (Zoom, Meet, Teams, etc.)
4. Both system audio (other participants) and microphone (user) are captured for full transcript

---

## Speaker Identification

The app uses speaker diarization to detect different voices, but cannot identify who is speaking by name.

**Flow:**
1. Meeting ends → App detects 3 speakers
2. User plays a sample of each speaker's voice
3. User assigns names (e.g., "Speaker A" → "Neel", "Speaker B" → "Client - Amit")
4. Transcript is updated with proper names

---

## User-Editable Prompts

All LLM prompts are stored as markdown files that users can edit:

- RAG system prompt (how to answer questions from documents)
- Meeting summary prompt (what to extract from transcripts)
- Note enhancement prompt (how to improve raw notes)
- Dictation cleanup prompt (how to format transcribed speech)

---

## Distribution

- **GitHub repository** — users clone or fork the repo
- Repo contains:
  - Full source code (for learning and modification)
  - Pre-built Mac app in `/releases` folder (for immediate use)
  - Setup instructions and documentation
- Users can either:
  - Run the bundled app directly (allow in System Settings, grant permissions)
  - Run from source during development
  - Build their own version after making changes
- No App Store, no code signing required for personal use
- Open source — learn, use, modify, extend

---

## What the Native Mac App Unlocks

| Capability | Web App Only | Native Mac App |
|------------|--------------|----------------|
| Global hotkeys | ❌ | ✅ |
| Type into any app | ❌ | ✅ |
| Capture system audio | ❌ | ✅ |
| Run in background | ❌ | ✅ |
| Menu bar presence | ❌ | ✅ |
| Mic access (anywhere) | ❌ | ✅ |

---

## Summary

LocalNotebook is a personal, local-first AI productivity tool that combines document research, voice dictation, and meeting transcription into a single Mac app. It's designed to be educational, extensible, and cost-effective — users learn from the code, use it daily, and only pay for the API calls they make.