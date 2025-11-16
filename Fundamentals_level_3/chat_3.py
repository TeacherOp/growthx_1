# Chat v3: Persistent conversations with tool functionality
# Building on chat_2.py, this version adds:
# - Tool use capability (get_weather tool)
# - Real-time weather data from Visual Crossing API
# - Proper serialization of tool use messages for persistence
# - Separate storage folder (conversations_with_tool) from chat_2

import os
import json
import uuid
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import anthropic

# Load environment variables from .env file
load_dotenv()

# Initialize the Anthropic client
client = anthropic.Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY"),
)

# Visual Crossing Weather API Key
VISUAL_CROSSING_API_KEY = os.environ.get("VISUAL_CROSSING_API_KEY")

# Model to use
MODEL = "claude-sonnet-4-5-20250929"

# Directory to store conversations (separate from chat_2 which uses "conversations")
CONVERSATIONS_DIR = "conversations_with_tool"

# Define the weather tool
WEATHER_TOOL = {
    "name": "get_weather",
    "description": "Get current weather data for a specific city and country",
    "input_schema": {
        "type": "object",
        "properties": {
            "city_name": {
                "type": "string",
                "description": "Name of the city (e.g., London, New York, Tokyo)"
            },
            "country_name": {
                "type": "string",
                "description": "Name of the country (e.g., UK, USA, Japan)"
            }
        },
        "required": ["city_name", "country_name"]
    }
}

def execute_weather_tool(city_name, country_name):
    """
    Execute the weather API call to Visual Crossing using urllib (like the test script)

    Args:
        city_name: Name of the city
        country_name: Name of the country

    Returns:
        Weather data as a string or error message
    """
    if not VISUAL_CROSSING_API_KEY:
        return "Error: Visual Crossing API key not configured in .env file"

    # Build the location string
    location = f"{city_name}, {country_name}"

    # Generate today's date in the required format
    start_date = datetime.now().strftime('%Y-%m-%d')

    # Construct the URL for the API request (using the exact format from test.py)
    url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{urllib.parse.quote(location)}/{start_date}/{start_date}?unitGroup=metric&contentType=json&key={VISUAL_CROSSING_API_KEY}"

    print(f"\n[Fetching weather for {location}...]")

    try:
        with urllib.request.urlopen(url) as response:
            data = response.read()
            weather_data = json.loads(data)

        # Extract the daily summary for today (same as test.py)
        today_data = weather_data.get('days', [])[0] if weather_data.get('days') else {}

        # Format the weather data with limited information
        weather_info = f"""Weather for {location} on {start_date}:
        - Summary: {today_data.get('description', 'No summary available')}
        - Temperature: {today_data.get('temp', 'No data')}°C
        - Humidity: {today_data.get('humidity', 'No data')}%
        - Wind Speed: {today_data.get('windspeed', 'No data')} kph"""

        return weather_info

    except urllib.error.HTTPError as e:
        error_info = e.read().decode()
        return f"HTTP error {e.code}: {error_info}"
    except urllib.error.URLError as e:
        return f"URL error: {e.reason}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

def ensure_conversations_dir():
    """Create conversations_with_tool directory if it doesn't exist"""
    Path(CONVERSATIONS_DIR).mkdir(exist_ok=True)

def generate_conversation_id():
    """Generate a unique conversation ID"""
    return str(uuid.uuid4())[:8]  # Use first 8 characters for simplicity

