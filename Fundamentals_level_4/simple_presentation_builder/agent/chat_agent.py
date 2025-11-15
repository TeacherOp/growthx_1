"""
Chat Agent - Interacts with user and orchestrates presentation generation

This agent handles the main conversation with the user, gathering requirements
and coordinating with the Presentation Agent to create slides.
"""

import anthropic
import os
import base64
from typing import Dict, List, Optional
from .tools import MAIN_CHAT_TOOLS
from .presentation_agent import PresentationAgent


class ChatAgent:
    """
    Chat Agent that collects user requirements and generates presentations

    This is the main orchestration agent that:
    1. Handles conversation with the user
    2. Gathers presentation requirements
    3. Calls the Presentation Agent to generate slides
    """

    def __init__(self, api_key: str = None, progress_callback=None):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.messages = []
        self.progress_callback = progress_callback
        self.presentation_agent = None  # Will be created with progress callback when needed

    def _emit_progress(self, event_type: str, data: dict):
        """Emit a progress event if callback is set"""
        if self.progress_callback:
            self.progress_callback(event_type, data)

    def start_conversation(self, initial_message: str, images: Optional[List[str]] = None):
        """
        Start a conversation with the AI

        Args:
            initial_message: User's first message
            images: Optional list of image file paths to analyze
        """

        # Build the first message with optional images
        first_message = self._build_message_with_images(initial_message, images)

        self.messages = [first_message]

        print("\n" + "="*60)
        print("💬 Main AI Chat Started")
        print("="*60)
        print(f"\nYou: {initial_message}\n")

        # Start the conversation loop
        return self._conversation_loop()

    def send_message(self, message: str, images: Optional[List[str]] = None) -> str:
        """
        Send a message in an ongoing conversation

        Args:
            message: User message
            images: Optional list of image file paths

        Returns:
            AI response
        """

        # Add user message
        user_message = self._build_message_with_images(message, images)
        self.messages.append(user_message)

        print(f"\nYou: {message}\n")

        return self._conversation_loop()

    def _conversation_loop(self) -> str:
        """
        Main conversation loop that handles tool use

        Returns:
            AI's response to the user
        """

        max_iterations = 10
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            # Make API request
            response = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=16000,
                temperature=0,
                system=self._get_system_prompt(),
                tools=MAIN_CHAT_TOOLS,
                messages=self.messages
            )

            # Check if AI wants to use tools
            if response.stop_reason == "tool_use":
                # Process tool use
                tool_results, ppt_generated = self._process_tool_use(response)

                # Add assistant response and tool results
                self.messages.append({
                    "role": "assistant",
                    "content": response.content
                })

                self.messages.append({
                    "role": "user",
                    "content": tool_results
                })

                # If PPT was generated, we might want to show a special message
                if ppt_generated:
                    # Continue to get AI's final response
                    continue

            else:
                # AI gave a final response - extract and return it
                response_text = self._extract_text_response(response)

                # Add to conversation history
                self.messages.append({
                    "role": "assistant",
                    "content": response.content
                })

                print(f"🤖 AI: {response_text}\n")
                return response_text

        # Max iterations reached
        return "Sorry, I encountered an issue. Please try again."

    def _build_message_with_images(self, text: str, images: Optional[List[str]] = None) -> Dict:
        """Build a message with optional images"""

        if not images:
            return {
                "role": "user",
                "content": text
            }

        # Build content with images
        content = []

        # Add images first
        for image_path in images:
            image_content = self._encode_image(image_path)
            if image_content:
                content.append(image_content)

        # Add text
        content.append({
            "type": "text",
            "text": text
        })

        return {
            "role": "user",
            "content": content
        }

    def _encode_image(self, image_path: str) -> Optional[Dict]:
        """Encode an image file to base64 for the API"""

        try:
            # Check if file exists
            if not os.path.exists(image_path):
                print(f"⚠️  Image file not found: {image_path}")
                print(f"   Please check the path and try again")
                return None

            # Determine media type
            if image_path.lower().endswith('.png'):
                media_type = "image/png"
            elif image_path.lower().endswith(('.jpg', '.jpeg')):
                media_type = "image/jpeg"
            elif image_path.lower().endswith('.gif'):
                media_type = "image/gif"
            elif image_path.lower().endswith('.webp'):
                media_type = "image/webp"
            else:
                print(f"⚠️  Unsupported image format: {image_path}")
                return None

            # Read and encode
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')

            print(f"✅  Successfully loaded image: {image_path}")

            return {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": media_type,
                    "data": image_data
                }
            }

        except Exception as e:
            print(f"⚠️  Error encoding image {image_path}: {str(e)}")
            return None

    def _process_tool_use(self, response) -> tuple:
        """
        Process tool use requests

        Returns:
            (tool_results, ppt_generated)
        """

        tool_results = []
        ppt_generated = False

        for block in response.content:
            if block.type == "tool_use":
                tool_name = block.name
                tool_input = block.input

                print(f"\n🔧 Using tool: {tool_name}")

                # Execute the tool
                if tool_name == "generate_ppt":
                    result, ppt_generated = self._execute_generate_ppt(tool_input)
                elif tool_name == "web_search":
                    # Web search is server-side, we shouldn't need to execute it
                    # This shouldn't happen, but handle it gracefully
                    result = "Web search completed (server-side)"
                else:
                    result = f"Unknown tool: {tool_name}"

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result
                })

        return tool_results, ppt_generated

    def _execute_generate_ppt(self, tool_input: Dict) -> tuple:
        """
        Execute the generate_ppt tool by calling PPT Agent

        Returns:
            (result_message, success)
        """

        print("\n" + "-"*60)
        print("📊 Triggering PPT Generation...")
        print("-"*60)

        self._emit_progress('generate_ppt_started', {
            'message': '📊 Triggering PPT Generation...',
            'topic': tool_input.get('ppt_topic', 'Unknown')
        })

        try:
            # Create Presentation Agent with progress callback
            self.presentation_agent = PresentationAgent(api_key=self.api_key, progress_callback=self.progress_callback)

            # Call the Presentation Agent
            result = self.presentation_agent.generate_presentation(tool_input)

            if result["success"]:
                # Build success message
                message = f"""Successfully generated presentation!

Slide count: {result['slide_count']}
Files created: {', '.join(result['slide_files'])}

{result['message']}

"""
                # Add PPTX info if available
                if result.get('pptx_file'):
                    message += f"""📊 PPTX File: {result['pptx_file']}
   You can open this file in PowerPoint or Keynote!

"""

                message += """💡 You can also view individual HTML slides in your browser:
   Open any slide file (e.g., input_output_data/slides/slide_1.html) directly!
"""
                return message, True
            else:
                return f"Failed to generate presentation: {result['message']}", False

        except Exception as e:
            return f"Error generating presentation: {str(e)}", False

    def _extract_text_response(self, response) -> str:
        """Extract text from response content"""

        text_parts = []

        for block in response.content:
            if hasattr(block, "text"):
                text_parts.append(block.text)

        return "\n".join(text_parts)

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the main chat"""

        return """You are an AI assistant specialized in helping users create PowerPoint presentations.

