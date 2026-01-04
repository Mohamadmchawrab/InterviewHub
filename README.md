# InterviewHub — AI Interview Preparation Assistant

An AI-powered web application that transforms interview preparation into structured, actionable checklists with interactive AI practice sessions.

## Features

- **AI-Powered Checklist Generation**: Uses OpenAI GPT-3.5-turbo to create personalized, actionable checklists
- **Proactive AI Agent**: Asks for job descriptions and interview details to create tailored preparation plans
- **Interactive Checklist**: Check off items, track progress, and organize tasks by readiness dimensions
- **AI Interviewer**: Test your knowledge with interactive 4-question sessions that provide real-time feedback
- **Automatic Completion**: Checklist items are automatically marked as "done" when you pass the AI interview test
- **Next 3 Actions**: Quick-start actions for immediate focus
- **Session Management**: Create multiple interview preparation sessions, view history, and delete sessions

## Tech Stack

- **Frontend**: Next.js 14 (App Router), TypeScript, TailwindCSS, Framer Motion, shadcn/ui
- **Backend**: Python, FastAPI, SQLModel, Alembic
- **AI**: OpenAI API (GPT-3.5-turbo with fallback strategy)
- **Database**: PostgreSQL (via SQLModel)

## Project Structure

```

├── backend/
│   ├── main.py              # FastAPI application
│   ├── models.py             # Database and Pydantic models
│   ├── schemas.py            # API request/response schemas
│   ├── ai_service.py         # AI service wrapper
│   ├── requirements.txt      # Python dependencies
│   └── Dockerfile            # Backend Docker configuration
├── frontend/
│   ├── app/                  # Next.js app directory
│   │   ├── page.tsx          # Home page
│   │   └── session/[id]/     # Session page
│   ├── components/ui/        # shadcn/ui components
│   ├── lib/                  # Utilities and API client
│   └── Dockerfile            # Frontend Docker configuration
├── docker-compose.yml        # Docker Compose configuration
└── README.md                 # This file
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- OpenAI API key

### Setup & Run

1. **Create backend environment file**:
   ```bash
   cd backend
   cp .env.example .env  # or create .env manually
   ```

2. **Add your OpenAI API key** to `backend/.env`:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

3. **Start everything with one command**:
   ```bash
   docker-compose up
   ```

   Or to rebuild from scratch:
   ```bash
   docker-compose up --build
   ```

4. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

That's it! The application will automatically:
- Set up PostgreSQL database
- Run database migrations (Alembic)
- Start the FastAPI backend
- Build and start the Next.js frontend

### For Production/Server Deployment

If deploying to a server, set the `NEXT_PUBLIC_API_URL` environment variable before running docker-compose:

```bash
export NEXT_PUBLIC_API_URL=http://your-server-ip:8000
docker-compose up --build
```

Or create a `.env` file in the project root:
```
NEXT_PUBLIC_API_URL=http://your-server-ip:8000
```

The docker-compose.yml will automatically use this value. Also ensure backend CORS is configured in `backend/main.py` (it includes common server IPs by default, or set `CORS_ORIGINS` environment variable).

## Usage

1. **Start a New Chat**: Click "New Chat" in the sidebar
2. **Enter Your Goal**: Type something like "I have a frontend interview in 10 days"
3. **Share Details**: The AI will proactively ask for:
   - Job description (required for interviews)
   - Interview format (coding challenges, system design, etc.)
   - Timeline and other relevant details
4. **Get Your Checklist**: Receive a structured checklist organized by:
   - **Context Understanding**: Understanding the role and company
   - **Skills / Knowledge Prep**: Technical skills to practice (with "Test Knowledge" button)
   - **Evidence & Examples**: Past projects and achievements to prepare
   - **Delivery & Execution**: Mock interviews and communication practice
   - **Logistics & Risk**: Date confirmation, tech setup, backup plans
5. **Test Your Knowledge**: Click "Test Knowledge" on any Skills item to start an AI interview:
   - Answer 4 questions about the skill
   - Get real-time feedback after each answer
   - Receive a rating (0-10 scale)
   - Automatically marked as "done" if you score 7/10 or higher
6. **Track Progress**: See your completion percentage and "Next 3 Actions" for immediate focus

## API Endpoints

- `POST /api/sessions` - Create a new session
- `POST /api/sessions/{session_id}/message` - Send message and get AI response
- `GET /api/sessions/{session_id}` - Get session details
- `GET /api/sessions` - List all sessions
- `PATCH /api/sessions/{session_id}/todos/{todo_id}` - Update todo status/text
- `DELETE /api/sessions/{session_id}` - Delete a session
- `POST /api/sessions/{session_id}/interview/start` - Start AI interview for a skill
- `POST /api/sessions/{session_id}/interview/{todo_id}/answer` - Answer interview question
- `GET /api/health` - Health check

See `http://localhost:8000/docs` for interactive API documentation.

## Database

The application uses PostgreSQL for persistence. The database is automatically set up when you run `docker-compose up`:

