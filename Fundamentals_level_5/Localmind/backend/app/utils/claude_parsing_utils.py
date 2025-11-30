"""
Claude Parsing Utils - Utilities for parsing Claude API responses and building message content.

Educational Note: Claude API has specific message patterns for tool use:

1. Simple text response:
   stop_reason: "end_turn"
   content: [{type: "text", text: "..."}]

2. Client Tool use (we execute, send results back):
   stop_reason: "tool_use"
   content: [
       {type: "text", text: "I'll check..."},
       {type: "tool_use", id: "toolu_01", name: "get_weather", input: {...}},
   ]

3. Server Tool use (Claude executes, results come in same response):
   stop_reason: "end_turn" (or continues)
   content: [
       {type: "server_tool_use", id: "srvtoolu_01", name: "web_fetch", input: {...}},
       {type: "web_fetch_tool_result", tool_use_id: "srvtoolu_01", content: "..."},
   ]

4. Tool results (sent as ONE user message with all results):
   role: "user"
   content: [
       {type: "tool_result", tool_use_id: "toolu_01", content: "68°F sunny"},
   ]

Server Tools (web_search, web_fetch):
- Claude handles execution directly
- Results appear as *_tool_result blocks in the same response
- No tool_result message needed from us
- Requires beta headers: "anthropic-beta": "web-search-2025-03-05,web-fetch-2025-09-10"

Message chain: user → assistant (tool_use[]) → user (tool_result[]) → assistant (final)

This utility is used by:
- main_chat_service (chat with search/memory tools)
- ai_services (PDF, PPTX, image extraction with forced tool use)
- ai_agents (web agent with server + client tools)
"""
from typing import Dict, List, Any, Optional


# =============================================================================
# Response Type Checks
# =============================================================================

def is_end_turn(response: Dict[str, Any]) -> bool:
    """
    Check if response is a final text response (conversation complete).

    Args:
        response: Response dict from claude_service.send_message()

    Returns:
        True if stop_reason is "end_turn"
    """
    return response.get("stop_reason") == "end_turn"


def is_tool_use(response: Dict[str, Any]) -> bool:
    """
    Check if response contains tool_use blocks that need tool_result back.

    Educational Note: When stop_reason is "tool_use", we must:
    1. Extract all tool_use blocks
    2. Execute each tool
    3. Send back tool_result for each (with matching IDs)
    4. Call Claude again to continue

    Args:
        response: Response dict from claude_service.send_message()

    Returns:
        True if stop_reason is "tool_use"
    """
    return response.get("stop_reason") == "tool_use"


def get_stop_reason(response: Dict[str, Any]) -> str:
    """
    Get the stop_reason from response.

    Common values:
    - "end_turn": Claude finished (final text response)
    - "tool_use": Claude wants to use tools
    - "max_tokens": Response truncated
    - "stop_sequence": Hit a stop sequence

    Args:
        response: Response dict from claude_service.send_message()

    Returns:
        The stop_reason string
    """
    return response.get("stop_reason", "")


# =============================================================================
# Content Extraction
# =============================================================================

def extract_text(response: Dict[str, Any]) -> str:
    """
    Extract text content from Claude response.

    Educational Note: Response content_blocks can contain multiple blocks
    (text + tool_use). This extracts only the text portions.
    For tool_use responses, this gets Claude's explanation like
    "I'll check the weather for you."

    Args:
        response: Response dict from claude_service.send_message()

    Returns:
        Combined text content as a single string
    """
    content_blocks = response.get("content_blocks", [])
    text_parts = []

    for block in content_blocks:
        # Handle Anthropic objects (have .type attribute)
        if hasattr(block, 'type') and block.type == "text":
            text_parts.append(block.text)
        # Handle dict format (already serialized)
        elif isinstance(block, dict) and block.get("type") == "text":
            text_parts.append(block.get("text", ""))

    return "\n".join(text_parts)


