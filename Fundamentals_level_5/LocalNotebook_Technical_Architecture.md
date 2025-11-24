# LocalNotebook Technical Architecture Document

## Project Overview
A local-first Mac application combining document research (NotebookLM), voice dictation (Wispr Flow), and meeting intelligence (Granola) into a single educational tool.

---

## Technology Stack

### Frontend
- **Framework**: React 18+ with TypeScript
- **UI Components**: shadcn/ui (Radix UI primitives)
- **Styling**: Tailwind CSS 3.x
- **Icons**: Lucide React (open source, consistent design)
- **Build Tool**: Vite 5.x (fast HMR, optimized builds)
- **State Management**: Zustand (simple, lightweight)
- **HTTP Client**: Axios with interceptors
- **Real-time**: Socket.io-client for live features

### Backend
- **Framework**: Python Flask 3.x
- **Real-time**: Flask-SocketIO
- **CORS**: Flask-CORS
- **File Handling**: Python built-in + PyPDF2
- **Audio Processing**: PyAudio + wave
- **AI Integration**:
  - Anthropic SDK (Claude API)
  - OpenAI SDK (Whisper API)
  - Pinecone client (Vector DB)
- **Task Queue**: Celery with Redis (for background jobs)

### Storage
- **Database**: JSON files with defined schemas
- **File Storage**: Local filesystem with organized structure
- **Vector Store**: Pinecone (for document embeddings)
- **Cache**: Redis (for session data, temp storage)

### Desktop Integration
- **Electron**: For Mac desktop app wrapper
- **Native Modules**:
  - node-global-key-listener (hotkeys)
  - robotjs (keyboard automation)
  - BlackHole audio driver (system audio)

---

## Project Structure

