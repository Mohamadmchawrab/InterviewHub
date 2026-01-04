# InterviewHub — AI Interview Preparation Assistant

An AI-powered web application that transforms interview preparation into structured, actionable checklists with interactive AI practice sessions.

## Features

- **AI-Powered Checklist Generation**: Uses OpenAI to create personalized, actionable checklists
- **Event Type Support**: Interview, Presentation, Performance Review, Negotiation, and more
- **Interactive Checklist**: Check off items, edit todos, add custom items
- **Follow-up Questions**: AI asks targeted questions to improve checklist accuracy
- **Regeneration**: Regenerate checklists while preserving completed items
- **Next 3 Actions**: Quick-start actions to get you moving immediately

## Tech Stack

- **Frontend**: Next.js 14 (App Router), TypeScript, TailwindCSS, Framer Motion, shadcn/ui
- **Backend**: Python, FastAPI, SQLModel, Alembic
- **AI**: OpenAI API (GPT-3.5-turbo with fallback strategy)
- **Database**: PostgreSQL (via SQLModel)

## Project Structure

```
wolters-case-study/
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

## Setup Instructions

### Prerequisites

- Node.js 20.9.0 or higher
- Python 3.11 or higher
- OpenAI API key
- Docker and Docker Compose (optional, for containerized deployment)

### Local Development

#### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the backend directory:
   ```bash
   cp .env.example .env
   ```

5. Edit `.env` and add your OpenAI API key and PostgreSQL connection:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   DATABASE_URL=postgresql://readylist:readylist_password@localhost:5432/readylist
   ```

6. Start PostgreSQL using Docker all open now for testing you can generate private labels later but always be sure to now share passwords like this:
   ```bash
   docker run --name readylist-postgres \
     -e POSTGRES_USER=readylist \
     -e POSTGRES_PASSWORD=readylist_password \
     -e POSTGRES_DB=readylist \
     -p 5432:5432 \
     -d postgres:15-alpine
   ```

7. Initialize the database:
   ```bash
   python init_db.py
   ```

6. Run the backend server:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

The backend will be available at `http://localhost:8000`

#### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Create a `.env.local` file (optional, defaults to `http://localhost:8000`):
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

4. Run the development server:
   ```bash
   npm run dev
   ```

The frontend will be available at `http://localhost:3000`

### Docker Deployment

1. Create a `.env` file in the project root:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

2. Build and start containers:
   ```bash
   docker-compose up --build
   ```

3. Access the application:
   - Frontend: `http://localhost:3000`
   - Backend API: `http://localhost:8000`
   - API Docs: `http://localhost:8000/docs`

## Usage

1. **Start a Session**: Enter your event description (e.g., "I have a frontend interview in 10 days")
2. **Answer Follow-up**: The AI will ask targeted questions to improve checklist accuracy
3. **Review Checklist**: Get a structured checklist grouped by readiness dimensions:
   - Context Understanding
   - Skills / Knowledge Prep
   - Evidence & Examples
   - Delivery & Execution
   - Logistics & Risk
4. **Interact**: Check off items, edit todos, add custom items
5. **Regenerate**: Regenerate the checklist while preserving completed items

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

The application uses PostgreSQL for persistence. You can run PostgreSQL locally using Docker:

```bash
docker run --name readylist-postgres \
  -e POSTGRES_USER=readylist \
  -e POSTGRES_PASSWORD=readylist_password \
  -e POSTGRES_DB=readylist \
  -p 5432:5432 \
  -d postgres:15-alpine
```

Or use the docker-compose setup which includes PostgreSQL automatically.

The database tables are created automatically on first run, or you can initialize them manually:
```bash
cd backend
python init_db.py
```

## Environment Variables

### Backend

- `OPENAI_API_KEY` (required): Your OpenAI API key
- `DATABASE_URL` (optional): Database connection string (defaults to SQLite)

### Frontend

- `NEXT_PUBLIC_API_URL` (optional): Backend API URL (defaults to `http://localhost:8000`)

## Development Notes

### AI Service

The AI service uses:
- **GPT-4o-mini** for event type classification and title generation (fast, cost-effective)
- **GPT-4o** for checklist generation (high quality, structured JSON output)

### Follow-up Questions

The system always asks at least one follow-up question before generating the checklist:
- **Interview**: Job description (required), company, interview format
- **Presentation**: Audience, goal, duration
- **Performance Review**: Role expectations, review period, previous feedback
- **Negotiation**: Target outcome, constraints, context
- **Other**: Additional details

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
- Click "Test Knowledge" button
- AI asks exactly 4 questions about the skill
- Answer each question
- Receive feedback after each answer
- Get final rating (0-10 scale)
- Pass if 7/10 or higher
- Automatically marked as "done" if passed

## Trade-offs & Limitations (MVP)

- **No Authentication**: Sessions are stored via ID (accessible for testing)
- **No Calendar Sync**: Manual time management
- **No Reminders**: No automated notifications
- **Single Use Case**: Focused on interviews only (not presentations, negotiations, etc.)
- **Chat Hidden After Checklist**: Once checklist is generated, chat is hidden (checklist is primary value)

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

### Backend Issues

- **Database errors**: Ensure PostgreSQL is running and accessible. Check connection string in `.env`
- **Connection refused**: Make sure PostgreSQL container is running: `docker ps | grep postgres`
- **OpenAI API errors**: Verify your API key is correct and has sufficient credits
- **Import errors**: Ensure all dependencies are installed: `pip install -r requirements.txt`

### Frontend Issues

- **API connection errors**: Verify `NEXT_PUBLIC_API_URL` points to the correct backend URL
- **Build errors**: Clear `.next` directory and rebuild: `rm -rf .next && npm run build`
- **Component errors**: Ensure all shadcn/ui dependencies are installed

### Docker Issues

- **Port conflicts**: Change ports in `docker-compose.yml` if 3000 or 8000 are in use
- **Build failures**: Ensure Docker has sufficient resources allocated
- **Environment variables**: Verify `.env` file is in the project root

## License

This project is a case study implementation.

## Documentation

- **REQUIREMENTS_COVERAGE.md**: Detailed analysis of how we meet all task requirements
- **DESIGN_DECISIONS.md**: Product, AI, and architectural decisions with rationale
- **ENHANCEMENTS.md**: Recommended enhancements for V2
- **SUBMISSION.md**: Comprehensive answer to all task questions

## Demo Script

For a 3–5 minute demo:

1. **Problem Statement** (30s): Interview preparation is overwhelming
2. **Solution Demo** (2-3min):
   - Enter goal: "I have a frontend interview in 10 days"
   - Show AI asking for job description
   - Paste job description
   - Show auto-generated checklist with grouped tasks + next 3 actions
   - Check off a few tasks
   - Show "Test Knowledge" button on Skills item
   - Demonstrate AI interviewer (4 questions, rating, auto-completion)
3. **Key Design Decisions** (1min): Chat-first → Checklist-first, AI interviewer value
4. **V2 Ideas** (30s): Timeline view, progress analytics, export

