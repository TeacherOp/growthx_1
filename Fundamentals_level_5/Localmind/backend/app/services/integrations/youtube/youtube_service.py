"""
YouTube Service - Fetch transcripts from YouTube videos.

Educational Note: This service uses the youtube-transcript-api library to fetch
existing captions/transcripts from YouTube videos. It's much faster than downloading
and transcribing audio since it uses YouTube's existing caption data.

Install: pip install youtube-transcript-api
"""

import re
from typing import Dict, Any, Optional, List
from youtube_transcript_api import YouTubeTranscriptApi


class YouTubeService:
    """
    Service class for fetching YouTube video transcripts.

    Educational Note: YouTube stores transcripts as a list of snippets,
    each with text, start time, and duration. We combine these into
    readable text with optional timestamps.
    """

    # Regex patterns for extracting video ID from various YouTube URL formats
    VIDEO_ID_PATTERNS = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com/watch\?.*v=([a-zA-Z0-9_-]{11})',
    ]

    def __init__(self):
        """Initialize the YouTube service."""
        self._api = YouTubeTranscriptApi()

    def extract_video_id(self, url: str) -> Optional[str]:
        """
        Extract video ID from various YouTube URL formats.

        Supported formats:
        - https://www.youtube.com/watch?v=VIDEO_ID
        - https://youtu.be/VIDEO_ID
        - https://www.youtube.com/embed/VIDEO_ID
        - https://youtube.com/watch?v=VIDEO_ID&other_params

        Args:
            url: YouTube URL

        Returns:
            11-character video ID or None if not found
        """
        for pattern in self.VIDEO_ID_PATTERNS:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def get_transcript(
        self,
        url: str,
        include_timestamps: bool = False,
        preferred_languages: List[str] = None
    ) -> Dict[str, Any]:
        """
        Fetch transcript for a YouTube video.

        Args:
            url: YouTube video URL
            include_timestamps: Whether to include timestamps in output
            preferred_languages: List of language codes to try (default: ['en'])

        Returns:
            Dict with:
                - success: bool
                - video_id: str
                - transcript: str (formatted transcript text)
                - language: str (language code of transcript)
                - is_auto_generated: bool
                - duration_seconds: float (total video duration)
                - segment_count: int
                - error_message: str (if failed)
        """
        if preferred_languages is None:
            preferred_languages = ['en']

        # Extract video ID
        video_id = self.extract_video_id(url)
        if not video_id:
            return {
                "success": False,
                "error_message": f"Could not extract video ID from URL: {url}"
            }

        try:
            # Fetch transcript using the new API
            transcript = self._api.fetch(video_id, languages=preferred_languages)

            # Extract data from FetchedTranscript object
            snippets = transcript.snippets
            language = transcript.language_code
            is_auto_generated = transcript.is_generated

            if not snippets:
                return {
                    "success": False,
                    "video_id": video_id,
                    "error_message": "Transcript is empty"
                }

            # Format the transcript
            formatted_text = self._format_transcript(
                snippets,
                include_timestamps=include_timestamps
            )

            # Calculate total duration from last snippet
            last_snippet = snippets[-1]
            total_duration = last_snippet.start + last_snippet.duration

            return {
                "success": True,
                "video_id": video_id,
                "transcript": formatted_text,
                "language": language,
                "is_auto_generated": is_auto_generated,
                "duration_seconds": total_duration,
                "segment_count": len(snippets)
            }

        except Exception as e:
            error_msg = str(e)

            # Provide more helpful error messages
            if "disabled" in error_msg.lower():
                return {
                    "success": False,
                    "video_id": video_id,
                    "error_message": "Transcripts are disabled for this video"
                }
            elif "unavailable" in error_msg.lower() or "private" in error_msg.lower():
                return {
                    "success": False,
                    "video_id": video_id,
                    "error_message": "Video is unavailable (private, deleted, or region-locked)"
                }
            elif "no transcript" in error_msg.lower():
                return {
                    "success": False,
                    "video_id": video_id,
                    "error_message": "No transcript available for this video"
                }
            else:
                return {
                    "success": False,
                    "video_id": video_id,
                    "error_message": f"Error fetching transcript: {error_msg}"
                }

    def _format_transcript(
        self,
        snippets: List[Any],
        include_timestamps: bool = False
    ) -> str:
        """
        Format transcript snippets into readable text.

        Args:
            snippets: List of FetchedTranscriptSnippet objects
            include_timestamps: Whether to include timestamps

        Returns:
            Formatted transcript text
        """
        if not snippets:
            return ""

        lines = []

        for snippet in snippets:
            text = snippet.text.strip() if snippet.text else ""
            if not text:
                continue

            if include_timestamps:
                timestamp = self._format_timestamp(snippet.start)
                lines.append(f"[{timestamp}] {text}")
            else:
                lines.append(text)

        # Join with spaces for cleaner reading
        if include_timestamps:
            return "\n".join(lines)
        else:
            return " ".join(lines)

    def _format_timestamp(self, seconds: float) -> str:
        """
        Format seconds into HH:MM:SS or MM:SS format.

        Args:
            seconds: Time in seconds

        Returns:
            Formatted timestamp string
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"


# Singleton instance
youtube_service = YouTubeService()