def save_conversation(conversation_id, messages, metadata=None):
    """Save conversation to a JSON file after each exchange"""
    ensure_conversations_dir()

    # Convert messages to a JSON-serializable format
    serializable_messages = []
    for msg in messages:
        clean_msg = {"role": msg["role"]}

        content = msg["content"]
        if isinstance(content, str):
            # Simple string content
            clean_msg["content"] = content
        elif isinstance(content, list):
            # List of content blocks (TextBlock, ToolUseBlock, or dicts)
            clean_content = []
            for item in content:
                if hasattr(item, '__dict__'):
                    # It's an Anthropic API object - convert to dict
                    if hasattr(item, 'type'):
                        item_dict = {"type": item.type}

                        # Handle TextBlock
                        if hasattr(item, 'text'):
                            item_dict["text"] = item.text

                        # Handle ToolUseBlock
                        if hasattr(item, 'id'):
                            item_dict["id"] = item.id
                        if hasattr(item, 'name'):
                            item_dict["name"] = item.name
                        if hasattr(item, 'input'):
                            item_dict["input"] = item.input

                        # Handle tool_result (already a dict)
                        if hasattr(item, 'tool_use_id'):
                            item_dict["tool_use_id"] = item.tool_use_id
                        if hasattr(item, 'content') and item.type == "tool_result":
                            item_dict["content"] = item.content

                        clean_content.append(item_dict)
                elif isinstance(item, dict):
                    # Already a dict (like tool_result), keep it
                    clean_content.append(item)
                else:
                    # Something else, convert to string
                    clean_content.append(str(item))
            clean_msg["content"] = clean_content
        else:
            # Single object or other type
            if hasattr(content, '__dict__'):
                # Convert API object to dict
                if hasattr(content, 'text'):
                    clean_msg["content"] = content.text
                else:
                    clean_msg["content"] = str(content)
            else:
                clean_msg["content"] = content

        serializable_messages.append(clean_msg)

    conversation_data = {
        "conversation_id": conversation_id,
        "created_at": metadata.get("created_at") if metadata else datetime.now().isoformat(),
        "last_updated": datetime.now().isoformat(),
        "message_count": len(serializable_messages),
        "messages": serializable_messages
    }

    # Save to file
    filename = f"{CONVERSATIONS_DIR}/conversation_{conversation_id}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(conversation_data, f, indent=2, ensure_ascii=False)

    print(f"[Auto-saved: {conversation_id}]")
    return filename

def load_conversation(conversation_id):
    """Load a conversation from file"""
    filename = f"{CONVERSATIONS_DIR}/conversation_{conversation_id}.json"
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data["messages"], data
    except FileNotFoundError:
        return None, None

def list_conversations():
    """List all saved conversations"""
    ensure_conversations_dir()
    conversations = []

    # Get all conversation files
    for file in Path(CONVERSATIONS_DIR).glob("conversation_*.json"):
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
                conversations.append({
                    "id": data["conversation_id"],
                    "created": data["created_at"],
                    "updated": data["last_updated"],
                    "messages": data["message_count"]
                })
        except:
            continue

    # Sort by last updated (most recent first)
    conversations.sort(key=lambda x: x["updated"], reverse=True)
    return conversations

def display_conversation_menu():
    """Display menu for selecting conversations with tool use history"""
    print("\n" + "=" * 50)
    print("CONVERSATION MENU (Chat v3)")
    print("=" * 50)

    conversations = list_conversations()

    if conversations:
        print("\nRecent Conversations:")
        print("-" * 50)
        for i, conv in enumerate(conversations[:5], 1):  # Show only 5 most recent
            # Parse and format the date
            created = datetime.fromisoformat(conv["created"]).strftime("%Y-%m-%d %H:%M")
            updated = datetime.fromisoformat(conv["updated"]).strftime("%Y-%m-%d %H:%M")
            print(f"{i}. ID: {conv['id']}")
            print(f"   Created: {created} | Updated: {updated}")
            print(f"   Messages: {conv['messages']}")
            print()

        if len(conversations) > 5:
            print(f"   ... and {len(conversations) - 5} more conversations")
            print()

        print("-" * 50)
        print(f"{len(conversations) + 1}. Start a NEW conversation")
    else:
        print("No saved conversations found.")
        print("1. Start a NEW conversation")

    print("0. Exit")
    print("=" * 50)

    return conversations

def select_conversation():
    """Let user select a conversation or start a new one"""
    conversations = display_conversation_menu()

    while True:
        try:
            choice = input("\nSelect an option (number): ").strip()

            if choice == "0":
                return None, None, None

            choice_num = int(choice)

            # Check if user wants a new conversation
            if choice_num == len(conversations) + 1 or (not conversations and choice_num == 1):
                conversation_id = generate_conversation_id()
                print(f"\n🆕 Starting new conversation with ID: {conversation_id}")
                return conversation_id, [], {"created_at": datetime.now().isoformat()}

            # Load existing conversation
            if 1 <= choice_num <= min(5, len(conversations)):
                conv = conversations[choice_num - 1]
                messages, metadata = load_conversation(conv["id"])
                if messages is not None:
                    print(f"\n📂 Resuming conversation: {conv['id']}")
                    print(f"   Loaded {len(messages)} messages from history")

                    # Show last message to give context
                    if messages:
                        last_msg = messages[-1]
                        preview = last_msg["content"][:100] + "..." if len(last_msg["content"]) > 100 else last_msg["content"]
                        print(f"   Last {last_msg['role']}: {preview}")

                    return conv["id"], messages, metadata

            print("Invalid choice. Please try again.")

        except ValueError:
            print("Please enter a valid number.")