def extract_citations(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract citations from web_search text blocks.

    Educational Note: When Claude uses web_search, text blocks can include
    citations with the source information. Each citation contains:
    - url: The source URL
    - title: The page title
    - encrypted_index: Reference for multi-turn (we can ignore)
    - cited_text: Up to 150 chars of the cited content

    This is valuable for the research agent to properly cite sources!

    Args:
        response: Response dict from claude_service.send_message()

    Returns:
        List of citation dicts: [{url, title, cited_text}, ...]
    """
    citations = []
    content_blocks = response.get("content_blocks", [])

    for block in content_blocks:
        block_citations = None

        # Handle Anthropic objects
        if hasattr(block, 'type') and block.type == "text":
            block_citations = getattr(block, 'citations', None)
        # Handle dict format
        elif isinstance(block, dict) and block.get("type") == "text":
            block_citations = block.get("citations")

        if block_citations:
            for citation in block_citations:
                # Extract the useful fields (skip encrypted_index)
                if hasattr(citation, 'url'):
                    citations.append({
                        "url": citation.url,
                        "title": getattr(citation, 'title', ''),
                        "cited_text": getattr(citation, 'cited_text', '')
                    })
                elif isinstance(citation, dict):
                    citations.append({
                        "url": citation.get("url", ""),
                        "title": citation.get("title", ""),
                        "cited_text": citation.get("cited_text", "")
                    })

    return citations


def extract_text_with_citations(response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract both text and citations from Claude response.

    Educational Note: Convenience method that returns both the text content
    and any citations from web_search. Useful for research agents that need
    to cite their sources.

    Args:
        response: Response dict from claude_service.send_message()

    Returns:
        Dict with 'text' and 'citations' keys
    """
    return {
        "text": extract_text(response),
        "citations": extract_citations(response)
    }


def extract_tool_use_blocks(
    response: Dict[str, Any],
    tool_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Extract tool_use blocks from Claude response.

    Educational Note: Claude can call multiple tools in parallel. Each tool_use has:
    - id: Unique identifier (e.g., "toolu_01") - MUST match in tool_result
    - name: Tool being called
    - input: Parameters for the tool

    Args:
        response: Response dict from claude_service.send_message()
        tool_name: Optional filter - only return blocks for this tool

    Returns:
        List of dicts: [{id, name, input}, ...]
    """
    tool_blocks = []
    content_blocks = response.get("content_blocks", [])

    for block in content_blocks:
        # Handle Anthropic objects (have .type attribute)
        if hasattr(block, 'type') and block.type == "tool_use":
            if tool_name is None or block.name == tool_name:
                tool_blocks.append({
                    "id": block.id,
                    "name": block.name,
                    "input": block.input,
                })

        # Handle dict format (already serialized)
        elif isinstance(block, dict) and block.get("type") == "tool_use":
            if tool_name is None or block.get("name") == tool_name:
                tool_blocks.append({
                    "id": block.get("id"),
                    "name": block.get("name"),
                    "input": block.get("input", {}),
                })

    return tool_blocks


def extract_tool_inputs(
    response: Dict[str, Any],
    tool_name: str
) -> List[Dict[str, Any]]:
    """
    Extract just the input parameters from tool_use blocks.

    Educational Note: Convenience method when you only need the inputs
    (not the IDs). Useful for extraction tasks like PDF processing where
    Claude uses submit_page_extraction tool and you just want the data.

    Args:
        response: Response dict from claude_service.send_message()
        tool_name: Name of the tool to extract inputs for

    Returns:
        List of input dicts from matching tool_use blocks
    """
    tool_blocks = extract_tool_use_blocks(response, tool_name)
    return [block["input"] for block in tool_blocks]


# =============================================================================
# Server Tool Extraction - For web_search, web_fetch (Claude-executed tools)
# =============================================================================

def extract_server_tool_use_blocks(
    response: Dict[str, Any],
    tool_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Extract server_tool_use blocks from Claude response.

    Educational Note: Server tools (web_search, web_fetch) are executed by Claude
    directly. They appear as "server_tool_use" blocks, and their results come
    back in the same response as "*_tool_result" blocks.

    Args:
        response: Response dict from claude_service.send_message()
        tool_name: Optional filter - only return blocks for this tool

    Returns:
        List of dicts: [{id, name, input}, ...]
    """
    tool_blocks = []
    content_blocks = response.get("content_blocks", [])

    for block in content_blocks:
        # Handle Anthropic objects
        if hasattr(block, 'type') and block.type == "server_tool_use":
            if tool_name is None or block.name == tool_name:
                tool_blocks.append({
                    "id": block.id,
                    "name": block.name,
                    "input": block.input,
                })

        # Handle dict format
        elif isinstance(block, dict) and block.get("type") == "server_tool_use":
            if tool_name is None or block.get("name") == tool_name:
                tool_blocks.append({
                    "id": block.get("id"),
                    "name": block.get("name"),
                    "input": block.get("input", {}),
                })

    return tool_blocks


def extract_server_tool_results(
    response: Dict[str, Any],
    result_type: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Extract server tool result blocks from Claude response.

    Educational Note: Server tool results have types like:
    - "web_search_tool_result" - Results from web_search
    - "web_fetch_tool_result" - Results from web_fetch

    These results are included directly in Claude's response and don't
    require us to send tool_result messages back.

    Args:
        response: Response dict from claude_service.send_message()
        result_type: Optional filter - "web_search_tool_result" or "web_fetch_tool_result"

    Returns:
        List of dicts: [{type, tool_use_id, content}, ...]
    """
    result_blocks = []
    content_blocks = response.get("content_blocks", [])

    # Types we recognize as server tool results
    server_result_types = {"web_search_tool_result", "web_fetch_tool_result"}

    for block in content_blocks:
        block_type = getattr(block, "type", None) if hasattr(block, "type") else block.get("type")

        if block_type in server_result_types:
            if result_type is None or block_type == result_type:
                result_blocks.append({
                    "type": block_type,
                    "tool_use_id": getattr(block, "tool_use_id", None) if hasattr(block, "tool_use_id") else block.get("tool_use_id"),
                    "content": getattr(block, "content", None) if hasattr(block, "content") else block.get("content"),
                })

    return result_blocks


def has_server_tool_use(response: Dict[str, Any]) -> bool:
    """
    Check if response contains server tool usage.

    Args:
        response: Response dict from claude_service.send_message()

    Returns:
        True if response contains server_tool_use blocks
    """
    return len(extract_server_tool_use_blocks(response)) > 0


# =============================================================================
# Content Block Building - For sending tool results back to Claude
# =============================================================================

def build_tool_result_content(
    tool_results: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Build tool_result content blocks for responding to tool_use.

    Educational Note: After Claude calls tools, we send back a single user message
    with ALL tool_result blocks. Each tool_result must have tool_use_id matching
    the original tool_use block.

    Example input:
        [
            {"tool_use_id": "toolu_01", "result": "68°F sunny"},
            {"tool_use_id": "toolu_02", "result": "2:30 PM PST"},
        ]

    Example output:
        [
            {"type": "tool_result", "tool_use_id": "toolu_01", "content": "68°F sunny"},
            {"type": "tool_result", "tool_use_id": "toolu_02", "content": "2:30 PM PST"},
        ]

    Args:
        tool_results: List of dicts with:
            - tool_use_id: ID from the tool_use block (REQUIRED)
            - result: The result string/content
            - is_error: (optional) Whether tool execution failed

    Returns:
        List of tool_result content blocks for user message
    """
    content_blocks = []

    for result in tool_results:
        tool_use_id = result.get("tool_use_id")
        result_content = result.get("result", "")
        is_error = result.get("is_error", False)

        # Ensure result is a string
        if not isinstance(result_content, str):
            result_content = str(result_content)

        block = {
            "type": "tool_result",
            "tool_use_id": tool_use_id,
            "content": result_content,
        }

        # Only add is_error if True (cleaner JSON)
        if is_error:
            block["is_error"] = True

        content_blocks.append(block)

    return content_blocks


def build_single_tool_result(
    tool_use_id: str,
    result: str,
    is_error: bool = False
) -> List[Dict[str, Any]]:
    """
    Build tool_result content for a single tool call.

    Educational Note: Convenience method for the common case of responding
    to a single tool use (non-parallel).

    Args:
        tool_use_id: ID from the tool_use block
        result: The result string
        is_error: Whether tool execution failed

    Returns:
        List with single tool_result content block
    """
    return build_tool_result_content([{
        "tool_use_id": tool_use_id,
        "result": result,
        "is_error": is_error,
    }])


# =============================================================================
# Content Block Serialization - For storing in JSON (message history, logs)
# =============================================================================

def _serialize_anthropic_object(obj: Any) -> Any:
    """
    Recursively convert Anthropic SDK objects to JSON-serializable dicts.

    Educational Note: Anthropic SDK returns objects with attributes (.type, .url, etc.)
    that aren't JSON serializable. This helper recursively converts them to plain dicts.
    Handles nested objects, lists, and primitive types.

    Used for server tool results (web_search_tool_result, web_fetch_tool_result)
    which contain nested SDK objects like WebSearchResultBlock, WebFetchResult, etc.
    """
    # Already a primitive type - return as-is
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj

    # List - recursively serialize each element
    if isinstance(obj, list):
        return [_serialize_anthropic_object(item) for item in obj]

    # Dict - recursively serialize values
    if isinstance(obj, dict):
        return {key: _serialize_anthropic_object(value) for key, value in obj.items()}

    # Anthropic SDK object - convert to dict by extracting attributes
    if hasattr(obj, '__dict__'):
        result = {}
        for key, value in vars(obj).items():
            # Skip private attributes
            if not key.startswith('_'):
                result[key] = _serialize_anthropic_object(value)
        return result

    # Fallback - try to convert to string
    return str(obj)


def serialize_content_blocks(content_blocks: List[Any]) -> List[Dict[str, Any]]:
    """
    Convert Anthropic content block objects to JSON-serializable dicts.

    Educational Note: Claude API returns content blocks as Anthropic objects
    with attributes (.type, .text, .id). For storing in JSON files (message
    history, debug logs), we need plain dicts.

    Handles both client tools (tool_use) and server tools (server_tool_use,
    web_search_tool_result, web_fetch_tool_result).

    Args:
        content_blocks: List of Anthropic content block objects

    Returns:
        List of JSON-serializable dicts
    """
    serialized = []

    for block in content_blocks:
        # Handle Anthropic objects
        if hasattr(block, 'type'):
            if block.type == "text":
                text_block = {
                    "type": "text",
                    "text": block.text
                }
                # Include citations if present (from web_search)
                if hasattr(block, 'citations') and block.citations:
                    text_block["citations"] = [
                        {
                            "url": getattr(c, 'url', ''),
                            "title": getattr(c, 'title', ''),
                            "cited_text": getattr(c, 'cited_text', '')
                        }
                        for c in block.citations
                    ]
                serialized.append(text_block)
            elif block.type == "tool_use":
                # Client tool use - we execute these
                serialized.append({
                    "type": "tool_use",
                    "id": block.id,
                    "name": block.name,
                    "input": block.input
                })
            elif block.type == "tool_result":
                serialized.append({
                    "type": "tool_result",
                    "tool_use_id": getattr(block, 'tool_use_id', ''),
                    "content": getattr(block, 'content', '')
                })
            elif block.type == "server_tool_use":
                # Server tool use - Claude executes these (web_fetch, web_search)
                serialized.append({
                    "type": "server_tool_use",
                    "id": block.id,
                    "name": block.name,
                    "input": block.input
                })
            elif block.type == "web_search_tool_result":
                # Server tool result from web_search
                # Content is a list of WebSearchResultBlock objects - must serialize recursively
                serialized.append({
                    "type": "web_search_tool_result",
                    "tool_use_id": getattr(block, 'tool_use_id', ''),
                    "content": _serialize_anthropic_object(getattr(block, 'content', None))
                })
            elif block.type == "web_fetch_tool_result":
                # Server tool result from web_fetch
                # Content is a WebFetchResult object with nested Document - must serialize recursively
                serialized.append({
                    "type": "web_fetch_tool_result",
                    "tool_use_id": getattr(block, 'tool_use_id', ''),
                    "content": _serialize_anthropic_object(getattr(block, 'content', None))
                })
        # Already a dict - pass through
        elif isinstance(block, dict):
            serialized.append(block)

    return serialized


# =============================================================================
# Token/Usage Extraction
# =============================================================================

def get_token_usage(response: Dict[str, Any]) -> Dict[str, int]:
    """
    Extract token usage from response.

    Educational Note: Token usage is important for:
    - Cost tracking (Sonnet: $3/$15, Haiku: $1/$5 per 1M tokens)
    - Debugging context length issues
    - Optimizing prompt sizes

    Args:
        response: Response dict from claude_service.send_message()

    Returns:
        Dict with 'input_tokens' and 'output_tokens'
    """
    usage = response.get("usage", {})
    return {
        "input_tokens": usage.get("input_tokens", 0),
        "output_tokens": usage.get("output_tokens", 0),
    }


def get_model(response: Dict[str, Any]) -> str:
    """
    Get the model name from response.

    Args:
        response: Response dict from claude_service.send_message()

    Returns:
        Model string (e.g., "claude-sonnet-4-5-20250929")
    """
    return response.get("model", "")
