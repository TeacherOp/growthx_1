"""
Claude Integration - Anthropic Claude API wrapper.

Educational Note: This module provides a clean interface to the Claude API.
Used by chat, agents, and various processing services.
"""
from app.services.integrations.claude.claude_service import claude_service

__all__ = ["claude_service"]
