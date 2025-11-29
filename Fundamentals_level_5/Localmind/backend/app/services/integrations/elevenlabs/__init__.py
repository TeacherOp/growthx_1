"""
ElevenLabs Integration - Speech-to-text services.

Educational Note: ElevenLabs provides two transcription modes:
- audio_service: File-based transcription using Scribe v1 model
- transcription_service: Real-time WebSocket transcription for voice input
"""
from app.services.integrations.elevenlabs.audio_service import audio_service
from app.services.integrations.elevenlabs.transcription_service import TranscriptionService

__all__ = ["audio_service", "TranscriptionService"]
