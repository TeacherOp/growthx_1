# this the same step 6 but the product manager wants to ensure that the data is backed with realreasearch to align stakeholders
# so they decide to provide a new tool to the script/agent whatever you want to call it, a way to research the web
# luckily claude provides inbuilt tools to do that.
import os
from dotenv import load_dotenv
import anthropic
import csv
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Load environment variables from .env file
load_dotenv()

# Get API key from environment
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
# Model configuration
MODEL = os.environ.get("CLAUDE_MODEL")

# File paths
INPUT_CSV = "step_6_input_data/inputdatasmall.csv"
OUTPUT_CSV = f"step_6_output_data/step_6_output_data_with_citations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

# System prompt template
SYSTEM_PROMPT = """You are an expert AI agent specialized in analyzing skills and determining appropriate technical assessment methods.

Your primary goal is to determine if a discipline and its micro skill require a technical assessment, and if that assessment is possible in our current setup.

IMPORTANT: You MUST use web search to research industry-standard assessment practices for each skill. Search for:
- How the specific skill is assessed in industry interviews
- Standard technical assessment methods for this skill
- Infrastructure requirements for assessing this skill
- Best practices for evaluating proficiency in this skill

Always base your analysis on real research and provide citations for your findings.

Current available information about our system:
    - Frontend:
        - Web-based IDE interface
        - Monaco Editor for code input
        - Multi-language support (Python, JavaScript, Java)
        - Real-time syntax highlighting
        - Submit and test functionality
    - Backend:
        - JDoodle API integration for code execution
        - Test case validation system
        - Async code execution handling
    - Execution Environment:
        - Sandboxed code execution via JDoodle
        - No persistent storage
        - No file system access
        - ~10-15 second timeout limit
        - Limited to standard libraries only

Current Assessment System Constraints:
- Platform: Online web-based IDE interface
- Code Execution: JDoodle API backend
- Languages Supported: Python, JavaScript, Java
- Execution Time Limit: 10-15 seconds maximum
- Libraries: Standard libraries only
- Storage: No file storage or persistence between executions
- Input/Output: Text-only (no visual outputs, charts, or graphics)
- Network: No external API calls from submitted code
- Database: No database connections available
- Data: Small embedded datasets only

Your task:
1. Analyze the given discipline, mega skill, and micro skill
2. Use your knowledge of industry-standard assessment practices for this skill
3. Determine if technical assessment is required
4. Evaluate if the industry-standard assessment can be conducted within our constraints (answer yes or no only)
5. List specific technical assessments needed with infrastructure requirements
6. If assessment is not possible in our system, explain why and what would be needed

Current Skill to Analyze:
- Discipline: {discipline}
- Mega Skill: {mega_skill}
- Micro Skill: {micro_skill}

Based on your knowledge of industry standards, call the return_analysis_result tool with your findings.

IMPORTANT: 
- We need to analyze everything for our current system setup only. Do not suggest any modifications to our current system or deviate from standard assessment practices. as our platform conducts online interview assesments, we need to know what skills can be assesed through our current system and which cant be assesed through our current system.
- Additionally we cant compromoise on industry standard assessment practices, so if our current system cant do it, we need to know what infrastructure is needed to do the standard assesment for that skill.
- We cannot imagine clever workarounds to do the assessment in our current system if its not possible, we need to strictly stick to industry standard assessment practices only.

"""


