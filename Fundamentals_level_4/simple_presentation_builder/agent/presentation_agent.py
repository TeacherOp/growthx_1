"""
Presentation Agent - Generates HTML slides using AI and file creation tools

This agent is responsible for the actual presentation generation process,
using tools to create HTML slides and convert them to PowerPoint format.
"""

import anthropic
import os
from typing import Dict, List
from pathlib import Path
from .tools import PPT_AGENT_TOOLS
from .tool_executor import PPTToolExecutor
from utils.screenshot import capture_slide_screenshots
from utils.export import create_pptx_from_screenshots
from config import Config


class PresentationAgent:
    """
    AI Agent that generates PowerPoint slides as HTML files

    This agent uses an agentic loop to:
    1. Plan slide structure based on requirements
    2. Generate individual slides as HTML files
    3. Capture screenshots of each slide
    4. Export to PowerPoint format (.pptx)
    """

    def __init__(self, api_key: str = None, progress_callback=None):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.client = anthropic.Anthropic(api_key=self.api_key)
        # Tool executor uses DATA_DIR as base path for all file operations
        self.tool_executor = PPTToolExecutor(base_path=str(Config.DATA_DIR))
        self.messages = []
        self.progress_callback = progress_callback

    def _emit_progress(self, event_type: str, data: dict):
        """Emit a progress event if callback is set"""
        if self.progress_callback:
            self.progress_callback(event_type, data)

    def generate_presentation(self, ppt_data: Dict) -> Dict:
        """
        Generate a presentation based on the provided data

        Args:
            ppt_data: Dictionary containing:
                - ppt_topic: str
                - ppt_description: str
                - ppt_details: str
                - ppt_data: str (optional)
                - brand_logo_details: str (optional)
                - brand_guideline_details: str (optional)
                - brand_color_details: str (optional)

        Returns:
            Result dictionary with success status and slide information
        """

        # Build the initial prompt for the PPT Agent
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(ppt_data)

        # Initialize conversation
        self.messages = [
            {"role": "user", "content": user_prompt}
        ]

        print("\n" + "="*60)
        print("🤖 PPT AI Agent Started")
        print("="*60)
        print(f"\nGenerating presentation: {ppt_data['ppt_topic']}\n")

        self._emit_progress('agent_started', {
            'message': f"🤖 PPT AI Agent Started",
            'topic': ppt_data['ppt_topic']
        })

        # Agent loop - continues until return_ppt_result is called
        max_iterations = 30
        iteration = 0
        final_result = None

        while iteration < max_iterations:
            iteration += 1
            print(f"\n--- Iteration {iteration} ---")
            self._emit_progress('iteration', {'iteration': iteration})

            # Make API request
            response = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=4000,
                temperature=0,
                system=system_prompt,
                tools=PPT_AGENT_TOOLS,
                tool_choice={"type": "any"},  # Force the model to use a tool
                messages=self.messages
            )

            # Check if agent wants to use tools
            if response.stop_reason == "tool_use":
                # Process tool use
                tool_results = self._process_tool_use(response)

                # Check if agent returned final result
                if self._is_generation_complete(tool_results):
                    final_result = self._extract_final_result(tool_results)

                    # Export to PPTX if generation was successful
                    if final_result.get("success") and final_result.get("slide_files"):
                        final_result = self._export_to_pptx(final_result, ppt_data.get('ppt_topic', 'Presentation'))

                    break

                # Add assistant message and tool results to conversation
                self.messages.append({
                    "role": "assistant",
                    "content": response.content
                })

                self.messages.append({
                    "role": "user",
                    "content": tool_results
                })

            else:
                # Agent finished without using tools (shouldn't happen in normal flow)
                print("\n⚠️  Agent finished without calling return_ppt_result")
                response_text = ""
                for block in response.content:
                    if hasattr(block, "text"):
                        response_text += block.text

                final_result = {
                    "success": False,
                    "message": f"Agent stopped unexpectedly: {response_text}",
                    "slide_count": 0,
                    "slide_files": []
                }
                break

        if iteration >= max_iterations:
            print("\n⚠️  Max iterations reached")
            final_result = {
                "success": False,
                "message": "Max iterations reached without completion",
                "slide_count": 0,
                "slide_files": []
            }

        print("\n" + "="*60)
        print("✅ PPT AI Agent Finished")
        print("="*60)
        print(f"Result: {final_result}\n")

        return final_result

    def _build_system_prompt(self) -> str:
        """Build the system prompt for the PPT Agent"""
        return """You are an expert presentation designer who creates HTML slides that will be screenshotted and exported to PowerPoint.

=== CRITICAL TECHNICAL CONSTRAINTS ===

**EXACT SLIDE DIMENSIONS (NON-NEGOTIABLE):**
- Browser viewport: 1920x1080px (screenshots capture this exact viewport)
- Use FULL viewport width and height (100vw × 100vh)
- EVERYTHING must fit within the SAFEBOX AREA - NO SCROLLING, NO OVERFLOW
- Safebox area: viewport minus padding (content must stay within this safe zone to prevent edge cutoff)

**HTML STRUCTURE (REQUIRED FOR EVERY SLIDE):**
```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/7.0.1/css/all.min.css">
    <link rel="stylesheet" href="base-styles.css">
</head>
<body class="m-0 p-0 w-screen h-screen overflow-hidden">
    <div class="w-full h-full overflow-hidden flex items-center justify-center p-20">
        <!-- SAFEBOX AREA: All slide content goes here -->
        <!-- Content MUST fit within this padded container -->
        <!-- p-20 = 80px padding on all sides = safebox of ~1760px × ~920px -->
    </div>
</body>
</html>
```

**SAFEBOX AREA CONCEPT (CRITICAL):**
- Outer container: `w-screen h-screen` (100vw × 100vh = full viewport)
- Inner container: Add `p-16` (64px) or `p-20` (80px) padding to create SAFEBOX
- ALL content must fit within the safebox - prevents edge cutoff during screenshot
- Safebox with p-20 padding: ~1760px wide × ~920px tall (usable area)
- Think of safebox as your canvas boundaries - NEVER let content overflow outside it

**TAILWIND CSS FIRST (MANDATORY):**
- Use Tailwind utility classes for ALL styling (spacing, colors, layout, typography)
- ONLY write custom CSS in base-styles.css for brand-specific styles (fonts, brand colors as CSS variables)
- NO custom CSS in individual slide files - use Tailwind classes exclusively
- NO inline styles - use Tailwind classes

**PREVENTING CONTENT OVERFLOW (CRITICAL):**
1. **Container padding:** Use `p-16` or `p-20` (64-80px) on the main content container to ensure safe margins from all edges
2. **Maximum content area:** With padding, your usable area is ~1760px wide × ~920px tall - design within this
3. **Text sizing:** Headings max `text-6xl`, body text `text-xl` or `text-2xl`, ensure line-height doesn't cause overflow
4. **List limits:** Maximum 5-6 bullet points per slide, use `space-y-4` or `space-y-6` for vertical spacing
5. **Grid/Column layouts:** Use `grid grid-cols-2 gap-12` for two-column, ensure each column fits within ~450px height
6. **Images/Icons:** Size appropriately - large icons `text-6xl`, images `max-h-[400px]`
7. **Vertical space check:** Total height = padding-top + heading + spacing + content + spacing + padding-bottom ≤ 1080px

**DESIGN PRINCIPLES:**
- Think PowerPoint, not website: generous whitespace, limited content per slide
- Prioritize readability: large text, clear hierarchy, strategic color use
- Better to split into 2 slides than overflow 1 slide
- Use flex/grid with `items-center` and `justify-center` for centering
- Test mentally: "Will this fit comfortably in 1080px height?"

=== WORKFLOW (FOLLOW IN ORDER) ===

**Step 1: Create base-styles.css**
- Define CSS custom properties for brand colors (--brand-primary, --brand-secondary, etc.)
- Import brand fonts from Google Fonts if specified
- Add minimal global styles (body reset only)
- Keep it under 50 lines - Tailwind handles the rest

Example base-styles.css:
```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

:root {
  --brand-primary: #FF5722;
  --brand-secondary: #333333;
}

body {
  margin: 0;
  padding: 0;
  font-family: 'Inter', sans-serif;
}
```

**Step 2: Create individual slides**
- Use the exact HTML structure shown above for EVERY slide
- Body must be: `<body class="m-0 p-0 w-screen h-screen overflow-hidden">`
- Content container must be: `<div class="w-full h-full overflow-hidden flex items-center justify-center p-20">`
- All content goes inside the p-20 container (this is your SAFEBOX)
- Use only Tailwind classes for styling
- Before creating each slide, verify content fits within ~1760px × ~920px safebox

**Step 3: Call return_ppt_result**
- Verify all slides use exact structure
- Confirm no custom CSS in individual slides

=== ABSOLUTE RULES ===
✅ DO:
1. Create base-styles.css FIRST before any slides
2. Use viewport-based containers: body = `w-screen h-screen`, inner div = `w-full h-full`
3. ALWAYS include `p-20` padding on the content container to create the SAFEBOX
4. Use ONLY Tailwind classes for all styling (except base-styles.css)
5. Keep ALL content within the safebox (~1760px × ~920px with p-20)
6. Limit content quantity - better 10 clean slides than 5 overflowing slides
7. Use Tailwind color classes or CSS variables from base-styles.css

❌ DON'T:
1. NO animations, transitions, hover effects, JavaScript
2. NO custom CSS in individual slide files (only in base-styles.css)
3. NO inline styles or <style> tags in slide HTML
4. NO content overflow - if it doesn't fit, split into multiple slides
5. NO cramming - respect whitespace and margins
6. NO vague sizing - use exact Tailwind classes (p-20, text-4xl, etc.)

**SAFEBOX OVERFLOW PREVENTION CHECKLIST:**
Before creating each slide, verify:
- [ ] Body uses `w-screen h-screen overflow-hidden`?
- [ ] Content container uses `w-full h-full` with `p-20` padding (creates SAFEBOX)?
- [ ] ALL content fits within safebox area (~1760px × ~920px with p-20)?
- [ ] Total content height ≤ 920px (accounting for 80px top+bottom padding)?
- [ ] Using Tailwind classes exclusively (no custom CSS in slide file)?
- [ ] Heading + body + spacing fits comfortably within safebox?
- [ ] No more than 5-6 list items to prevent vertical overflow?
- [ ] Text sizes appropriate (headings ≤ text-6xl, body ≤ text-2xl)?
- [ ] Content will NOT overflow beyond viewport edges when screenshotted?

START WITH base-styles.css NOW!
"""

    def _build_user_prompt(self, ppt_data: Dict) -> str:
        """Build the user prompt with PPT requirements"""

        prompt = f"""Please generate a presentation with the following details:

**Topic**: {ppt_data['ppt_topic']}

**Description**: {ppt_data['ppt_description']}

**Details**: {ppt_data['ppt_details']}

**Data/Statistics**: {ppt_data.get('ppt_data', 'N/A')}
**Brand Colors**: {ppt_data.get('brand_color_details', 'N/A')}
**Logo Details**: {ppt_data.get('brand_logo_details', 'N/A')}
**Brand Guidelines**: {ppt_data.get('brand_guideline_details', 'N/A')}
"""
        return prompt

    def _process_tool_use(self, response) -> List[Dict]:
        """Process tool use requests from the agent"""

        tool_results = []

        for block in response.content:
            if block.type == "tool_use":
                tool_name = block.name
                tool_input = block.input

                print(f"\n🔧 Tool: {tool_name}")
                print(f"   Input: {tool_input}")

                # Emit tool use event
                self._emit_progress('tool_use', {
                    'tool': tool_name,
                    'input': tool_input
                })

                # Execute the tool
                result = self.tool_executor.execute_tool(tool_name, tool_input)

                print(f"   Result: {result[:200]}..." if len(result) > 200 else f"   Result: {result}")

                # Emit tool result event
                self._emit_progress('tool_result', {
                    'tool': tool_name,
                    'result': result[:200] if len(result) > 200 else result
                })

                # Check if it's an error
                is_error = result.startswith("Error:")

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                    "is_error": is_error
                })

        return tool_results

    def _is_generation_complete(self, tool_results: List[Dict]) -> bool:
        """Check if the agent called return_ppt_result"""
        for result in tool_results:
            if "PPT_GENERATION_COMPLETE" in result.get("content", ""):
                return True
        return False

    def _extract_final_result(self, tool_results: List[Dict]) -> Dict:
        """Extract the final result from return_ppt_result"""
        import json

        for result in tool_results:
            content = result.get("content", "")
            if "PPT_GENERATION_COMPLETE" in content:
                # Extract JSON part
                json_part = content.split("PPT_GENERATION_COMPLETE:")[1].strip()
                return json.loads(json_part)

        return {
            "success": False,
            "message": "Could not extract final result",
            "slide_count": 0,
            "slide_files": []
        }

    def _export_to_pptx(self, result: Dict, presentation_title: str) -> Dict:
        """
        Export HTML slides to PPTX

        Args:
            result: Result dictionary from return_ppt_result
            presentation_title: Title of the presentation

        Returns:
            Updated result dictionary with PPTX file path
        """
        try:
            print("\n" + "="*60)
            print("📤 Exporting to PPTX")
            print("="*60)

            self._emit_progress('export_started', {
                'message': '📤 Exporting to PPTX'
            })

            slide_files = result["slide_files"]

            self._emit_progress('capturing_screenshots', {
                'message': '📸 Capturing screenshots...',
                'slide_count': len(slide_files)
            })

            # Capture screenshots using configured path
            screenshots = capture_slide_screenshots(
                slide_files,
                output_dir=str(Config.SCREENSHOTS_FOLDER),
                progress_callback=self._emit_progress
            )

            if not screenshots:
                print("⚠️  No screenshots captured, skipping PPTX export")
                return result

            # Create PPTX using configured path
            self._emit_progress('creating_pptx', {
                'message': '📊 Creating PPTX presentation...'
            })

            output_filename = f"{presentation_title.replace(' ', '_')}.pptx"
            output_path = Config.EXPORTS_FOLDER / output_filename

            pptx_file = create_pptx_from_screenshots(
                screenshots,
                output_file=str(output_path),
                presentation_title=presentation_title,
                progress_callback=self._emit_progress
            )

            # Add PPTX file to result
            result["pptx_file"] = pptx_file
            result["screenshots"] = screenshots

            self._emit_progress('export_complete', {
                'message': f'✅ PPTX created: {pptx_file}'
            })

            return result

        except Exception as e:
            print(f"❌ Error exporting to PPTX: {str(e)}")
            import traceback
            traceback.print_exc()
            # Return original result even if export fails
            return result
