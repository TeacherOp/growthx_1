"""
Batching Utils - Generic utilities for splitting items into batches.

Educational Note: Batching is a common pattern when processing large datasets
with APIs that have:
- Rate limits (max requests per minute)
- Context limits (max items per request)
- Cost optimization (fewer API calls = lower cost)

This utility provides a simple, reusable way to split any list into
fixed-size chunks for batch processing.

Used by:
- pdf_service (batch PDF pages for vision extraction)
- pptx_service (batch slides for vision extraction)
- Any future service that needs to process items in batches
"""
from typing import List, TypeVar

# Generic type for batch items
T = TypeVar('T')

# Default batch size for vision-based extraction (PDF, PPTX)
# Educational Note: Balances context awareness (more pages = better cross-page
# understanding) vs API limits (too many pages = token overflow).
DEFAULT_BATCH_SIZE = 5


def create_batches(items: List[T], batch_size: int) -> List[List[T]]:
    """
    Split a list of items into batches of specified size.

    Educational Note: This is a simple chunking algorithm that divides
    a list into sublists of maximum `batch_size` items each. The last
    batch may have fewer items if the total doesn't divide evenly.

    Example:
        items = [1, 2, 3, 4, 5, 6, 7]
        create_batches(items, 3) → [[1, 2, 3], [4, 5, 6], [7]]

    Args:
        items: List of items to batch
        batch_size: Maximum number of items per batch (must be > 0)

    Returns:
        List of batches, where each batch is a list of items

    Raises:
        ValueError: If batch_size is less than 1
    """
    if batch_size < 1:
        raise ValueError("batch_size must be at least 1")

    if not items:
        return []

    batches = []
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        batches.append(batch)

    return batches


def get_batch_info(items: List[T], batch_size: int) -> dict:
    """
    Get information about how items will be batched.

    Educational Note: Useful for logging and progress tracking before
    starting batch processing. Helps estimate time and resources needed.

    Args:
        items: List of items to batch
        batch_size: Maximum number of items per batch

    Returns:
        Dict with total_items, batch_size, total_batches, last_batch_size
    """
    if not items or batch_size < 1:
        return {
            "total_items": 0,
            "batch_size": batch_size,
            "total_batches": 0,
            "last_batch_size": 0
        }

    total_items = len(items)
    total_batches = (total_items + batch_size - 1) // batch_size  # Ceiling division
    last_batch_size = total_items % batch_size or batch_size

    return {
        "total_items": total_items,
        "batch_size": batch_size,
        "total_batches": total_batches,
        "last_batch_size": last_batch_size
    }