class SkillAssessmentAgent:
    def __init__(self, api_key: str):
        """Initialize the skill assessment agent"""
        self.client = anthropic.Anthropic(api_key=api_key)
        self.results = []

    def create_return_analysis_tool(self) -> Dict:
        """Create the return_analysis_result tool definition"""
        return {
            "name": "return_analysis_result",
            "description": "Submit the final analysis results for the skill assessment",
            "input_schema": {
                "type": "object",
                "properties": {
                    "discipline_name": {
                        "type": "string",
                        "description": "Name of the discipline"
                    },
                    "mega_skill": {
                        "type": "string",
                        "description": "Name of the mega skill"
                    },
                    "micro_skill": {
                        "type": "string",
                        "description": "Name of the micro skill"
                    },
                    "requires_technical_assessment": {
                        "type": "string",
                        "enum": ["yes", "no"],
                        "description": "Whether this skill requires technical assessment"
                    },
                    "can_assess_in_current_setup": {
                        "type": "string",
                        "enum": ["yes", "no"],
                        "description": "Whether the industry standard assessment can be done in our current setup"
                    },
                    "technical_assessments_required": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "assessment_name": {
                                    "type": "string"
                                },
                                "process_brief": {
                                    "type": "string"
                                },
                                "infra_needs": {
                                    "type": "string"
                                }
                            }
                        },
                        "description": "Array of technical assessments required with process and infrastructure needs"
                    },
                    "reason_cannot_assess": {
                        "type": "string",
                        "description": "If we can't assess in current setup, explain why"
                    },
                    "system_requirements_needed": {
                        "type": "string",
                        "description": "Details of infrastructure needed to assess this skill"
                    },
                    "citations": {
                        "type": "string",
                        "description": "Comma-separated URLs of sources used for the analysis"
                    }
                },
                "required": [
                    "discipline_name",
                    "mega_skill",
                    "micro_skill",
                    "requires_technical_assessment",
                    "can_assess_in_current_setup",
                    "technical_assessments_required",
                    "reason_cannot_assess",
                    "system_requirements_needed",
                    "citations"
                ]
            }
        }

    def analyze_skill(self, discipline: str, mega_skill: str, micro_skill: str) -> Dict:
        """Analyze a single skill using Claude with tools"""
        print(f"\n🔍 Starting analysis for: {discipline} > {mega_skill} > {micro_skill}")

        # Prepare the system prompt with current skill data
        system_prompt = SYSTEM_PROMPT.format(
            discipline=discipline,
            mega_skill=mega_skill,
            micro_skill=micro_skill
        )

        # ============================================================================
        # RATE LIMIT CONFIGURATION: Web Search Tool
        # ============================================================================
        # Understanding token consumption per skill analysis:
        #
        # Token sources:
        # 1. System prompt (SYSTEM_PROMPT above): ~1,500 tokens
        # 2. User messages (lines 199, 227): ~500 tokens total
        # 3. Web search results: ~2,500 tokens PER search
        # 4. Conversation overhead (multi-turn, lines 204-238): ~1,000 tokens
        #    - First API call (line 204)
        #    - Assistant response added to messages (line 219-222)
        #    - Second API call with accumulated context (line 231)
        #
        # Calculation with different max_uses values:
        # - max_uses=5: (5 × 2,500) + 1,500 + 500 + 1,000 = ~15,500 tokens/skill
        # - max_uses=2: (2 × 2,500) + 1,500 + 500 + 1,000 = ~8,500 tokens/skill
        #
        # API Rate Limit: 30,000 input tokens per minute
        # With max_uses=2: Can process ~3.5 skills/minute (30,000 ÷ 8,500)
        #
        # HOW TO ADJUST: If you have higher rate limits or want faster processing:
        # - Increase max_uses for more research depth (but uses more tokens)
        # - Decrease max_uses for faster processing (but less research)
        # - Recalculate delay below using: delay = 60 / (rate_limit ÷ tokens_per_skill)
        # ============================================================================
        tools = [
            self.create_return_analysis_tool(),
            {
                "type": "web_search_20250305",
                "name": "web_search",
                "max_uses": 2  # Balanced for quality research within rate limits
            }
        ]

        try:
            # Initial message to trigger analysis # we can add the variable data to be analysed in the user message or even the system prompt itself, as this is not a conversation but a single analysis task, done multiple times for available data in the csv
            messages = [
                {
                    "role": "user",
                    "content": f"Please analyze the skill '{micro_skill}' under '{mega_skill}' in '{discipline}' discipline. Use web search to research industry standards and assessment practices for this specific skill. Provide citations for all sources used in your analysis. Then use the return_analysis_result tool to provide your findings."
                }
            ]

            # Make API call with tools
            response = self.client.messages.create(
                model=MODEL,
                max_tokens=4000,
                temperature=0.1,
                system=system_prompt,
                messages=messages,
                tools=tools
            )

            # Process response to extract tool results
            analysis_result = self.process_response(response)

            # If no result from first call, continue conversation
            if not analysis_result:
                # Add assistant response to conversation
                messages.append({
                    "role": "assistant",
                    "content": response.content
                })

                # Prompt for final analysis
                messages.append({
                    "role": "user",
                    "content": "Please provide your final analysis using the return_analysis_result tool. Make sure to include all the URLs from your web searches in the citations field as a comma-separated list."
                })

                # Make another call
                response = self.client.messages.create(
                    model=MODEL,
                    max_tokens=4000,
                    temperature=0.1,
                    system=system_prompt,
                    messages=messages,
                    tools=tools
                )

                analysis_result = self.process_response(response)

            if analysis_result:
                print(f"✅ Completed analysis for: {micro_skill}")
                print(f"   - Requires technical assessment: {analysis_result.get('requires_technical_assessment', 'N/A')}")
                print(f"   - Can assess in current setup: {analysis_result.get('can_assess_in_current_setup', 'N/A')}")
                return analysis_result
            else:
                print(f"⚠️  No analysis result returned for: {micro_skill}")
                return self.create_error_result(discipline, mega_skill, micro_skill, "No analysis result returned")

        except Exception as e:
            print(f"❌ Error analyzing {micro_skill}: {str(e)}")
            return self.create_error_result(discipline, mega_skill, micro_skill, str(e))

    def process_response(self, response) -> Dict:
        """Extract the return_analysis_result tool call from response"""
        for content in response.content:
            if hasattr(content, 'type') and content.type == 'tool_use':
                if content.name == 'return_analysis_result':
                    return content.input
        return None

    def create_error_result(self, discipline: str, mega_skill: str, micro_skill: str, error: str) -> Dict:
        """Create an error result entry"""
        return {
            "discipline_name": discipline,
            "mega_skill": mega_skill,
            "micro_skill": micro_skill,
            "requires_technical_assessment": "error",
            "can_assess_in_current_setup": "error",
            "technical_assessments_required": [],
            "reason_cannot_assess": f"Error: {error}",
            "system_requirements_needed": "Error occurred during analysis",
            "citations": ""  # Empty citations for error cases
        }

    def save_result_to_csv(self, result: Dict, filename: str):
        """Save a single result to CSV file (append mode)"""
        # Create output directory if it doesn't exist
        output_dir = Path(filename).parent
        output_dir.mkdir(parents=True, exist_ok=True)

        # Flatten technical assessments for CSV
        tech_assessments = result.get('technical_assessments_required', [])
        tech_assessments_str = json.dumps(tech_assessments) if tech_assessments else ""

        # Prepare row data
        row_data = {
            'discipline_name': result.get('discipline_name', ''),
            'mega_skill': result.get('mega_skill', ''),
            'micro_skill': result.get('micro_skill', ''),
            'requires_technical_assessment': result.get('requires_technical_assessment', ''),
            'can_assess_in_current_setup': result.get('can_assess_in_current_setup', ''),
            'technical_assessments_required': tech_assessments_str,
            'reason_cannot_assess': result.get('reason_cannot_assess', ''),
            'system_requirements_needed': result.get('system_requirements_needed', ''),
            'timestamp': datetime.now().isoformat(),
            'citations': result.get('citations', '')  # Add citations column
        }

        # Check if file exists to determine if we need headers
        file_exists = Path(filename).exists()

        # Write to CSV
        with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = list(row_data.keys())
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            # Write header only if file doesn't exist
            if not file_exists:
                writer.writeheader()

            writer.writerow(row_data)

        print(f"💾 Result saved to {filename}")

    def run_analysis(self, input_csv: str, output_csv: str):
        """Run analysis for all skills in the input CSV"""
        print(f"\n🚀 Starting skill assessment analysis")
        print(f"📂 Input file: {input_csv}")
        print(f"📂 Output file: {output_csv}")
        print("-" * 50)

        try:
            # Read input CSV
            with open(input_csv, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                rows = list(reader)
                total_rows = len(rows)

                print(f"📊 Found {total_rows} skills to analyze")

                # Process each row
                for idx, row in enumerate(rows, 1):
                    print(f"\n[{idx}/{total_rows}] Processing skill...")

                    # Extract skill data (matching actual CSV column names)
                    discipline = row.get('Discipline', '').strip()
                    mega_skill = row.get('Megaskill', '').strip()
                    micro_skill = row.get('Microskill', '').strip()

                    if not all([discipline, mega_skill, micro_skill]):
                        print(f"⚠️  Skipping row {idx}: Missing required fields")
                        continue

                    # Analyze the skill
                    result = self.analyze_skill(discipline, mega_skill, micro_skill)

                    # Save result immediately
                    self.save_result_to_csv(result, output_csv)

                    # ================================================================
                    # RATE LIMIT CONFIGURATION: Delay Between Skills
                    # ================================================================
                    # Purpose: Prevent hitting API rate limits by pacing requests
                    #
                    # Current setup (from token calculation in analyze_skill method):
                    # - API rate limit: 30,000 input tokens per minute
                    # - Tokens per skill: ~8,500 tokens (see breakdown above at line 187-200)
                    # - Theoretical max: 30,000 ÷ 8,500 = 3.5 skills per minute
                    #
                    # With 30-second delay:
                    # - Skills per minute: 60 seconds ÷ 30 seconds = 2 skills/minute
                    # - Token usage: 2 × 8,500 = 17,000 tokens/minute
                    # - Safety buffer: 30,000 - 17,000 = 13,000 tokens (43% margin)
                    #
                    # HOW TO CALCULATE YOUR OWN DELAY:
                    # Step 1: Determine your tokens per skill (see calculation above)
                    # Step 2: Decide safety margin (e.g., 80% of limit = safe)
                    # Step 3: Calculate: delay = 60 / (rate_limit × 0.8 / tokens_per_skill)
                    # Example: delay = 60 / (30,000 × 0.8 / 8,500) = 60 / 2.82 ≈ 21 seconds
                    #
                    # Adjust this delay based on:
                    # - Your organization's rate limit (check API dashboard)
                    # - Your max_uses setting (more searches = more tokens)
                    # - Desired safety margin (higher = slower but safer)
                    # ================================================================
                    if idx < total_rows:
                        time.sleep(30)

                print(f"\n✨ Analysis complete! Results saved to {output_csv}")

        except FileNotFoundError:
            print(f"❌ Error: Input file '{input_csv}' not found")
        except Exception as e:
            print(f"❌ Error during analysis: {str(e)}")


def main():
    """Main entry point"""
    print("=" * 50)
    print("SKILL ASSESSMENT AI AGENT")
    print("=" * 50)

    # Check if input file exists
    if not Path(INPUT_CSV).exists():
        print(f"❌ Error: Input file '{INPUT_CSV}' not found")
        print("\nPlease create an input CSV file with the following columns:")
        print("- Discipline")
        print("- Megaskill")
        print("- Microskill")
        return

    # Initialize agent
    agent = SkillAssessmentAgent(api_key=ANTHROPIC_API_KEY)

    # Run analysis
    agent.run_analysis(INPUT_CSV, OUTPUT_CSV)


if __name__ == "__main__":
    main()