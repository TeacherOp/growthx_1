"""
Memory Executor - Execute memory tool calls from main chat.

Educational Note: This executor handles the store_memory tool when Claude
decides to save user or project memory. The execution flow is:

1. Main chat Claude calls store_memory tool with user_memory/project_memory
2. This executor immediately returns "memory stored" (non-blocking)
3. Actual memory merge is triggered as background task via task_service
4. Background task uses memory_service to merge with AI and save

This design ensures the chat response isn't delayed by memory operations.
"""
from typing import Dict, Any, Optional

from app.services.ai_services import memory_service
from app.services.background_services import task_service


class MemoryExecutor:
    """
    Executor for store_memory tool calls.

    Educational Note: Provides immediate response to tool call while
    delegating actual work to background task for non-blocking operation.
    """

    def execute(
        self,
        project_id: str,
        user_memory: Optional[str] = None,
        project_memory: Optional[str] = None,
        why_generated: str = ""
    ) -> Dict[str, Any]:
        """
        Execute the store_memory tool call.

        Educational Note: This method:
        1. Validates inputs
        2. Queues background tasks for memory updates
        3. Returns immediate success (non-blocking)

        Args:
            project_id: The project UUID (needed for project memory)
            user_memory: Optional user-level memory to store
            project_memory: Optional project-level memory to store
            why_generated: Reason for storing this memory

        Returns:
            Dict with immediate success response
        """
        # Track what we're storing
        storing = []

        # Queue user memory update if provided
        if user_memory and user_memory.strip():
            task_service.submit_task(
                "memory_update",           # task_type
                "user_memory",             # target_id
                self._update_user_memory,  # callable_func
                new_memory=user_memory,
                reason=why_generated
            )
            storing.append("user memory")
            print(f"Queued user memory update: {user_memory[:50]}...")

        # Queue project memory update if provided
        if project_memory and project_memory.strip():
            task_service.submit_task(
                "memory_update",              # task_type
                f"project_memory_{project_id}",  # target_id
                self._update_project_memory,  # callable_func
                project_id_for_memory=project_id,
                new_memory=project_memory,
                reason=why_generated
            )
            storing.append("project memory")
            print(f"Queued project memory update: {project_memory[:50]}...")

        # Return immediate success
        if storing:
            return {
                "success": True,
                "message": f"Memory update queued: {', '.join(storing)}",
                "reason": why_generated
            }
        else:
            return {
                "success": False,
                "message": "No memory content provided to store"
            }

    def _update_user_memory(
        self,
        new_memory: str,
        reason: str,
        **kwargs  # Accept extra kwargs from task_service
    ) -> Dict[str, Any]:
        """
        Background task to update user memory.

        Educational Note: This runs in a background thread via task_service.
        It calls memory_service which uses AI to merge memories.

        Args:
            new_memory: New memory content to merge
            reason: Why this update was triggered

        Returns:
            Result from memory_service.update_memory()
        """
        return memory_service.update_memory(
            memory_type="user",
            new_memory=new_memory,
            reason=reason
        )

    def _update_project_memory(
        self,
        project_id_for_memory: str,
        new_memory: str,
        reason: str,
        **kwargs  # Accept extra kwargs from task_service
    ) -> Dict[str, Any]:
        """
        Background task to update project memory.

        Educational Note: This runs in a background thread via task_service.
        It calls memory_service which uses AI to merge memories.

        Args:
            project_id_for_memory: Project UUID for the memory
            new_memory: New memory content to merge
            reason: Why this update was triggered

        Returns:
            Result from memory_service.update_memory()
        """
        return memory_service.update_memory(
            memory_type="project",
            new_memory=new_memory,
            reason=reason,
            project_id=project_id_for_memory
        )


# Singleton instance
memory_executor = MemoryExecutor()
