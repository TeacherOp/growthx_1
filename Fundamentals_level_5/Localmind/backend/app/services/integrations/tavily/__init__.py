"""
Tavily Integration - Tavily AI web search API wrapper.

Educational Note: Tavily provides AI-powered web search with optional
answer generation. Used as a fallback in the web agent when web_fetch fails.
"""
from app.services.integrations.tavily.tavily_service import tavily_service

__all__ = ["tavily_service"]