Your role is to:
1. Engage in friendly conversation with the user
2. Gather all necessary information about their presentation needs through back-and-forth conversation
3. Ask clarifying questions to understand their requirements
4. Collect optional brand information if available
5. Use web search when you need current information
6. Analyze any images provided for brand colors, logo details, design style
7. Call the generate_ppt tool ONLY after you have asked questions AND received answers from the user

CRITICAL - CONVERSATION FIRST:
- DO NOT call generate_ppt on the first message
- ALWAYS ask clarifying questions first, even if you think you have enough information
- WAIT for the user to answer your questions
- Have a back-and-forth conversation to understand their needs
- Only call generate_ppt after at least 2-3 exchanges with the user

REQUIRED INFORMATION before calling generate_ppt:
- ppt_topic: The main topic/title of the presentation
- ppt_description: Brief description and purpose
- ppt_details: Detailed content outline, key points, structure (must be comprehensive, not vague)
- ppt_data: Specific data, statistics, numbers, metrics
- brand_color_details: Brand colors in hex format
- brand_logo_details: Logo file path and description
- brand_guideline_details: Brand tone, voice, style, fonts
- Specific business details (fundraising amount, target audience, key metrics, etc.)
- If the user doesnt provide data perform web search usiong the web_search tool to get required data
- You can also use the websearch tool to get current brand guidleines data and any style insipiration ftom the brands website

CRITICAL - IMAGE ANALYSIS:
When the user provides images (logo, screenshots, etc.):
1. Carefully analyze each image for:
   - Brand colors (extract hex codes if possible)
   - Logo style and characteristics
   - Design patterns and aesthetics
   - Typography and layout style
2. INCLUDE this analysis in the brand_color_details, brand_logo_details, and brand_guideline_details
3. Be specific: example - "Logo shows a blue shopping bag (#146EB4), clean modern sans-serif font, minimalist design" 

IMPORTANT GUIDELINES:
- Be conversational and helpful
- ALWAYS ask follow-up questions - don't assume you have enough information
- When images are provided, analyze them but STILL ask questions about the content
- Use web search to find current data if needed
- Never rush to generate - take time to understand the user's needs fully
- When calling generate_ppt, include detailed information gathered from conversation and image analysis

Remember: The goal is to have a helpful conversation, not to rush to generation. Ask questions, gather details, and only then create the presentation!
"""
