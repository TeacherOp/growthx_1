"""
Background Services - Services for background task management.

Educational Note: This folder contains services that manage background
operations like async task execution, job queues, and thread pool management.

Services:
- task_service: Background task management using ThreadPoolExecutor
"""
from app.services.background_services.task_service import task_service

__all__ = ["task_service"]