- **Database**: PostgreSQL 15 (Alpine)
- **Auto-migration**: Alembic migrations run automatically on startup
- **Data persistence**: Data is stored in a Docker volume (`postgres-data`)
- **Connection**: Backend connects automatically via Docker networking

No manual database setup required!

## Environment Variables

### Backend (`backend/.env`)

- `OPENAI_API_KEY` (required): Your OpenAI API key
- `DATABASE_URL` (optional): Automatically set by docker-compose to connect to PostgreSQL container
- `CORS_ORIGINS` (optional): Comma-separated list of allowed origins (defaults include localhost and server IP)

### Frontend (via docker-compose.yml)

- `NEXT_PUBLIC_API_URL`: Backend API URL (set as build arg and runtime env var)
  - Default for local: `http://localhost:8000`
  - For server deployment: Update to your server IP/domain

## Development Notes

### AI Service

The AI service uses:
- **GPT-3.5-turbo** with intelligent fallback strategy:
  - Tries specific versions (`gpt-3.5-turbo-0125`, `gpt-3.5-turbo-1106`) first
  - Falls back to `gpt-3.5-turbo` if needed
  - Cost-effective for MVP while maintaining quality
  - Handles structured JSON output for checklists and interview questions

### Proactive AI Agent

The AI proactively asks for information before generating the checklist:
- **Job Description**: Required for interview preparation
- **Interview Format**: Coding challenges, system design, behavioral, etc.
- **Timeline**: When is the interview scheduled?
- **Company/Context**: Additional details to tailor the preparation plan

### Checklist Structure

Each checklist contains:
- **Title**: Short summary of the interview
- **Event Type**: Always "interview" (focused scope)
- **Assumptions**: Any assumptions made due to missing information
- **Groups**: Five readiness dimension groups with todos:
  - Context Understanding
  - Skills / Knowledge Prep (with "Test Knowledge" button)
  - Evidence & Examples
  - Delivery & Execution
  - Logistics & Risk
- **Next 3 Actions**: Quick-start actions for immediate progress
- **Progress Tracking**: "X of Y completed" with percentage

### AI Interviewer Feature

For "Skills / Knowledge Prep" items:
- Click "Test Knowledge" button on any skill item
- AI asks exactly 4 questions about the skill (no more, no less)
- Answer each question in the chat interface
- Receive immediate feedback after each answer
- Get a final rating (0-10 scale) based on your performance
- **Pass threshold**: 7/10 or higher
- **Auto-completion**: Checklist item is automatically marked as "done" if you pass
- **Question deduplication**: AI ensures no repeated questions
- **Smart evaluation**: Analyzes feedback to determine correct, partially correct, or incorrect answers

## Trade-offs & Limitations (MVP)

- **No Authentication**: Sessions are stored via ID (accessible for testing/demonstration)
- **No Calendar Sync**: Manual time management
- **No Reminders**: No automated notifications
- **Interview-Focused**: Specialized for interview preparation (not general goal planning)
- **Single Session Model**: One checklist per session (no multi-checklist support)
- **GPT-3.5-turbo**: Cost-effective choice; may require GPT-4 for more complex reasoning in future

## Future Enhancements (V2 Ideas)

- **Timeline View**: Visual calendar showing preparation schedule
- **Progress Analytics**: "You're 75% ready" with detailed insights
- **Smart Recommendations**: AI suggests focus areas based on progress
- **Export/Share**: Export to PDF, share with mentor
- **Multiple Interview Types**: Behavioral, system design, technical coding (each with tailored checklists)
- **Resource Recommendations**: Links to relevant articles, videos
- **Calendar Integration**: Sync with Google Calendar, reminders
- **User Authentication**: Save profiles, reuse content

## Troubleshooting

### Docker Issues

- **Port conflicts**: Change ports in `docker-compose.yml` if 3000 or 8000 are in use
- **Build failures**: 
  - Ensure Docker has sufficient resources allocated
  - Try `docker-compose down -v` to remove volumes and start fresh
  - Rebuild: `docker-compose up --build`
- **Container won't start**: Check logs with `docker-compose logs [service-name]`

### Backend Issues

- **OpenAI API errors**: 
  - Verify your API key is correct in `backend/.env`
  - Check if you have sufficient quota/credits
  - Error messages will indicate if it's a quota, model access, or key issue
- **Database connection errors**: 
  - Ensure PostgreSQL container is running: `docker-compose ps`
  - Check database logs: `docker-compose logs postgres`
- **Migration errors**: Check backend logs for Alembic migration issues

### Frontend Issues

- **API connection errors**: 
  - Verify backend is running: `docker-compose ps backend`
  - Check `NEXT_PUBLIC_API_URL` in `docker-compose.yml` matches your setup
  - For server deployment, ensure CORS is configured correctly
- **Build errors**: 
  - Rebuild frontend: `docker-compose build frontend`
  - Check build logs: `docker-compose logs frontend`

## License

This project is a case study implementation.