```
LocalNotebook/
├── frontend/                    # React application
│   ├── src/
│   │   ├── components/         # Reusable UI components
│   │   │   ├── common/        # Shared components
│   │   │   │   ├── Button.tsx
│   │   │   │   ├── Input.tsx
│   │   │   │   └── Modal.tsx
│   │   │   ├── document/      # Document-related components
│   │   │   │   ├── DocumentUploader.tsx
│   │   │   │   ├── DocumentViewer.tsx
│   │   │   │   └── DocumentList.tsx
│   │   │   ├── voice/         # Voice dictation components
│   │   │   │   ├── VoiceRecorder.tsx
│   │   │   │   ├── TranscriptDisplay.tsx
│   │   │   │   └── HotkeySettings.tsx
│   │   │   └── meeting/       # Meeting components
│   │   │       ├── MeetingRecorder.tsx
│   │   │       ├── SpeakerLabeler.tsx
│   │   │       └── MeetingNotes.tsx
│   │   ├── hooks/             # Custom React hooks
│   │   │   ├── useDocuments.ts
│   │   │   ├── useVoiceRecording.ts
│   │   │   ├── useMeeting.ts
│   │   │   └── useWebSocket.ts
│   │   ├── lib/               # Utility libraries
│   │   │   ├── api.ts         # API client setup
│   │   │   ├── constants.ts   # App constants
│   │   │   ├── utils.ts       # Helper functions
│   │   │   └── types.ts       # TypeScript definitions
│   │   ├── pages/             # Main app pages
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Documents.tsx
│   │   │   ├── Voice.tsx
│   │   │   ├── Meetings.tsx
│   │   │   └── Settings.tsx
│   │   ├── store/             # State management
│   │   │   ├── documentStore.ts
│   │   │   ├── voiceStore.ts
│   │   │   └── meetingStore.ts
│   │   ├── styles/            # Global styles
│   │   │   └── globals.css
│   │   ├── App.tsx            # Main app component
│   │   └── main.tsx           # Entry point
│   ├── public/                # Static assets
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   ├── vite.config.ts
│   └── README.md              # Frontend documentation
│
├── backend/                    # Flask application
│   ├── app/
│   │   ├── __init__.py        # Flask app initialization
│   │   ├── config.py          # Configuration management
│   │   ├── api/               # API routes
│   │   │   ├── __init__.py
│   │   │   ├── documents.py   # Document endpoints
│   │   │   ├── voice.py       # Voice endpoints
│   │   │   ├── meetings.py    # Meeting endpoints
│   │   │   └── chat.py        # Chat/AI endpoints
│   │   ├── services/          # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── document_service.py
│   │   │   ├── voice_service.py
│   │   │   ├── meeting_service.py
│   │   │   ├── ai_service.py
│   │   │   └── storage_service.py
│   │   ├── models/            # Data models
│   │   │   ├── __init__.py
│   │   │   ├── document.py
│   │   │   ├── meeting.py
│   │   │   ├── project.py
│   │   │   └── schemas.py     # JSON schemas
│   │   ├── utils/             # Utility functions
│   │   │   ├── __init__.py
│   │   │   ├── audio_utils.py
│   │   │   ├── pdf_utils.py
│   │   │   ├── text_utils.py
│   │   │   └── validators.py
│   │   └── websocket/         # WebSocket handlers
│   │       ├── __init__.py
│   │       └── events.py
│   ├── data/                  # Local data storage
│   │   ├── projects/          # User projects
│   │   ├── documents/         # Uploaded documents
│   │   ├── meetings/          # Meeting recordings
│   │   └── temp/             # Temporary files
│   ├── prompts/              # AI prompt templates
│   │   ├── chat_system.md
│   │   ├── summary.md
│   │   ├── meeting_notes.md
│   │   └── README.md         # Prompt documentation
│   ├── tests/                # Test files
│   │   ├── unit/
│   │   ├── integration/
│   │   └── fixtures/
│   ├── requirements.txt      # Python dependencies
│   ├── run.py               # Application entry point
│   └── README.md            # Backend documentation
│
├── electron/                 # Desktop app wrapper
│   ├── main.js              # Main process
│   ├── preload.js           # Preload script
│   ├── package.json
│   └── README.md
│
├── docs/                    # Documentation
│   ├── API.md              # API documentation
│   ├── SETUP.md            # Setup instructions
│   ├── ARCHITECTURE.md     # This document
│   └── LEARNING_NOTES.md   # Educational notes
│
├── scripts/                 # Utility scripts
│   ├── setup.sh            # Initial setup script
│   ├── install_blackhole.sh # Audio driver setup
│   └── build.sh            # Build script
│
├── .env.template           # Environment variables template
├── .gitignore
├── README.md              # Main project documentation
└── LICENSE

```

---

## Core Design Principles

### 1. DRY (Don't Repeat Yourself)
```python
# backend/app/utils/decorators.py
"""
Educational Note: We create reusable decorators to avoid
repeating validation logic across endpoints
"""
def validate_api_key(f):
    """
    Decorator to validate API key presence before executing endpoint.
    This follows DRY principle - write validation once, use everywhere.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key or not validate_key(api_key):
            return jsonify({'error': 'Invalid API key'}), 401
        return f(*args, **kwargs)
    return decorated_function

# Usage in multiple endpoints:
@app.route('/api/documents', methods=['POST'])
@validate_api_key  # Reusing the validation logic
def upload_document():
    pass
```

### 2. Configuration Management
```python
# backend/app/config.py
"""
Educational Note: All configuration in one place, no hardcoding.
Use environment variables for sensitive data.
"""
import os
from typing import Dict, Any

class Config:
    """Base configuration class with common settings"""

    # Application settings
    APP_NAME = "LocalNotebook"
    VERSION = "1.0.0"

    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

    # File paths - using os.path for cross-platform compatibility
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    UPLOAD_DIR = os.path.join(DATA_DIR, 'documents')

    # API Keys - loaded from environment, never hardcoded
    ANTHROPIC_KEY = os.getenv('ANTHROPIC_API_KEY')
    OPENAI_KEY = os.getenv('OPENAI_API_KEY')
    PINECONE_KEY = os.getenv('PINECONE_API_KEY')

    # File upload settings
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB max file size
    ALLOWED_EXTENSIONS = {'pdf', 'txt', 'md', 'docx', 'json'}

    @classmethod
    def validate_config(cls) -> Dict[str, Any]:
        """
        Validate required configuration values.
        Educational: Always validate config at startup to catch issues early.
        """
        errors = []
        if not cls.ANTHROPIC_KEY:
            errors.append("ANTHROPIC_API_KEY is required")
        if not os.path.exists(cls.DATA_DIR):
            os.makedirs(cls.DATA_DIR, exist_ok=True)
        return {"valid": len(errors) == 0, "errors": errors}
```

