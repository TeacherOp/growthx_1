# In this file we will understand what is a chat, and how to maintain context in a chat.
# A chat is essentially a sequence of messages between the user and assistant that build on each other.
# The AI remembers previous messages by including them in each API call.

import os
from dotenv import load_dotenv
import anthropic

# Load environment variables from .env file
load_dotenv()

# Initialize the Anthropic client
client = anthropic.Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY"),
)

# Model to use
MODEL = "claude-sonnet-4-5-20250929"

# Just for printing better logs in terminal
def print_separator():
    """Print a visual separator"""
    print("-" * 50)

def main():
    """Main chat loop"""
    print("=" * 50)
    print("CHAT WITH CLAUDE - Terminal Interface")
    print("=" * 50)
    print("Type 'exit' or 'quit' to end the conversation")
    print("Type 'clear' to start a new conversation")
    print("=" * 50)
    print()

    # Initialize the conversation history
    # This list will store all messages to maintain context
    messages = []

    # Chat loop
    while True:
        # Get user input
        user_input = input("You: ").strip()

        # Check for exit commands, this is just checking if you want to quit the chat
        if user_input.lower() in ['exit', 'quit']:
            print("\nGoodbye! Thanks for chatting!")
            break

        # Check for clear command
        if user_input.lower() == 'clear':
            messages = []  # Reset conversation history
            print("\n--- Conversation cleared. Starting fresh! ---\n")
            continue

        # Skip empty inputs
        if not user_input:
            continue

        # Add user message to the conversation history
        messages.append({
            "role": "user",
            "content": user_input
        })

        try:
            # Make API call with the full conversation history
            # This is the key part - we send ALL previous messages to maintain context
            print("\nClaude: ", end="", flush=True)

            response = client.messages.create(
                model=MODEL,
                system="You are the founder of GrowthX, and your name is Udayan, and you always talk like Yoda!",
                temperature=0.1,
                max_tokens=1024,
                messages=messages  # Send the entire conversation history
            )

            # Extract the assistant's response
            assistant_message = response.content[0].text

            # Print the response
            print(assistant_message)
            print()

            # IMPORTANT: Add the assistant's response to the conversation history
            # This ensures the AI remembers what it said in future turns
            messages.append({
                "role": "assistant",
                "content": assistant_message
            })

            # Optional: Show conversation stats
            print(f"[Context: {len(messages)} messages in history]")
            print_separator()
            print()

        except Exception as e:
            print(f"\nError: {str(e)}")
            print("Let's continue our conversation...")
            print_separator()
            print()

            # Remove the last user message if there was an error
            # This prevents corrupting the conversation history
            if messages and messages[-1]["role"] == "user":
                messages.pop()

if __name__ == "__main__":
    # Print a tutorial explanation
    print("\n" + "=" * 50)
    print("HOW CHAT CONTEXT WORKS:")
    print("=" * 50)
    print("1. Each message (user and assistant) is stored in a list")
    print("2. When making an API call, we send ALL previous messages")
    print("3. This allows Claude to 'remember' the conversation")
    print("4. The messages alternate between 'user' and 'assistant' roles")
    print("5. Context grows with each turn of the conversation")
    print("=" * 50)
    print("\nExample conversation flow:")
    print("  Turn 1: [user: 'Hi'] → API → [assistant: 'Hello!']")
    print("  Turn 2: [user: 'Hi', assistant: 'Hello!', user: 'How are you?'] → API")
    print("  Turn 3: All previous messages + new user input → API")
    print("=" * 50)
    print()

    # Start the chat
    main()