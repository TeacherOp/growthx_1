# In this we will improve the chat, by storing the data, so we can continue a chat, by loading previous messages, and adding new messages to it.
# This version saves conversations after each exchange and allows resuming previous chats

import os
import json
import uuid
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

# Model to use
MODEL = os.environ.get("CLAUDE_MODEL")

# Directory to store conversations
CONVERSATIONS_DIR = "conversations"

def ensure_conversations_dir():
    """Create conversations directory if it doesn't exist"""
    Path(CONVERSATIONS_DIR).mkdir(exist_ok=True)

def generate_conversation_id():
    """Generate a unique conversation ID"""
    return str(uuid.uuid4())[:8]  # Use first 8 characters for simplicity

def save_conversation(conversation_id, messages, metadata=None):
    """Save conversation to a JSON file after each exchange"""
    ensure_conversations_dir()

    conversation_data = {
        "conversation_id": conversation_id,
        "created_at": metadata.get("created_at") if metadata else datetime.now().isoformat(),
        "last_updated": datetime.now().isoformat(),
        "message_count": len(messages),
        "messages": messages
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
    """Display menu for selecting conversations"""
    print("\n" + "=" * 50)
    print("CONVERSATION MENU")
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
    """Main chat loop with a specific conversation"""
    print("\n" + "=" * 50)
    print(f"CHAT SESSION - ID: {conversation_id}")
    print("=" * 50)
    print("Commands: 'exit' to quit, 'history' to view history")
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

        # Add user message to conversation with metadata
        user_message = {
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now().isoformat()
        }

        # For API, we only need role and content
        messages.append({
            "role": "user",
            "content": user_input
        })

        try:
            # Make API call with full conversation history
            print("\nClaude: ", end="", flush=True)

            response = client.messages.create(
                model=MODEL,
                max_tokens=1024,
                system="You are the founder of GrowthX, and your name is Udayan, and you always talk like Yoda!",
                temperature=0.2,
                messages=messages  # Send entire conversation history
            )

            # Extract and display response
            assistant_content = response.content[0].text
            print(assistant_content)

            # Add assistant message to history
            assistant_message = {
                "role": "assistant",
                "content": assistant_content,
                "timestamp": datetime.now().isoformat()
            }

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
    print("CLAUDE CHAT v2 - Persistent Conversations")
    print("=" * 60)
    print("✨ Features:")
    print("  • Save and resume conversations")
    print("  • Auto-save after each message exchange")
    print("  • Unique ID for each conversation")
    print("  • Full conversation history preservation")
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
    print("TUTORIAL: How Conversation Persistence Works")
    print("=" * 60)
    print()
    print("1. CONVERSATION ID:")
    print("   Each conversation gets a unique 8-character ID")
    print("   Example: 'a1b2c3d4'")
    print()
    print("2. STORAGE FORMAT:")
    print("   Messages are saved as JSON files")
    print("   Location: ./conversations/conversation_{id}.json")
    print()
    print("3. AUTO-SAVE MECHANISM:")
    print("   After each user message + assistant response")
    print("   Ensures no data loss")
    print()
    print("4. MESSAGE STRUCTURE:")
    print("   Each message contains:")
    print("   - role: 'user' or 'assistant'")
    print("   - content: the actual message text")
    print("   - timestamp: when the message was sent")
    print()
    print("5. RESUMING CONVERSATIONS:")
    print("   Select from menu to continue where you left off")
    print("   Full context is maintained")
    print("=" * 60)

    # Show example JSON structure
    print("\nExample Saved Conversation Structure:")
    print("-" * 60)
    example = {
        "conversation_id": "a1b2c3d4",
        "created_at": "2024-01-01T10:00:00",
        "last_updated": "2024-01-01T10:30:00",
        "message_count": 4,
        "messages": [
            {"role": "user", "content": "Hello Claude!"},
            {"role": "assistant", "content": "Hello! How can I help you today?"},
            {"role": "user", "content": "What's 2+2?"},
            {"role": "assistant", "content": "2+2 equals 4."}
        ]
    }
    print(json.dumps(example, indent=2))
    print("=" * 60)

    input("\nPress Enter to start the chat application...")

    main()