def chat_loop(conversation_id, messages, metadata):
    """Main chat loop with tool use support"""
    print("\n" + "=" * 50)
    print(f"CHAT v3 SESSION - ID: {conversation_id}")
    print("=" * 50)
    print("Commands: 'exit' to quit, 'history' to view history")
    print("Tool available: get_weather (city, country)")
    print("=" * 50)

    # Show conversation context if resuming
    if messages:
        print("\n--- Conversation Context ---")
        # Show last 2 exchanges (4 messages)
        recent = messages[-4:] if len(messages) >= 4 else messages
        for msg in recent:
            role_label = "You" if msg["role"] == "user" else "Claude"
            content = msg["content"]
            if len(content) > 150:
                content = content[:150] + "..."
            print(f"{role_label}: {content}")
        print("--- Continue conversation below ---\n")
    else:
        print("\nStarting new conversation...\n")

    while True:
        # Get user input
        user_input = input("You: ").strip()

        # Handle commands
        if user_input.lower() == 'exit':
            print(f"\nConversation {conversation_id} saved.")
            print("You can resume this conversation anytime!")
            break

        if user_input.lower() == 'history':
            print("\n--- Full Conversation History ---")
            for i, msg in enumerate(messages, 1):
                role_label = "You" if msg["role"] == "user" else "Claude"
                print(f"{i}. {role_label}: {msg['content']}")
            print("--- End of History ---\n")
            continue

        # Skip empty inputs
        if not user_input:
            continue

        # Add user message to conversation
        # For API, we only need role and content
        messages.append({
            "role": "user",
            "content": user_input
        })

        try:
            # Make API call with full conversation history and tools
            print("\nClaude: ", end="", flush=True)

            response = client.messages.create(
                model=MODEL,
                max_tokens=1024,
                system="You are the founder of GrowthX, and your name is Udayan, and you always talk like Yoda! You have access to a weather tool that can fetch current weather data for any city and country. When users ask about weather, use the get_weather tool to provide real-time information.",
                temperature=0.2,
                messages=messages,  # Send entire conversation history
                tools=[WEATHER_TOOL]  # Include the weather tool
            )

            # Check if the response contains tool use
            if response.stop_reason == "tool_use":
                # Process tool use
                tool_results = []
                assistant_content_parts = []

                for content_block in response.content:
                    if content_block.type == "text":
                        # Text content from assistant
                        assistant_content_parts.append(content_block.text)
                        print(content_block.text, end="", flush=True)

                    elif content_block.type == "tool_use":
                        # Tool use request
                        tool_name = content_block.name
                        tool_input = content_block.input
                        tool_use_id = content_block.id

                        print(f"\n[Using tool: {tool_name}]")

                        # Execute the weather tool
                        if tool_name == "get_weather":
                            city = tool_input.get("city_name", "")
                            country = tool_input.get("country_name", "")
                            tool_result = execute_weather_tool(city, country)
                        else:
                            tool_result = f"Unknown tool: {tool_name}"

                        # Store tool result for sending back
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_use_id,
                            "content": tool_result
                        })

                # Add the assistant's message with tool use to history
                messages.append({
                    "role": "assistant",
                    "content": response.content
                })

                # Add tool results as user message
                messages.append({
                    "role": "user",
                    "content": tool_results
                })

                # Make another API call to get final response after tool execution
                print("\n", end="", flush=True)
                final_response = client.messages.create(
                    model=MODEL,
                    max_tokens=1024,
                    system="You are the founder of GrowthX, and your name is Udayan, and you always talk like Yoda! You have access to a weather tool that can fetch current weather data for any city and country. When users ask about weather, use the get_weather tool to provide real-time information.",
                    temperature=0.2,
                    messages=messages,
                    tools=[WEATHER_TOOL]
                )

                # Extract and display final response
                assistant_content = ""
                for content_block in final_response.content:
                    if content_block.type == "text":
                        assistant_content += content_block.text
                        print(content_block.text, end="", flush=True)

                print()  # New line after response

                # Add final assistant response to history
                messages.append({
                    "role": "assistant",
                    "content": assistant_content
                })

            else:
                # Normal text response without tool use
                assistant_content = response.content[0].text
                print(assistant_content)

                # Add assistant message to history
                messages.append({
                    "role": "assistant",
                    "content": assistant_content
                })

            # AUTO-SAVE after each successful user-assistant exchange
            # This is the key feature - persistence after each complete interaction
            save_conversation(conversation_id, messages, metadata)

            print(f"\n[Messages in conversation: {len(messages)}]")
            print("-" * 50)
            print()

        except Exception as e:
            print(f"\nError: {str(e)}")

            # Remove the failed user message to keep conversation clean
            if messages and messages[-1]["role"] == "user":
                messages.pop()

            print("Please try again...\n")

