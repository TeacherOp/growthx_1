# LocalMind - Quick Start Guide

## Running the Application

### Backend (Flask)
```bash
cd backend

# Activate virtual environment
source myvenv/bin/activate  # On Mac/Linux
# or
myvenv\Scripts\activate  # On Windows

# Install dependencies (if not already done)
pip install -r requirements.txt

# Run the backend
python run.py
```
Backend will run on: http://localhost:5000

### Frontend (React)
Open a new terminal:
```bash
cd frontend

# Install dependencies (if not already done)
npm install

# Run the frontend
npm run dev
```
Frontend will run on: http://localhost:5173

## Features Available

✅ **Backend API Endpoints:**
- GET /api/v1/projects - List all projects
- POST /api/v1/projects - Create new project
- GET /api/v1/projects/{id} - Get project details
- PUT /api/v1/projects/{id} - Update project
- DELETE /api/v1/projects/{id} - Delete project
- POST /api/v1/projects/{id}/open - Mark as opened

✅ **Frontend Features:**
- View all projects in a grid layout
- Create new projects with name and description
- Delete projects
- Open project (placeholder workspace)
- Responsive design with Tailwind CSS
- shadcn/ui components

## Tech Stack

**Backend:**
- Python Flask
- Flask-CORS for cross-origin requests
- JSON file storage
- Modular architecture with services

**Frontend:**
- React with TypeScript
- Vite for fast development
- Tailwind CSS for styling
- shadcn/ui for components
- Axios for API calls
- Lucide React for icons

## Next Steps

- [ ] Add document upload functionality
- [ ] Implement chat interface
- [ ] Add voice dictation
- [ ] Create meeting recording features
- [ ] Build project workspace

## Educational Notes

This project includes extensive comments throughout the code to help learners understand:
- Flask application factory pattern
- React hooks and state management
- API integration patterns
- Component composition
- TypeScript typing
- Tailwind CSS utilities
- shadcn/ui component patterns