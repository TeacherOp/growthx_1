"""
ElevenLabs Integration - Speech-to-text and text-to-speech services.

Educational Note: ElevenLabs provides multiple audio services:

Speech-to-Text:
- audio_service: File-based transcription using Scribe v1 model
- transcription_service: Real-time WebSocket transcription for voice input

Text-to-Speech:
- tts_service: Convert text to spoken audio for studio features (audio overview, etc.)
"""
from app.services.integrations.elevenlabs.audio_service import audio_service
from app.services.integrations.elevenlabs.transcription_service import TranscriptionService
from app.services.integrations.elevenlabs.tts_service import tts_service

__all__ = ["audio_service", "TranscriptionService", "tts_service"]
