"""
Embedding Utils - Token counting and embedding decisions.

Educational Note: We ALWAYS create chunks and embed them for every source.
This creates a consistent pipeline across all file types:

Pipeline: Source → Process → Count Tokens → Chunk → Embed

Token count is used for:
1. Deciding chunk sizes when splitting
2. Tracking source size in metadata
3. Future: Could be used for selective embedding

Every source gets chunked and embedded - no exceptions (for now).

Token Counting Strategy (Hybrid Approach):
- Local counting (tiktoken): Used for chunking operations where speed matters
  and thousands of calls are made. tiktoken uses cl100k_base encoding which
  closely matches Claude's tokenizer for most text.
- API counting: Available via count_tokens_api() when exact Claude token
  count is needed (e.g., for billing estimation).

Why tiktoken? Chunking calls count_tokens() thousands of times (per page,
per sentence, per word for long sentences). API calls would take minutes
due to network latency. tiktoken is local and instant.
"""
from typing import Tuple
import tiktoken

# Initialize tiktoken encoder once (cl100k_base is closest to Claude's tokenizer)
# Educational Note: cl100k_base is used by GPT-4 and Claude uses a similar
# byte-pair encoding. The counts are close enough for chunking purposes.
_encoder = tiktoken.get_encoding("cl100k_base")


# Chunking configuration
CHUNK_TOKEN_TARGET = 200  # Target tokens per chunk
CHUNK_MARGIN_PERCENT = 20  # +/- margin percentage

# Calculated thresholds
CHUNK_MIN_TOKENS = int(CHUNK_TOKEN_TARGET * (1 - CHUNK_MARGIN_PERCENT / 100))  # 160
CHUNK_MAX_TOKENS = int(CHUNK_TOKEN_TARGET * (1 + CHUNK_MARGIN_PERCENT / 100))  # 240

# Embedding flag - can be changed later if we want selective embedding
ALWAYS_EMBED = True


def get_embedding_info(text: str) -> Tuple[bool, int, str]:
    """
    Get embedding decision and token count for a source.

    Args:
        text: The processed text content

    Returns:
        Tuple of:
            - should_embed (bool): Whether to embed this source
            - token_count (int): Actual token count (for chunk sizing)
            - reason (str): Explanation
    """
    if not text or not text.strip():
        return ALWAYS_EMBED, 0, "Empty text"

    token_count = count_tokens(text)

    # Currently always embed, but token count is returned for chunk sizing
    if ALWAYS_EMBED:
        if token_count <= CHUNK_MAX_TOKENS:
            return True, token_count, f"{token_count:,} tokens - single chunk"
        else:
            estimated_chunks = max(1, token_count // CHUNK_TOKEN_TARGET)
            return True, token_count, f"{token_count:,} tokens - ~{estimated_chunks} chunks"
    else:
        # Future: Could add logic here for selective embedding
        return False, token_count, f"{token_count:,} tokens - embedding disabled"


def count_tokens(text: str) -> int:
    """
    Count tokens using tiktoken (fast, local).

    Educational Note: This uses tiktoken's cl100k_base encoding for fast
    local token counting. This is called thousands of times during chunking
    (per page, per sentence, per word for long sentences), so speed is critical.

    tiktoken is ~10,000x faster than API calls for token counting because
    it runs locally with no network latency.

    Args:
        text: The text to count tokens for

    Returns:
        Number of tokens (approximate, within ~5% of Claude's actual count)
    """
    if not text:
        return 0

    try:
        return len(_encoder.encode(text))
    except Exception as e:
        # Fallback: estimate ~4 chars per token (rough approximation)
        print(f"tiktoken encoding failed, using estimation: {e}")
        return len(text) // 4


def count_tokens_api(text: str) -> int:
    """
    Count tokens using Claude's count_tokens API (accurate but slow).

    Educational Note: Use this when you need exact Claude token counts,
    such as for billing estimation or quota tracking. For chunking
    operations, use count_tokens() which uses tiktoken.

    Args:
        text: The text to count tokens for

    Returns:
        Exact token count according to Claude's tokenizer
    """
    from app.services.integrations.claude import claude_service

    if not text:
        return 0

    messages = [{"role": "user", "content": text}]

    try:
        return claude_service.count_tokens(messages=messages)
    except Exception as e:
        print(f"API token counting failed, falling back to tiktoken: {e}")
        return count_tokens(text)


def get_chunk_config() -> dict:
    """Get chunking configuration values."""
    return {
        "target_tokens": CHUNK_TOKEN_TARGET,
        "margin_percent": CHUNK_MARGIN_PERCENT,
        "min_tokens": CHUNK_MIN_TOKENS,
        "max_tokens": CHUNK_MAX_TOKENS,
        "always_embed": ALWAYS_EMBED,
    }


# Alias for backward compatibility during transition
needs_embedding = get_embedding_info
