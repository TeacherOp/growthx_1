"""
Transcription API Blueprint - ElevenLabs Speech-to-Text.

Educational Note: This blueprint demonstrates real-time audio transcription
using ElevenLabs' Scribe API via WebSockets.

Why WebSockets for Transcription?
- HTTP is request/response - not suitable for streaming audio
- WebSockets provide bidirectional, low-latency communication
- Audio is streamed in small chunks as user speaks
- Transcription results stream back in real-time

Architecture Overview:
1. Backend generates single-use token (this blueprint)
2. Frontend connects directly to ElevenLabs WebSocket
3. Audio captured via AudioWorklet (low-latency audio processing)
4. Audio converted to 16-bit PCM, base64 encoded
5. Sent over WebSocket, transcription streams back

Security Model:
- API key stays on server (never sent to frontend)
- Single-use tokens expire after 15 minutes
- Each recording session gets fresh token
- Token embedded in WebSocket URL for auth

Audio Format:
- Sample rate: 16000 Hz (optimal for speech)
- Encoding: PCM signed 16-bit little-endian
- Mono channel

This is a great example of keeping sensitive credentials server-side
while still enabling real-time client-side functionality.
"""
from flask import Blueprint

# Create blueprint for transcription configuration
transcription_bp = Blueprint('transcription', __name__)

# Import routes to register them with the blueprint
from app.api.transcription import routes  # noqa: F401
