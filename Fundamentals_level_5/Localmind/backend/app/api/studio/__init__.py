"""
Studio Blueprint - Content generation features from sources.

Educational Note: Studio features generate various content types from source
materials using AI. Each feature follows the same async pattern:

Background Job Pattern:
1. POST creates job record with status="pending"
2. Submits task to ThreadPoolExecutor via task_service
3. Returns job_id immediately (202 Accepted)
4. Frontend polls GET /jobs/{job_id} for status
5. When status="ready", content URL is available

This pattern is essential for long-running AI operations:
- Audio generation can take 30+ seconds (TTS processing)
- Image generation with Gemini takes 10-20 seconds
- Website/component generation involves multiple AI calls
- User gets immediate feedback, not blocked UI

Content Types Generated:
- Audio Overview: TTS audio summaries (ElevenLabs)
- Ad Creative: Marketing images (Gemini Imagen)
- Flash Cards: Q&A pairs for learning (Claude)
- Mind Map: Hierarchical concept visualization (Claude)
- Quiz: Multiple choice questions (Claude)
- Social Posts: Platform-specific posts with images (Claude + Gemini)
- Infographic: Visual summaries (Gemini Imagen)
- Email Template: HTML emails with images (Claude + Gemini)
- Website: Multi-page HTML/CSS/JS sites (Claude)
- Component: Reusable UI components (Claude)
- Video: AI-generated video clips (Google Veo)
- Flow Diagram: Mermaid diagrams for processes/relationships (Claude)
- Wireframe: UI/UX wireframes with Excalidraw (Claude)

Routes:
- POST /projects/<id>/studio/<type>           - Start generation
- GET  /projects/<id>/studio/<type>-jobs      - List jobs
- GET  /projects/<id>/studio/<type>-jobs/<id> - Job status
- GET  /projects/<id>/studio/<type>/<file>    - Serve generated files
"""
from flask import Blueprint

# Create the studio blueprint
studio_bp = Blueprint('studio', __name__)

# Import route modules to register them with the blueprint
from app.api.studio import audio  # noqa: F401
from app.api.studio import ads  # noqa: F401
from app.api.studio import flash_cards  # noqa: F401
from app.api.studio import mind_maps  # noqa: F401
from app.api.studio import quizzes  # noqa: F401
from app.api.studio import social_posts  # noqa: F401
from app.api.studio import infographics  # noqa: F401
from app.api.studio import emails  # noqa: F401
from app.api.studio import websites  # noqa: F401
from app.api.studio import components  # noqa: F401
from app.api.studio import videos  # noqa: F401
from app.api.studio import flow_diagrams  # noqa: F401
from app.api.studio import wireframes  # noqa: F401

# Educational Note: The noqa comments tell flake8 to ignore the
# "imported but unused" warning. We import to register routes,
# not to use the module directly.
