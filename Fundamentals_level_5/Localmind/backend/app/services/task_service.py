"""
Task Service - Background task management using ThreadPoolExecutor.

Educational Note: This service manages background tasks without external
dependencies like Celery or Redis. It uses Python's built-in ThreadPoolExecutor
for concurrent execution and a JSON file for task tracking.

Why ThreadPoolExecutor works for our use case:
- Our tasks are I/O-bound (API calls, file operations)
- I/O operations release the GIL (Global Interpreter Lock)
- While one thread waits for Claude API, other threads can run
- User can chat while PDFs are being processed in background

How it works:
1. Task is submitted with a callable and arguments
2. ThreadPoolExecutor runs it in a background thread
3. Task status is tracked in JSON file
4. Source status is updated directly by the task
"""
import json
import uuid
import threading
from concurrent.futures import ThreadPoolExecutor, Future
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Callable, Optional, List

from config import Config


class TaskService:
    """
    Service class for managing background tasks.

    Educational Note: This is a simple task queue implementation using
    Python's built-in ThreadPoolExecutor. No external dependencies needed.
    """

    # Maximum concurrent background tasks
    MAX_WORKERS = 4

    def __init__(self):
        """Initialize the task service."""
        self.tasks_dir = Config.DATA_DIR / "tasks"
        self.tasks_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.tasks_dir / "tasks_index.json"

        # Thread pool for executing tasks
        # Educational Note: ThreadPoolExecutor manages a pool of worker threads
        # Tasks are queued and executed as threads become available
        self._executor = ThreadPoolExecutor(max_workers=self.MAX_WORKERS)

        # Lock for thread-safe JSON file operations
        self._lock = threading.Lock()

        # Track running futures (for potential cancellation)
        self._futures: Dict[str, Future] = {}

        # Track cancelled tasks - workers check this to stop early
        self._cancelled_tasks: set = set()

        # Initialize index file
        self._ensure_index()

        # Clean up any stale tasks from previous runs
        self._cleanup_stale_tasks()

    def _ensure_index(self) -> None:
        """Ensure the tasks index file exists."""
        if not self.index_path.exists():
            self._save_index({"tasks": [], "last_updated": datetime.now().isoformat()})

    def _load_index(self) -> Dict[str, Any]:
        """Load the tasks index from JSON file."""
        try:
            with open(self.index_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {"tasks": [], "last_updated": datetime.now().isoformat()}

    def _save_index(self, data: Dict[str, Any]) -> None:
        """Save the tasks index to JSON file."""
        data["last_updated"] = datetime.now().isoformat()
        with open(self.index_path, "w") as f:
            json.dump(data, f, indent=2)

    def _cleanup_stale_tasks(self) -> None:
        """
        Clean up tasks that were running when server stopped.

        Educational Note: If the server restarts while tasks are running,
        those tasks will be stuck in "running" or "pending" state forever.
        We mark them as failed on startup.
        """
        with self._lock:
            index = self._load_index()
            stale_count = 0

            for task in index["tasks"]:
                if task["status"] in ["pending", "running"]:
                    task["status"] = "failed"
                    task["error"] = "Server restarted while task was running"
                    task["completed_at"] = datetime.now().isoformat()
                    stale_count += 1

            if stale_count > 0:
                self._save_index(index)
                print(f"Marked {stale_count} stale tasks as failed")

    def submit_task(
        self,
        task_type: str,
        target_id: str,
        callable_func: Callable,
        *args,
        **kwargs
    ) -> str:
        """
        Submit a task for background execution.

        Educational Note: This method returns immediately after queuing the task.
        The actual execution happens in a background thread.

        Args:
            task_type: Type of task (e.g., "source_processing")
            target_id: ID of the target resource (e.g., source_id)
            callable_func: The function to execute
            *args, **kwargs: Arguments to pass to the function

        Returns:
            task_id: Unique identifier for tracking the task
        """
        task_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()

        # Create task record
        task_record = {
            "id": task_id,
            "type": task_type,
            "target_id": target_id,
            "status": "pending",
            "error": None,
            "created_at": timestamp,
            "started_at": None,
            "completed_at": None,
        }

        # Save to index
        with self._lock:
            index = self._load_index()
            index["tasks"].append(task_record)
            self._save_index(index)

        # Wrapper function that handles status updates
        def task_wrapper():
            try:
                # Update status to running
                self._update_task(task_id, status="running", started_at=datetime.now().isoformat())

                # Execute the actual task
                result = callable_func(*args, **kwargs)

                # Update status to completed
                self._update_task(
                    task_id,
                    status="completed",
                    completed_at=datetime.now().isoformat()
                )

                return result

            except Exception as e:
                # Update status to failed
                self._update_task(
                    task_id,
                    status="failed",
                    error=str(e),
                    completed_at=datetime.now().isoformat()
                )
                print(f"Task {task_id} failed: {e}")

            finally:
                # Remove from futures tracking
                self._futures.pop(task_id, None)
                # Remove from cancelled set if present
                self._cancelled_tasks.discard(task_id)

        # Submit to executor - this returns immediately
        future = self._executor.submit(task_wrapper)
        self._futures[task_id] = future

        print(f"Task submitted: {task_id} ({task_type} for {target_id})")

        return task_id

    def _update_task(self, task_id: str, **updates) -> None:
        """Update a task's fields in the index."""
        with self._lock:
            index = self._load_index()

            for task in index["tasks"]:
                if task["id"] == task_id:
                    task.update(updates)
                    break

            self._save_index(index)

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get a task's current status."""
        with self._lock:
            index = self._load_index()

            for task in index["tasks"]:
                if task["id"] == task_id:
                    return task

        return None

    def get_tasks_for_target(self, target_id: str) -> List[Dict[str, Any]]:
        """Get all tasks for a specific target."""
        with self._lock:
            index = self._load_index()
            return [t for t in index["tasks"] if t["target_id"] == target_id]

    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a running or pending task.

        Educational Note: Cancellation is cooperative - we set a flag that
        the running task should check periodically. For ThreadPoolExecutor,
        we can also try to cancel the future if it hasn't started yet.

        Args:
            task_id: The task ID to cancel

        Returns:
            True if cancellation was initiated, False if task not found
        """
        task = self.get_task(task_id)
        if not task:
            return False

        # Only cancel pending or running tasks
        if task["status"] not in ["pending", "running"]:
            return False

        # Add to cancelled set - workers should check this
        self._cancelled_tasks.add(task_id)

        # Try to cancel the future if it hasn't started yet
        future = self._futures.get(task_id)
        if future:
            cancelled = future.cancel()
            if cancelled:
                print(f"Task {task_id} cancelled before it started")

        # Update task status
        self._update_task(
            task_id,
            status="cancelled",
            error="Cancelled by user",
            completed_at=datetime.now().isoformat()
        )

        print(f"Task {task_id} cancellation requested")
        return True

    def is_cancelled(self, task_id: str) -> bool:
        """
        Check if a task has been cancelled.

        Educational Note: Long-running tasks should call this periodically
        and stop early if True. This enables cooperative cancellation.

        Args:
            task_id: The task ID to check

        Returns:
            True if task should stop, False otherwise
        """
        return task_id in self._cancelled_tasks

    def cancel_tasks_for_target(self, target_id: str) -> int:
        """
        Cancel all running/pending tasks for a target (e.g., a source).

        Args:
            target_id: The target resource ID

        Returns:
            Number of tasks cancelled
        """
        tasks = self.get_tasks_for_target(target_id)
        cancelled_count = 0

        for task in tasks:
            if task["status"] in ["pending", "running"]:
                if self.cancel_task(task["id"]):
                    cancelled_count += 1

        return cancelled_count

    def is_target_cancelled(self, target_id: str) -> bool:
        """
        Check if any task for a target has been cancelled.

        Educational Note: This is useful for long-running operations that
        need to check if they should stop early, but don't know their task_id.

        Args:
            target_id: The target resource ID (e.g., source_id)

        Returns:
            True if any task for this target was cancelled
        """
        tasks = self.get_tasks_for_target(target_id)
        for task in tasks:
            if task["id"] in self._cancelled_tasks:
                return True
            # Also check if task status is cancelled
            if task["status"] == "cancelled":
                return True
        return False

    def cleanup_old_tasks(self, older_than_hours: int = 24) -> int:
        """
        Remove completed/failed tasks older than specified hours.

        Educational Note: Call this periodically to prevent the JSON file
        from growing indefinitely.

        Args:
            older_than_hours: Remove tasks completed more than this many hours ago

        Returns:
            Number of tasks removed
        """
        cutoff = datetime.now() - timedelta(hours=older_than_hours)

        with self._lock:
            index = self._load_index()
            original_count = len(index["tasks"])

            # Keep tasks that are still running OR completed/cancelled recently
            index["tasks"] = [
                t for t in index["tasks"]
                if t["status"] in ["pending", "running"]
                or (
                    t.get("completed_at")
                    and datetime.fromisoformat(t["completed_at"]) > cutoff
                )
            ]

            # Also clean up cancelled tasks from the cancelled set
            completed_task_ids = {t["id"] for t in index["tasks"]}
            self._cancelled_tasks = self._cancelled_tasks.intersection(completed_task_ids)

            removed_count = original_count - len(index["tasks"])
            if removed_count > 0:
                self._save_index(index)
                print(f"Cleaned up {removed_count} old tasks")

        return removed_count

    def shutdown(self, wait: bool = True) -> None:
        """
        Shutdown the executor gracefully.

        Args:
            wait: If True, wait for running tasks to complete
        """
        print("Shutting down task service...")
        self._executor.shutdown(wait=wait)
        print("Task service shutdown complete")


# Singleton instance
task_service = TaskService()
