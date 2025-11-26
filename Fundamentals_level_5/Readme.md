# LocalNotebook — Open Source NotebookLM Clone

## What We're Building

An open-source web application that recreates the core functionality of Google's NotebookLM with local data storage and educational focus:

- **NotebookLM Clone** — Upload documents, create projects, chat with your knowledge base, and generate content
- **Educational Focus** — Learn LLM concepts through practical implementation
- **Local-First** — All data stored locally, users control their own API keys
- **Cross-Platform** — Web app that works on all platforms (Mac, Windows, Linux, mobile)

---

## Why This Exists

- **For learning**: Covers core LLM teaching concepts through practical implementation
- **Open source**: Fully transparent codebase for learning and modification
- **Privacy-first**: Local data storage with user-controlled API keys
- **No subscriptions**: Pay only for the API calls you make

---

## Target Platform

- **Web Application** — Works in any modern browser
- **No app bundling complexity** — Same app works on all platforms
- **Local data storage** — JSON files stored in browser's local storage or downloadable
- **Self-hosted option** — Run locally or deploy to any web server

---

## Core Features (NotebookLM Clone)

### Document Management
- Create and manage multiple projects/notebooks
- Upload documents (PDF, text, markdown, URLs, YouTube videos)
- Support for multiple sources per project (up to 50)
- Document indexing and organization
- Source categorization and quick switching

### AI-Powered Research
- Natural language Q&A about documents
- Context-aware responses with inline citations
- Direct linking to source sections
- Multi-document cross-referencing
- Follow-up question suggestions

### Content Generation
- **Study Guides** — Automatic study guide creation from sources
- **Briefing Documents** — Executive summaries and briefings
- **Audio Overviews** — Convert documents to podcast-style discussions
- **Mind Maps** — Visual representation of document relationships
- **Presentations** — Auto-generate slides from content
- **Video Overviews** — Create video summaries with AI narration
- **Outlines** — Structured outlines from notes
- **Key Points** — Extract and organize main ideas

### Chat Interface
- Normal chat mode (general AI assistant)
- Project chat mode (chat within document context)
- Multiple chats per project
- Chat history and management
- Voice input for chat (using browser's speech API)

---

### External APIs (User Provides Keys)

| Service | Provider | Purpose | Required |
|---------|----------|---------|----------|
| LLM / Chat | Claude API (Anthropic) | Main AI brain | Yes |
| Embeddings | OpenAI API | Document embeddings | Yes |
| Voice Transcription | Browser Speech API | Voice input | No (built-in) |
| YouTube Data | YouTube API | Video transcripts | Optional |
| Image Generation | Google Gemini | Visual content | Optional |

---

## Learning Concepts Covered

### Core LLM Concepts
1. **Normal Chat** — Basic LLM interaction
2. **Project-Based Chat** — Context management and memory
3. **RAG (Retrieval Augmented Generation)** — Document Q&A with citations
4. **Embeddings & Vector Search** — Semantic document search
5. **Prompt Engineering** — Customizable system prompts

### Agent Architecture
1. **Main Agent** — Orchestrates different capabilities
2. **Sub-Agents** — Specialized agents for specific tasks:
   - Document processing agent
   - Content generation agent
   - Audio overview agent (podcast generation)
   - Presentation builder agent
   - Mind map creator agent

### Advanced Features
1. **Multi-modal Processing** — Text, images, PDFs, videos
2. **Streaming Responses** — Real-time AI output
3. **Token Management** — Handling context limits
4. **Citation Generation** — Linking responses to sources