"""
Rate Limit Utils - Thread-safe rate limiting for API calls.

Educational Note: Rate limiting prevents hitting API limits by:
- Tracking requests within a time window (typically 1 minute)
- Blocking/waiting when the limit is reached
- Resetting the counter when the window expires

This utility is designed to work with tier_loader.py which provides
rate limit configurations based on API tier (free, paid, enterprise).

Usage:
    from app.utils.rate_limit_utils import RateLimiter
    from app.config import get_anthropic_config

    # Create limiter with tier config
    tier_config = get_anthropic_config()
    limiter = RateLimiter(requests_per_minute=tier_config["pages_per_minute"])

    # Before each API call
    limiter.wait_if_needed()
    response = api.call(...)

Used by:
- pdf_service (PDF page extraction)
- pptx_service (slide extraction)
- image_service (image analysis)
- Any service that needs to respect API rate limits
"""
import time
import threading
from typing import Optional


class RateLimiter:
    """
    Thread-safe rate limiter for API calls.

    Educational Note: This uses a sliding window approach:
    - Tracks how many requests were made in the current minute
    - When limit is reached, calculates wait time until window resets
    - Thread-safe via threading.Lock for concurrent batch processing
    """

    def __init__(self, requests_per_minute: int):
        """
        Initialize the rate limiter.

        Args:
            requests_per_minute: Maximum requests allowed per minute
        """
        self.requests_per_minute = requests_per_minute
        self._lock = threading.Lock()
        self._requests_this_minute = 0
        self._minute_start_time = 0.0

    def wait_if_needed(self) -> float:
        """
        Wait if rate limit is reached, then increment counter.

        Educational Note: This method is called before each API request.
        It blocks if we've hit the limit, then increments the request count.

        Returns:
            Time waited in seconds (0 if no wait needed)
        """
        with self._lock:
            current_time = time.time()
            waited = 0.0

            # Reset counter if we're in a new minute
            if current_time - self._minute_start_time >= 60:
                self._requests_this_minute = 0
                self._minute_start_time = current_time

            # Check if we need to wait
            if self._requests_this_minute >= self.requests_per_minute:
                wait_time = 60 - (current_time - self._minute_start_time)
                if wait_time > 0:
                    print(f"Rate limit reached ({self.requests_per_minute}/min). Waiting {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    waited = wait_time
                    # Reset after waiting
                    self._requests_this_minute = 0
                    self._minute_start_time = time.time()

            # Increment counter for this request
            self._requests_this_minute += 1

            return waited

    def reset(self) -> None:
        """Reset the rate limiter counters."""
        with self._lock:
            self._requests_this_minute = 0
            self._minute_start_time = 0.0

    @property
    def remaining_requests(self) -> int:
        """Get remaining requests in current window."""
        with self._lock:
            current_time = time.time()

            # If window expired, full limit is available
            if current_time - self._minute_start_time >= 60:
                return self.requests_per_minute

            return max(0, self.requests_per_minute - self._requests_this_minute)

    @property
    def seconds_until_reset(self) -> float:
        """Get seconds until the rate limit window resets."""
        with self._lock:
            current_time = time.time()
            elapsed = current_time - self._minute_start_time

            if elapsed >= 60:
                return 0.0

            return 60 - elapsed


def create_rate_limiter(requests_per_minute: int) -> RateLimiter:
    """
    Factory function to create a rate limiter.

    Educational Note: This is a convenience function that makes it
    clear we're creating a new limiter instance.

    Args:
        requests_per_minute: Maximum requests allowed per minute

    Returns:
        New RateLimiter instance
    """
    return RateLimiter(requests_per_minute)
