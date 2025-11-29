"""
Chat Services - Services for chat orchestration and message flow.

Educational Note: This folder contains services that handle chat conversations,
including message processing, AI response generation, and tool execution loops.

Services:
- main_chat_service: Main chat orchestrator - handles message flow with tool support
  - Builds dynamic system prompt with source and memory context
  - Manages tool use loop (search_sources, store_memory tools)
  - Logs all API calls for debugging
"""
from app.services.chat_services.main_chat_service import main_chat_service

__all__ = ["main_chat_service"]
