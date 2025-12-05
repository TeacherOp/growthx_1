"""
Studio Signal Executor - Execute studio_signal tool calls from main chat.

Educational Note: This executor handles the studio_signal tool when Claude
identifies opportunities to activate studio generation options. The flow is:

1. Main chat Claude calls studio_signal tool with signals array
2. This executor validates and stores signals synchronously
3. Returns "signals activated" response to Claude

Note: Signal storage is synchronous (not background) to avoid race conditions
with the main chat service which reads/writes the same chat JSON file.

Signals accumulate within a chat (don't reset) and are chat-scoped.
New chats in the same project start with empty signals.
"""
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List

from app.utils.path_utils import get_chats_dir


class StudioSignalExecutor:
    """
    Executor for studio_signal tool calls.

    Educational Note: Provides immediate response to tool call while
    delegating actual signal storage to background task.
    """

    def execute(
        self,
        project_id: str,
        chat_id: str,
        signals: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Execute the studio_signal tool call.

        Educational Note: This method:
        1. Validates signals array
        2. Queues background task to store signals
        3. Returns immediate success (non-blocking)

        Args:
            project_id: The project UUID
            chat_id: The chat UUID where signals should be stored
            signals: Array of signal objects with studio_item, direction, sources

        Returns:
            Dict with immediate success response
        """
        if not signals or not isinstance(signals, list):
            return {
                "success": False,
                "message": "No signals provided"
            }

        # Validate signals structure
        valid_signals = []
        valid_items = {
            "quiz", "flash_cards", "audio_overview", "mind_map",
            "business_report", "marketing_strategy", "prd", "infographics",
            "flow_diagram", "blog", "social", "website", "email_templates",
            "components", "ads_creative", "video", "presentation", "wireframes"
        }

        for signal in signals:
            studio_item = signal.get("studio_item")
            if studio_item not in valid_items:
                print(f"Invalid studio_item: {studio_item}, skipping")
                continue

            # Build base signal
            valid_signal = {
                "id": str(uuid.uuid4()),
                "studio_item": studio_item,
                "direction": signal.get("direction", ""),
                "sources": signal.get("sources", []),
                "created_at": datetime.now().isoformat()
            }

            # Add blog-specific fields if present
            if studio_item == "blog":
                if signal.get("target_keyword"):
                    valid_signal["target_keyword"] = signal.get("target_keyword")
                if signal.get("blog_type"):
                    valid_signal["blog_type"] = signal.get("blog_type")

            # Add business_report-specific fields if present
            if studio_item == "business_report":
                if signal.get("report_type"):
                    valid_signal["report_type"] = signal.get("report_type")
                if signal.get("csv_source_ids"):
                    valid_signal["csv_source_ids"] = signal.get("csv_source_ids")
                if signal.get("context_source_ids"):
                    valid_signal["context_source_ids"] = signal.get("context_source_ids")
                if signal.get("focus_areas"):
                    valid_signal["focus_areas"] = signal.get("focus_areas")

            valid_signals.append(valid_signal)

        if not valid_signals:
            return {
                "success": False,
                "message": "No valid signals to store"
            }

        # Store signals synchronously (not background task)
        # Educational Note: We do this synchronously to avoid race conditions
        # with the main chat service which also reads/writes the chat file.
        # Signal storage is fast (just appending to JSON) so no need for background.
        activated = [s["studio_item"] for s in valid_signals]
        print(f"Storing {len(valid_signals)} studio signals: {activated}")

        store_result = self._store_signals(
            project_id=project_id,
            chat_id=chat_id,
            signals=valid_signals
        )

        if not store_result.get("success"):
            return {
                "success": False,
                "message": f"Failed to store signals: {store_result.get('error', 'Unknown error')}"
            }

        return {
            "success": True,
            "message": f"Studio signals activated: {', '.join(activated)}",
            "count": len(valid_signals)
        }

    def _store_signals(
        self,
        project_id: str,
        chat_id: str,
        signals: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Store signals in chat JSON.

        Educational Note: This runs synchronously (not background) to avoid
        race conditions with the main chat service that reads/writes the same file.
        It appends new signals to the chat's studio_signals array.
        Signals accumulate - they don't replace existing ones.

        Args:
            project_id: The project UUID
            chat_id: The chat UUID
            signals: Array of validated signal objects

        Returns:
            Result dict with success status
        """
        try:
            # Get chat file path
            chats_dir = get_chats_dir(project_id)
            chat_file = chats_dir / f"{chat_id}.json"

            if not chat_file.exists():
                return {
                    "success": False,
                    "error": f"Chat not found: {chat_id}"
                }

            # Load chat data
            with open(chat_file, 'r') as f:
                chat_data = json.load(f)

            # Initialize studio_signals array if not exists
            if "studio_signals" not in chat_data:
                chat_data["studio_signals"] = []

            # Append new signals (accumulate, don't replace)
            chat_data["studio_signals"].extend(signals)

            # Save chat data
            with open(chat_file, 'w') as f:
                json.dump(chat_data, f, indent=2)

            print(f"Stored {len(signals)} studio signals for chat {chat_id}")

            return {
                "success": True,
                "signals_stored": len(signals),
                "total_signals": len(chat_data["studio_signals"])
            }

        except Exception as e:
            print(f"Error storing studio signals: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# Singleton instance
studio_signal_executor = StudioSignalExecutor()
