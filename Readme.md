# A Practical Guide to Building AI Tools & Agents ( For Non Developers )

- This is a readme file, its a doc / notion file for developers, its the same thing
- Why is everything shared here, you need to download this repo to pratice / learn whatever was taught in this session.
- In one session we were not able to cover or reach levl 4 & 5 which are more complex automations & ageents
- You need to understand how level 1,2 & 3 to be able to grasp or understand worklows & 

## Session 1 Goal

- Click on the image link
![alt text](<Notes_Session_1/Session_1.png>)

## Unvavoidable Learning Curve for code or nocode tools, if you want to build your own AI tools / Agents / Automations

- You can't avoid this learning curve, if you want to use no code tools like zapier, n8n, the learning curve is almost the same, but you get limited to a platform, following a template, without understanding the basics.
- You can spend the same time here, and still be able to use no code tools, switch to any tool you want, as basics of building ai tools / automations / agents are same.

- Click on the image link
![alt text](<Notes_Session_1//learningcurve_realtity/realisticlearningcurve.jpeg>)

![alt text](<Notes_Session_1//learningcurve_realtity/learningcurvedefinitions.jpeg>)

## Get Started.

- Visit the folder "Notes - Start Here"
   - Meeting Notes
   - Session 1 Goal - "Session_1.png"
   - Excpected Learning Curve - folder -> "learningcurve_reality
   - Additional Learning Resources - The OG Resources from OpenAI & Anthropic
   - Session Recording & Meeting Notes if you want to read a google doc.
      - https://docs.google.com/document/d/1ycOjVEvzYEleJsINHzO8C7WaynkQFywcbRBL9sV-K70/edit?usp=sharing
      - https://drive.google.com/file/d/1eBJ7R-Z-nFIhFF8B1Zr5LIkums2-62t2/view?usp=sharing
         - I already watched it again ( New Drinking game & or nickname "Fundamental" :?? oops sorry i was thinking too much about fundamentals, and ended up saying "Fundamental" 95 times in 134 minuntes Enjoy )
      - QA asked during meet -> https://docs.google.com/spreadsheets/d/1Jx1ueVTdfSa8AcqyQ3llkJbkXz7jjyjJFqysPceq854/edit?usp=sharing
   - By: https://x.com/NeelSeth7 & https://growthx.club/ 
   - Leave Your Feedback At: [https](https://growthx.club/events/690455e57442138c9d6ece7d?feedback=true):

- Non - Developers Can just download the code from Github, you don't need to learn using git yet, its just used to manage the version of your code, if you mess up you can just delete the folder and download again
- Or you can learn how to use git its fairly simple and saves time by saving checkpoints of your code. 
- Talk to chatgpt / claude / google
- If you really want to understand how to build AI tools / automations / agents - this is your starting point


A comprehensive, hands-on tutorial course for learning to work with Claude's API (Anthropic) from beginner to advanced levels. This repository contains practical examples and progressive lessons to help developers understand and implement AI-powered applications.

##  Course Overview

This course is structured in five progressive levels:
- **Fundamentals Level 1**: Basic API interactions and response handling (Session 1) 
- **Fundamentals Level 2**: Example business solutions  (Session 1)
- **Fundamentals Level 3**: Chat applications with context management (Session 2)
- **Fundamentals Level 4**: Advanced agent implementations (Blog automation, Presentation Builder) (Session 2)
- **Fundamentals Level 5**: Complex AI workflows (Lead scoring, Product management, Blog automation) (Session 3)

##  Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- An Anthropic API key ([Get one here](https://console.anthropic.com/))
- Git (for cloning the repository) - can be avoided, if you download the file as zip and open in your IDE

#### Windows-Specific Prerequisites
- Install Python from [python.org](https://www.python.org/downloads/) - **Important: Check "Add Python to PATH" during installation**
- Install Git from [git-scm.com](https://git-scm.com/download/win)
- Use Command Prompt, PowerShell, or Windows Terminal

### Installation

1. **Clone the repository**:

**Windows (Command Prompt or PowerShell):**
```bash
git clone https://github.com/TeacherOp/growthx_1
cd Learnai
```

**macOS/Linux:**
```bash
git clone https://github.com/TeacherOp/growthx_1
cd Learnai
```

2. **Create and activate a virtual environment**:

**Windows (Command Prompt):**
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate
```

**Windows (PowerShell):**
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Note: You may need to enable script execution first:
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
venv\Scripts\Activate.ps1
```

**macOS/Linux:**
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate
```

3. **Install dependencies**:

**All Platforms:**
```bash
pip install -r requirements.txt
# Or manually:
pip install anthropic python-dotenv
```

4. **Set up your API key**:

Create a `.env` file in the root directory:
```bash
ANTHROPIC_API_KEY=your_actual_api_key_here
```

Replace `your_actual_api_key_here` with your actual Anthropic API key.

### Verifying Your Setup

**Windows - Test your installation:**
```bash
# Check Python version
python --version

# Check pip
python -m pip --version

# Check if virtual environment is activated
where python
# Should show path to venv\Scripts\python.exe

# Test the API key setup
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('API Key configured!' if os.getenv('ANTHROPIC_API_KEY') else 'API Key not found!')"
```

**macOS/Linux - Test your installation:**
```bash
# Check Python version
python3 --version

# Check pip
pip3 --version

# Check if virtual environment is activated
which python3
# Should show path to venv/bin/python3

# Test the API key setup
python3 -c "from dotenv import load_dotenv; import os; load_dotenv(); print('API Key configured!' if os.getenv('ANTHROPIC_API_KEY') else 'API Key not found!')"
```

## 📖 Course Structure

### Level 1: Fundamentals
Learn the basics of working with Claude's API.

#### Step 1: Basic API Call

**Windows:**
```bash
cd Fundamentals_level_1
python -m step_1
```

**macOS/Linux:**
```bash
cd Fundamentals_level_1
python3 -m step_1
```
- **File**: `Fundamentals_level_1/step_1.py`
- **Learns**: Making your first API call, understanding response structure
- **Features**: Prints raw response, extracted content, and saves to text file

#### Step 2: Adding Parameters

**Windows:**
```bash
python -m step_2
```

**macOS/Linux:**
```bash
python3 -m step_2
```
- **File**: `Fundamentals_level_1/step_2.py`
- **Learns**: System prompts, temperature control, response customization
- **Features**: Demonstrates parameter effects on AI behavior

#### Step 3: Response Formatting

**Windows:**
```bash
python -m step_3
```

**macOS/Linux:**
```bash
python3 -m step_3
```
- **File**: `Fundamentals_level_1/step_3.py`
- **Learns**: Getting responses in specific formats (JSON, XML, etc.)
- **Features**: Shows how to request structured output

#### Step 4: Structured Output with Tools

**Windows:**
```bash
python -m step_4
```

**macOS/Linux:**
```bash
python3 -m step_4
```
- **File**: `Fundamentals_level_1/step_4.py`
- **Learns**: Using tool use for guaranteed structured JSON output
- **Features**: Demonstrates the proper way to get structured data from Claude

### Level 2: Solve Real World Business Problem
Solving one real world business problem

#### Step 5: Skill Assessment Agent

**Windows:**
```bash
cd ..\Fundamentals_level_2
python -m step_5
```

**macOS/Linux:**
```bash
cd ../Fundamentals_level_2
python3 -m step_5
```
- **File**: `step_5.py`
- **Input**: `step_5_input_data/inputdatesmall.csv`
- **Output**: `step_5_output_data/step_5_output_data_{timestamp}.csv`
- **Learns**: Building an AI agent for business analysis
- **Use Case**: Analyzing skills for technical assessment feasibility

#### Step 6: Enhanced too luse with Web Search

**Windows:**
```bash
python -m step_6
```

**macOS/Linux:**
```bash
python3 -m step_6
```
- **File**: `step_6.py`
- **Input**: `step_6_input_data/inputdatesmall.csv`
- **Output**: `step_6_output_data/step_6_output_data_with_citations_{timestamp}.csv`
- **Learns**: Integrating web search for research-backed analysis
- **Features**: Adds citations from web sources, research-based decisions

### Level 3: Bulding A chat that maintains Context ( Session 2 )
Build interactive chat script with context management.

#### Basic Chat with Context

**Windows:**
```bash
cd ..\Fundamentals_level_3
python -m chat
```

**macOS/Linux:**
```bash
cd ../Fundamentals_level_3
python3 -m chat
```
- **File**: `chat.py`
- **Learns**: Maintaining conversation context
- **Features**:
  - Real-time chat in terminal
  - Context preservation across messages
  - Clear command to reset conversation

#### Persistent Chat with Save/Resume ( Session 2 )

**Windows:**
```bash
python -m chat_2
```

**macOS/Linux:**
```bash
python3 -m chat_2
```
- **File**: `chat_2.py`
- **Learns**: Advanced conversation management
- **Features**:
  - Save conversations to JSON files
  - Resume previous conversations
  - Unique conversation IDs
  - Auto-save after each exchange
  - Conversation history browsing

## 💡 Key Concepts Covered

### API Fundamentals
- Making API calls
- Handling responses
- Error management
- Rate limiting considerations

### Advanced Features
- System prompts for personality/behavior
- Temperature control for creativity
- Token management
- Structured output with tools
- Web search integration

### Conversation Management
- Message role management (user/assistant)
- Context preservation
- Conversation persistence
- State management

### Best Practices
- Environment variable management
- Error handling
- Data persistence
- JSON file operations
- CSV data processing

## Learning Path

### Recommended Progression

1. **Start with Fundamentals** (Week 1)
   - Complete steps 1-5 in order
   - Experiment with different prompts
   - Understand response structures

2. **Move to Business Applications** (Week 2)
   - Run step_5 with sample data
   - Understand tool-based responses
   - Explore step_7's web search integration

3. **Master Chat Applications** (Week 3)
   - Build basic chat understanding with `chat.py`
   - Implement persistence with `chat_2.py`
   - Create your own chat variations

4. **Master Simple tools and workflows** ( Week 4)
   - Use the simple blog script, modify for your own use case, or just save output locally dont publish anywhere
   - Use the blog app, see the difference between a script vs app, use cases where a UI is needef for user input
   - Use Presentation builder app, understand how simple apps work, modify configure, your own tools and executions


## Session 2 - Chat Applications and Advanced Agent Implementations ✅

### What We Covered in Session 2

We successfully completed teaching **Level 3** and **Level 4** fundamentals, moving from basic chat applications to advanced multi-agent systems.

#### Session 2 Goal
- Click on the image link
![Session 2 Plan](<Notes_session_2/sesion_2_plan.jpeg>)

### Topics Covered:

#### 📝 **Level 3 - Chat Applications with Context Management**
- Building interactive chat applications that maintain conversation context
- Message sequencing and role management (user/assistant/tool messages)
- Implementing conversation persistence with save/resume functionality
- Tool integration for real-time data access (weather API example)
- Understanding the critical user→assistant→user message flow

#### 🚀 **Level 4 - Advanced Agent Implementations**
- **Simple Blog Automation Agent**:
  - Automated SEO-optimized blog generation
  - Web research integration with citations
  - Image generation and uploading
  - Publishing to live websites
  - Flask web UI with Server-Sent Events (SSE)

- **Simple Presentation Builder**:
  - Multi-agent architecture (main chat agent + PPT agent)
  - Web research for data gathering
  - HTML to PowerPoint conversion
  - Brand guideline integration
  - Screenshot capture and stitching

### Key Technical Concepts Learned:
1. **Tool Use Evolution**: From single API calls to complex tool chains
2. **Agent Architecture**: Collection of tools + execution sequence = Agent
3. **Context Management**: Maintaining conversation history across API calls
4. **Multi-Agent Systems**: Agents calling sub-agents for specialized tasks
5. **Production Considerations**: UI development, SSE for real-time updates, error handling

### Session 2 Resources:
- **Meeting Notes**: https://docs.google.com/document/d/11MJJAiMngitY8xa-XQByBPdLlZRcOwRKZ0npubJTqbI/edit?usp=sharing
- **Session Recording**: https://drive.google.com/file/d/1zlsIMINlm-yqfnsNwunaIspO_fRl5K-7/view?usp=sharing
- **Detailed Transcript**: Available in `Notes_session_2/session_2.md`
- **Feedback Link**: https://growthx.club/events/690d38c2c2df6fe0a0e32c64?feedback=true

### Practice Files:
After watching the session, practice with these implementations:
- `Fundamentals_level_3/chat_3.py` - Chat with weather tool integration
- `Fundamentals_level_4/simple_blog_automation/` - Full blog automation system with UI
- `Fundamentals_level_4/simple_presentation_builder/` - Multi-agent presentation builder

### Important Takeaways:
- One API call is the foundation for solving 90% of problems
- Tools can be as simple as a function or as complex as another AI agent
- Understanding the basics allows you to work with any platform (no-code or code)
- Focus on learning the fundamentals rather than specific platforms


## =� Troubleshooting

### Common Issues

1. **API Key Not Found**
   - Ensure `.env` file exists in root directory
   - Check API key format (no quotes needed in .env)
   - Verify key is active in Anthropic console

2. **Module Not Found**
   - Ensure you're in the correct directory
   - Windows: Use `python -m filename` (without .py extension)
   - macOS/Linux: Use `python3 -m filename` (without .py extension)
   - Check virtual environment is activated

3. **Windows-Specific Issues**
   - **Python not recognized**: Add Python to PATH during installation
   - **PowerShell script execution disabled**: Run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
   - **pip not found**: Use `python -m pip` instead of just `pip`
   - **Line ending issues**: Configure git with `git config --global core.autocrlf true`

4. **Rate Limiting**
   - Add delays between API calls if processing many items
   - Check your API tier limits


## > Contributing

Feel free to:
- Report issues
- Suggest improvements
- Add new examples
- Improve documentation

## =� License

This educational repository is for learning purposes. Please ensure you comply with Anthropic's usage policies when using the API.

## <� Next Steps

After completing this course, you can:
1. Build your own AI-powered applications
2. Integrate Claude into existing projects
3. Create sophisticated agents for business automation
4. Develop advanced chat interfaces

## =� Support

For questions or issues:
- Check the troubleshooting section
- Review the code comments
- Consult Anthropic's documentation
- Open an issue in this repository

---

**Happy Learning!** 🚀

Remember: The best way to learn is by doing. Start with step_1 and work your way through each example, experimenting and modifying the code as you go.

## 📚 Additional Resources

- [Anthropic Documentation](https://docs.anthropic.com/)
- [Claude Model Information](https://docs.anthropic.com/claude/docs/models-overview)
- [API Reference](https://docs.anthropic.com/claude/reference/messages-api)
- [Tool Use Guide](https://docs.anthropic.com/claude/docs/tool-use)