### 3. Service Layer Pattern
```python
# backend/app/services/document_service.py
"""
Educational Note: Business logic separated from API routes.
This makes code testable and reusable.
"""
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class DocumentService:
    """
    Service class for document operations.
    Separates business logic from Flask routes.
    """

    def __init__(self, storage_service, ai_service):
        """
        Dependency injection - services are passed in, not created here.
        This makes testing easier and follows SOLID principles.
        """
        self.storage = storage_service
        self.ai = ai_service

    def process_document(self, file_path: str, project_id: str) -> Dict:
        """
        Process uploaded document through multiple steps.

        Learning Note: Breaking complex operations into steps
        makes code easier to understand and debug.
        """
        try:
            # Step 1: Extract text from document
            logger.info(f"Extracting text from {file_path}")
            text = self._extract_text(file_path)

            # Step 2: Chunk text for processing
            logger.info("Chunking document text")
            chunks = self._chunk_text(text)

            # Step 3: Generate embeddings
            logger.info("Generating embeddings")
            embeddings = self.ai.generate_embeddings(chunks)

            # Step 4: Store in vector database
            logger.info("Storing in vector database")
            doc_id = self.storage.store_document(
                project_id=project_id,
                chunks=chunks,
                embeddings=embeddings
            )

            return {
                "success": True,
                "document_id": doc_id,
                "chunks_created": len(chunks)
            }

        except Exception as e:
            logger.error(f"Document processing failed: {str(e)}")
            return {"success": False, "error": str(e)}

    def _extract_text(self, file_path: str) -> str:
        """Extract text based on file type"""
        # Implementation here
        pass

    def _chunk_text(self, text: str, chunk_size: int = 1000) -> List[str]:
        """
        Split text into manageable chunks for processing.

        Educational: LLMs have token limits, so we chunk documents
        to process them piece by piece.
        """
        # Implementation here
        pass
```