def main():
    """Main application entry point"""
    print("\n" + "=" * 60)
    print("CLAUDE CHAT v3 - Persistent Conversations with Weather Tool")
    print("=" * 60)
    print("✨ Features:")
    print("  • Save and resume conversations")
    print("  • Auto-save after each message exchange")
    print("  • Unique ID for each conversation")
    print("  • Full conversation history preservation")
    print("  • Real-time weather data with get_weather tool")
    print("=" * 60)

    while True:
        # Let user select or create a conversation
        conversation_id, messages, metadata = select_conversation()

        if conversation_id is None:
            print("\nThank you for using Claude Chat v2!")
            break

        # Start the chat loop
        chat_loop(conversation_id, messages, metadata)

        # Ask if user wants to continue with another conversation
        print("\n" + "-" * 50)
        choice = input("Open another conversation? (yes/no): ").strip().lower()
        if choice != 'yes':
            print("\nGoodbye! All conversations have been saved.")
            break

if __name__ == "__main__":
    # Educational information about the system
    print("\n" + "=" * 60)
    print("TUTORIAL: Chat v3 - Persistence & Tool Use")
    print("=" * 60)
    print()
    print("1. CONVERSATION ID:")
    print("   Each conversation gets a unique 8-character ID")
    print("   Example: 'a1b2c3d4'")
    print()
    print("2. STORAGE FORMAT:")
    print("   Messages are saved as JSON files")
    print("   Location: ./conversations_with_tool/conversation_{id}.json")
    print()
    print("3. AUTO-SAVE MECHANISM:")
    print("   After each user message + assistant response")
    print("   Ensures no data loss")
    print()
    print("4. MESSAGE STRUCTURE:")
    print("   Each message contains:")
    print("   - role: 'user' or 'assistant'")
    print("   - content: the actual message text or tool use blocks")
    print("   - timestamp: when the message was sent (for saved messages)")
    print()
    print("5. TOOL FUNCTIONALITY (NEW IN v3!):")
    print("   • Tool: get_weather")
    print("   • Parameters: city_name, country_name")
    print("   • API: Visual Crossing Weather API")
    print("   • Returns: Temperature, Humidity, Wind Speed, Summary")
    print("   ")
    print("   Example queries:")
    print("   - 'What's the weather in Mumbai, India?'")
    print("   - 'Tell me the temperature in Tokyo, Japan'")
    print("   - 'How's the weather in New York, USA?'")
    print()
    print("6. TOOL USE IN MESSAGES:")
    print("   Tool use creates special message blocks:")
    print("   - Assistant: tool_use block with parameters")
    print("   - User: tool_result block with weather data")
    print("   - Assistant: Final response with weather info")
    print()
    print("7. RESUMING CONVERSATIONS:")
    print("   Select from menu to continue where you left off")
    print("   Full context including tool use history is preserved")
    print("=" * 60)

    # Show example JSON structure with tool use
    print("\nExample Conversation with Tool Use:")
    print("-" * 60)
    example = {
        "conversation_id": "4f0f788c",
        "created_at": "2024-11-16T10:00:00",
        "last_updated": "2024-11-16T10:05:00",
        "message_count": 5,
        "messages": [
            {"role": "user", "content": "What's the weather in Mumbai, India?"},
            {"role": "assistant", "content": [
                {"type": "tool_use", "id": "toolu_01...", "name": "get_weather",
                 "input": {"city_name": "Mumbai", "country_name": "India"}}
            ]},
            {"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": "toolu_01...",
                 "content": "Weather for Mumbai: Temp: 28°C, Humidity: 70%..."}
            ]},
            {"role": "assistant", "content": "The weather in Mumbai is warm at 28°C..."}
        ]
    }
    print(json.dumps(example, indent=2))
    print("=" * 60)

    input("\nPress Enter to start the chat application...")

    main()