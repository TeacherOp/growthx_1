"""
YouTube Integration - Fetch transcripts from YouTube videos.

Educational Note: This integration uses the youtube-transcript-api library to fetch
existing captions/transcripts from YouTube videos. It's much faster than downloading
and transcribing audio since it uses YouTube's existing caption data.

Install: pip install youtube-transcript-api
"""
from app.services.integrations.youtube.youtube_service import youtube_service

__all__ = ["youtube_service"]