### 4. Frontend Component Structure
```typescript
// frontend/src/components/document/DocumentUploader.tsx
/**
 * DocumentUploader Component
 *
 * Educational Note: This component follows React best practices:
 * - Single responsibility (only handles document upload)
 * - Proper TypeScript typing for props
 * - Error handling with user feedback
 * - Accessible (ARIA labels, keyboard support)
 */

import React, { useState, useCallback } from 'react';
import { Upload, FileText, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useToast } from '@/components/ui/use-toast';
import { uploadDocument } from '@/lib/api';

interface DocumentUploaderProps {
  projectId: string;
  onUploadComplete: (documentId: string) => void;
  maxFileSize?: number; // in MB
  allowedTypes?: string[];
}

export const DocumentUploader: React.FC<DocumentUploaderProps> = ({
  projectId,
  onUploadComplete,
  maxFileSize = 100,
  allowedTypes = ['pdf', 'txt', 'md', 'docx']
}) => {
  const [isUploading, setIsUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const { toast } = useToast();

  /**
   * Handle file drop
   * Educational: useCallback prevents function recreation on each render
   */
  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const files = Array.from(e.dataTransfer.files);
    await processFiles(files);
  }, [projectId]);

  /**
   * Process uploaded files
   * Educational: Extract logic to separate function for reusability
   */
  const processFiles = async (files: File[]) => {
    // Validation
    const validFiles = files.filter(file => {
      const extension = file.name.split('.').pop()?.toLowerCase();
      const isValidType = allowedTypes.includes(extension || '');
      const isValidSize = file.size <= maxFileSize * 1024 * 1024;

      if (!isValidType) {
        toast({
          title: 'Invalid file type',
          description: `${file.name} is not a supported file type`,
          variant: 'destructive'
        });
        return false;
      }

      if (!isValidSize) {
        toast({
          title: 'File too large',
          description: `${file.name} exceeds ${maxFileSize}MB limit`,
          variant: 'destructive'
        });
        return false;
      }

      return true;
    });

    // Upload valid files
    for (const file of validFiles) {
      await uploadFile(file);
    }
  };

  const uploadFile = async (file: File) => {
    setIsUploading(true);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('projectId', projectId);

      const response = await uploadDocument(formData);

      toast({
        title: 'Upload successful',
        description: `${file.name} has been uploaded`
      });

      onUploadComplete(response.documentId);
    } catch (error) {
      // Educational: Always provide meaningful error messages
      toast({
        title: 'Upload failed',
        description: error instanceof Error ? error.message : 'Unknown error',
        variant: 'destructive'
      });
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div
      className={`
        relative border-2 border-dashed rounded-lg p-8
        transition-colors duration-200 ease-in-out
        ${dragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300'}
        ${isUploading ? 'opacity-50 pointer-events-none' : ''}
      `}
      onDragEnter={(e) => { e.preventDefault(); setDragActive(true); }}
      onDragLeave={(e) => { e.preventDefault(); setDragActive(false); }}
      onDragOver={(e) => e.preventDefault()}
      onDrop={handleDrop}
    >
      <div className="flex flex-col items-center justify-center space-y-4">
        <Upload className="w-12 h-12 text-gray-400" />
        <div className="text-center">
          <p className="text-lg font-medium">
            Drop files here or click to upload
          </p>
          <p className="text-sm text-gray-500 mt-1">
            Supports {allowedTypes.join(', ')} up to {maxFileSize}MB
          </p>
        </div>
        <Button
          onClick={() => document.getElementById('file-input')?.click()}
          disabled={isUploading}
        >
          Select Files
        </Button>
        <input
          id="file-input"
          type="file"
          className="hidden"
          multiple
          accept={allowedTypes.map(t => `.${t}`).join(',')}
          onChange={(e) => {
            const files = Array.from(e.target.files || []);
            processFiles(files);
          }}
        />
      </div>
    </div>
  );
};
```

### 5. API Route Structure
```python
# backend/app/api/documents.py
"""
Document API endpoints.

Educational Note: RESTful API design with clear HTTP methods:
- GET: Retrieve resources
- POST: Create new resources
- PUT: Update existing resources
- DELETE: Remove resources
"""
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import os
import logging

from app.services import document_service, storage_service
from app.utils.validators import validate_file_type, validate_project_id
from app.utils.decorators import validate_api_key, handle_errors

logger = logging.getLogger(__name__)

# Create blueprint for modular route organization
documents_bp = Blueprint('documents', __name__, url_prefix='/api/documents')

@documents_bp.route('/', methods=['GET'])
@validate_api_key
@handle_errors
def list_documents():
    """
    List all documents for a project.

    Query Parameters:
        project_id: ID of the project
        page: Page number (default: 1)
        per_page: Items per page (default: 20)

    Returns:
        JSON list of documents with metadata

    Educational: Pagination prevents memory issues with large datasets
    """
    project_id = request.args.get('project_id')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))

    # Validate inputs
    if not validate_project_id(project_id):
        return jsonify({'error': 'Invalid project ID'}), 400

    # Get documents with pagination
    documents = document_service.get_documents(
        project_id=project_id,
        page=page,
        per_page=per_page
    )

    return jsonify({
        'documents': documents,
        'page': page,
        'per_page': per_page,
        'total': len(documents)
    })

@documents_bp.route('/', methods=['POST'])
@validate_api_key
@handle_errors
def upload_document():
    """
    Upload a new document.

    Educational: File upload handling with security considerations:
    - Validate file type to prevent malicious uploads
    - Use secure_filename to prevent path traversal attacks
    - Store files outside web root for security
    """
    # Check if file present
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    project_id = request.form.get('project_id')

    # Validate inputs
    if not file.filename:
        return jsonify({'error': 'No file selected'}), 400

    if not validate_project_id(project_id):
        return jsonify({'error': 'Invalid project ID'}), 400

    if not validate_file_type(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400

    # Secure the filename
    filename = secure_filename(file.filename)

    # Create unique filename to prevent overwrites
    import uuid
    unique_filename = f"{uuid.uuid4()}_{filename}"

    # Save file
    file_path = os.path.join(
        current_app.config['UPLOAD_DIR'],
        project_id,
        unique_filename
    )

    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    file.save(file_path)

    # Process document asynchronously
    # Educational: Long operations should be queued to prevent timeout
    from app.tasks import process_document_task
    task = process_document_task.delay(file_path, project_id)

    return jsonify({
        'message': 'Document uploaded successfully',
        'task_id': task.id,
        'filename': filename
    }), 202  # 202 Accepted for async operations

@documents_bp.route('/<document_id>', methods=['DELETE'])
@validate_api_key
@handle_errors
def delete_document(document_id: str):
    """
    Delete a document.

    Educational: Soft delete vs hard delete:
    - Soft delete: Mark as deleted but keep data (recoverable)
    - Hard delete: Permanently remove (not recoverable)
    We use soft delete for safety.
    """
    success = document_service.soft_delete_document(document_id)

    if success:
        return jsonify({'message': 'Document deleted successfully'})
    else:
        return jsonify({'error': 'Document not found'}), 404
```

### 6. Error Handling
```python
# backend/app/utils/decorators.py
"""
Educational Note: Centralized error handling prevents code duplication
and ensures consistent error responses across the API.
"""
import functools
import logging
from flask import jsonify

logger = logging.getLogger(__name__)

def handle_errors(f):
    """
    Decorator to handle exceptions in API endpoints.

    Learning Point: This decorator catches all exceptions and returns
    appropriate HTTP responses, preventing the app from crashing and
    exposing internal errors to users.
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            # Client error - bad input
            logger.warning(f"ValueError in {f.__name__}: {str(e)}")
            return jsonify({'error': str(e)}), 400
        except PermissionError as e:
            # Authorization error
            logger.warning(f"PermissionError in {f.__name__}: {str(e)}")
            return jsonify({'error': 'Permission denied'}), 403
        except FileNotFoundError as e:
            # Resource not found
            logger.warning(f"FileNotFoundError in {f.__name__}: {str(e)}")
            return jsonify({'error': 'Resource not found'}), 404
        except Exception as e:
            # Unexpected error - log full details but return generic message
            logger.error(f"Unexpected error in {f.__name__}: {str(e)}", exc_info=True)
            return jsonify({'error': 'Internal server error'}), 500

    return decorated_function
```

---

## Development Workflow

### 1. Environment Setup
```bash
# Clone repository
git clone https://github.com/username/LocalNotebook.git
cd LocalNotebook

# Backend setup
cd backend
python3 -m venv venv
source venv/bin/activate  # On Mac/Linux
pip install -r requirements.txt
cp .env.template .env
# Edit .env with your API keys

# Frontend setup (new terminal)
cd frontend
npm install
cp .env.template .env.local
# Edit .env.local with backend URL

# Start development servers
# Backend terminal
python run.py

# Frontend terminal
npm run dev
```

### 2. Code Standards

#### Python (Backend)
- **Style Guide**: PEP 8
- **Type Hints**: Use for all functions
- **Docstrings**: Google style for all public functions
- **Testing**: Minimum 80% coverage
- **Linting**: Black + Flake8

#### TypeScript (Frontend)
- **Style Guide**: Airbnb React/TypeScript
- **Components**: Functional with hooks
- **State**: Zustand for global, useState for local
- **Testing**: Jest + React Testing Library
- **Linting**: ESLint + Prettier

### 3. Git Workflow
```bash
# Feature branch workflow
git checkout -b feature/document-upload
# Make changes
git add .
git commit -m "feat: add document upload functionality"
git push origin feature/document-upload
# Create pull request for review
```

---

## API Documentation Example

### Upload Document
```http
POST /api/documents
Content-Type: multipart/form-data
X-API-Key: your-api-key

{
  "file": (binary),
  "project_id": "proj_123",
  "metadata": {
    "title": "Meeting Notes",
    "tags": ["important", "q4-2024"]
  }
}

Response 202:
{
  "task_id": "task_456",
  "filename": "meeting_notes.pdf",
  "message": "Document queued for processing"
}

Response 400:
{
  "error": "Invalid file type"
}
```

---

## Learning Resources

### For Students
1. **Code Comments**: Every complex logic explained
2. **Educational Notes**: "Why" behind design decisions
3. **Examples**: Real-world use cases in comments
4. **Patterns**: Common patterns highlighted
5. **Anti-patterns**: What NOT to do and why

### Example Learning Comment
```python
# backend/app/services/ai_service.py
def chunk_text(text: str, max_tokens: int = 1000) -> List[str]:
    """
    Split text into chunks for LLM processing.

    Educational Context:
    ----------------------
    LLMs have token limits (e.g., Claude has 200k context).
    We need to chunk large documents to:
    1. Stay within limits
    2. Maintain coherent context
    3. Optimize cost (charged per token)

    This implementation uses a sliding window approach
    with overlap to maintain context between chunks.

    Real-world example:
    A 50-page PDF might be 25,000 tokens. We chunk it
    into 25 chunks of ~1,000 tokens each, with 100-token
    overlap to maintain context continuity.

    Args:
        text: The text to chunk
        max_tokens: Maximum tokens per chunk

    Returns:
        List of text chunks
    """
    # Implementation here
```

---

## Deployment Considerations

### Local-First Architecture
- No cloud dependencies for core features
- API keys stored locally
- All data on user's machine
- Offline capability for non-AI features

### Performance Optimization
- Lazy loading for large documents
- Background processing for heavy tasks
- Caching for frequently accessed data
- Efficient vector search with Pinecone

### Security
- API keys encrypted at rest
- Sanitize all user inputs
- Secure file handling
- No telemetry or tracking

---

## Testing Strategy

### Unit Tests
```python
# backend/tests/unit/test_document_service.py
"""
Educational: Unit tests test individual functions in isolation.
We mock external dependencies to test only our logic.
"""
import pytest
from unittest.mock import Mock, patch
from app.services.document_service import DocumentService

def test_chunk_text():
    """Test that text is properly chunked"""
    service = DocumentService(Mock(), Mock())

    text = "A" * 3000  # 3000 characters
    chunks = service._chunk_text(text, chunk_size=1000)

    assert len(chunks) == 3
    assert all(len(chunk) <= 1000 for chunk in chunks)
```

### Integration Tests
```python
# backend/tests/integration/test_api.py
"""
Educational: Integration tests test multiple components together.
They ensure different parts of the system work correctly together.
"""
def test_document_upload_flow(client, sample_pdf):
    """Test complete document upload and processing flow"""

    # Upload document
    response = client.post('/api/documents',
        data={'file': sample_pdf, 'project_id': 'test_project'},
        headers={'X-API-Key': 'test-key'}
    )

    assert response.status_code == 202
    assert 'task_id' in response.json

    # Check document appears in list
    response = client.get('/api/documents?project_id=test_project')
    assert len(response.json['documents']) == 1
```

---

## Monitoring & Logging

### Structured Logging
```python
# backend/app/__init__.py
import logging
import logging.config

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        }
    },
    'handlers': {
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/app.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'default'
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default'
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['file', 'console']
    }
}

logging.config.dictConfig(LOGGING_CONFIG)
```

---

## Next Steps

1. **Phase 1**: Core infrastructure setup
2. **Phase 2**: Basic features implementation
3. **Phase 3**: AI integration
4. **Phase 4**: Desktop app packaging
5. **Phase 5**: Testing & documentation
6. **Phase 6**: Beta release

---

## Educational Philosophy

This project is designed to teach:
1. **Modern web development** with React + Flask
2. **AI integration** patterns
3. **Desktop app development** with Electron
4. **Best practices** in code organization
5. **Real-world problem solving**

Every piece of code includes learning notes to help students understand not just "what" but "why" we make certain decisions.