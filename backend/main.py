from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlmodel import SQLModel, create_engine, Session, select
from sqlalchemy.orm.attributes import flag_modified
from typing import Optional, Dict, Any
import uuid
import os
from datetime import datetime

from models import SessionModel, TodoItem, ChecklistGroup, ChecklistStructure
from schemas import (
    CreateSessionRequest,
    CreateSessionResponse,
    SendMessageRequest,
    SendMessageResponse,
    GetSessionResponse,
    UpdateTodoRequest,
    StartInterviewRequest,
    InterviewAnswerRequest,
    InterviewResponse,
    InterviewQuestion,
)
from ai_service import AIService
from dotenv import load_dotenv

load_dotenv()

# Database setup - PostgreSQL
database_url = os.getenv("DATABASE_URL")
engine = create_engine(database_url, echo=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup
    SQLModel.metadata.create_all(engine)
    
    # Run Alembic migrations
    try:
        from alembic.config import Config
        from alembic import command
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        print("✓ Database migrations applied")
    except Exception as e:
        print(f"Migration check failed: {e}")
    
    yield


app = FastAPI(
    title="InterviewHub API",
    description="AI-powered readiness checklist generator",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware - allow origins from environment or default to localhost
cors_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,http://46.224.4.80:3000"
).split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ai_service = AIService()


@app.post("/api/sessions", response_model=CreateSessionResponse)
def create_session(request: CreateSessionRequest):
    """Create a new session from user goal text."""
    try:
        session_id = str(uuid.uuid4())
        
        # Classify event type
        event_type = ai_service.classify_event_type(request.user_goal_text)
        
        # Generate title
        title = ai_service.generate_title(request.user_goal_text, event_type)
        
        # Generate initial AI response
        initial_messages = [{"role": "user", "content": request.user_goal_text}]
        initial_response = ai_service.generate_conversational_response(
            messages=initial_messages,
            event_type=event_type,
            context={}
        )
        
        # Create session in database with initial messages
        with Session(engine) as db_session:
            db_session_model = SessionModel(
                id=session_id,
                created_at=datetime.utcnow(),
                event_type=event_type,
                title=title,
                user_goal_text=request.user_goal_text,
                context={},
                checklist=None,
                messages=[
                    {
                        "role": "user",
                        "content": request.user_goal_text
                    },
                    {
                        "role": "assistant",
                        "content": initial_response
                    }
                ]
            )
        db_session.add(db_session_model)
        db_session.commit()
        db_session.refresh(db_session_model)
        
        # Followup questions are now handled via chat messages, but we still return the structure for compatibility
        followup_question = ai_service.get_followup_question(event_type, context={})
        
        return CreateSessionResponse(
            session_id=session_id,
            event_type=event_type,
            title=title,
            followup_question=followup_question
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")


@app.post("/api/sessions/{session_id}/message", response_model=SendMessageResponse)
def send_message(session_id: str, request: SendMessageRequest):
    """Send a message in the conversation and get AI response."""
    try:
        with Session(engine) as db_session:
            # Get session
            statement = select(SessionModel).where(SessionModel.id == session_id)
            session = db_session.exec(statement).first()
            
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            
            # Ensure messages is a list (handle case where it might be None or not properly loaded)
            if session.messages is None:
                session.messages = []
            
            # Create a new list to ensure SQLModel detects the change
            messages_list = list(session.messages) if session.messages else []
            
            # Add user message
            user_message = {"role": "user", "content": request.content}
            messages_list.append(user_message)
            
            # Extract context from messages and update session context
            extracted_context = ai_service.extract_context_from_messages(messages_list, session.event_type)
            current_context = session.context or {}
            current_context.update(extracted_context)
            session.context = current_context
            
            # Check if we have enough information to generate checklist
            has_enough_info = ai_service.has_enough_information(
                session.event_type, 
                current_context, 
                messages_list
            )
            
            checklist_generated = False
            if has_enough_info and not session.checklist:
                # Auto-generate checklist
                try:
                    checklist = ai_service.generate_checklist(
                        event_type=session.event_type,
                        user_goal_text=session.user_goal_text,
                        answers=current_context
                    )
                    session.checklist = checklist.model_dump()
                    checklist_generated = True
                except Exception as checklist_error:
                    import traceback
                    traceback.print_exc()
                    # Continue with normal conversation even if checklist generation fails
            
            # Generate AI response
            try:
                if checklist_generated:
                    # If checklist was just generated, inform the user
                    ai_response = "Perfect! I've gathered enough information to create your personalized preparation checklist. I've generated it for you - you can see it on the right side. Let me know if you'd like to discuss any specific items or need clarification on anything!"
                else:
                    ai_response = ai_service.generate_conversational_response(
                        messages=messages_list,
                        event_type=session.event_type,
                        context=current_context
                    )
                
                if not ai_response or not ai_response.strip():
                    ai_response = "I apologize, but I didn't receive a response. Please try again or check if your API quota is available."
            except Exception as ai_error:
                import traceback
                traceback.print_exc()
                ai_response = f"I encountered an error while generating a response: {str(ai_error)[:200]}. Please check the backend logs for more details."
            
            # Add AI response
            assistant_message = {"role": "assistant", "content": ai_response}
            messages_list.append(assistant_message)
            
            # Update session with the new messages list (this ensures SQLModel detects the change)
            session.messages = messages_list
            
            # Save session
            db_session.add(session)
            db_session.commit()
            db_session.refresh(session)
        
        return SendMessageResponse(
            session_id=session_id,
            message=assistant_message,
            messages=session.messages,
            checklist=session.checklist  # Include checklist in response if generated
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")


@app.get("/api/sessions/{session_id}", response_model=GetSessionResponse)
def get_session(session_id: str):
    """Get session with checklist and messages."""
    with Session(engine) as db_session:
        statement = select(SessionModel).where(SessionModel.id == session_id)
        session = db_session.exec(statement).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        checklist = None
        if session.checklist:
            try:
                checklist = ChecklistStructure.model_validate(session.checklist)
            except Exception as e:
                # If validation fails, try to parse as dict
                if isinstance(session.checklist, dict):
                    checklist = ChecklistStructure(**session.checklist)
                else:
                    raise e
        
        return GetSessionResponse(
            session_id=session.id,
            created_at=session.created_at,
            event_type=session.event_type,
            title=session.title,
            user_goal_text=session.user_goal_text,
            context=session.context or {},
            checklist=checklist,
            messages=session.messages or []
        )


@app.patch("/api/sessions/{session_id}/todos/{todo_id}")
def update_todo(session_id: str, todo_id: str, request: UpdateTodoRequest):
    """Update todo status or text."""
    with Session(engine) as db_session:
        statement = select(SessionModel).where(SessionModel.id == session_id)
        session = db_session.exec(statement).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if not session.checklist:
            raise HTTPException(status_code=400, detail="No checklist found")
        
        checklist = ChecklistStructure.model_validate(session.checklist)
        
        # Find and update todo
        todo_found = False
        for group in checklist.groups:
            for item in group.items:
                if item.id == todo_id:
                    todo_found = True
                    if request.status is not None:
                        item.status = request.status
                    if request.text is not None:
                        item.text = request.text
                    break
            if todo_found:
                break
        
        if not todo_found:
            raise HTTPException(status_code=404, detail="Todo not found")
        
        # Save updated checklist
        session.checklist = checklist.model_dump()
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)
        
        # Return updated todo
        for group in checklist.groups:
            for item in group.items:
                if item.id == todo_id:
                    return item


@app.delete("/api/sessions/{session_id}")
def delete_session(session_id: str):
    """Delete a session by ID."""
    with Session(engine) as db_session:
        session = db_session.get(SessionModel, session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        db_session.delete(session)
        db_session.commit()
        return {"message": "Session deleted successfully"}


@app.get("/api/sessions")
def list_sessions(limit: int = 50, offset: int = 0):
    """List all sessions, ordered by created_at descending."""
    with Session(engine) as db_session:
        statement = (
            select(SessionModel)
            .order_by(SessionModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        sessions = db_session.exec(statement).all()
        
        return [
            {
                "session_id": session.id,
                "title": session.title,
                "event_type": session.event_type,
                "created_at": session.created_at.isoformat(),
            }
            for session in sessions
        ]


@app.post("/api/sessions/{session_id}/interview/start", response_model=InterviewResponse)
def start_interview(session_id: str, request: StartInterviewRequest):
    """Start an AI interview/test session for a checklist item."""
    with Session(engine) as db_session:
        statement = select(SessionModel).where(SessionModel.id == session_id)
        session = db_session.exec(statement).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if not session.checklist:
            raise HTTPException(status_code=400, detail="No checklist found")
        
        # Get checklist and find the todo item
        checklist = ChecklistStructure.model_validate(session.checklist)
        todo_item = None
        for group in checklist.groups:
            for item in group.items:
                if item.id == request.todo_id:
                    todo_item = item
                    break
            if todo_item:
                break
        
        if not todo_item:
            raise HTTPException(status_code=404, detail="Todo item not found")
        
        # Only allow interviews for Skills items
        if todo_item.group_key != "skills":
            raise HTTPException(status_code=400, detail="Interviews are only available for Skills / Knowledge Prep items")
        
        # Build context for interview
        interview_context = {
            "user_goal_text": session.user_goal_text,
            **(session.context or {})
        }
        
        # Start interview
        try:
            result = ai_service.start_interview(
                todo_text=request.todo_text,
                todo_id=request.todo_id,
                context=interview_context,
                event_type=session.event_type
            )
            
            # Store interview session
            if not hasattr(session, 'interview_sessions') or session.interview_sessions is None:
                session.interview_sessions = {}
            
            # Validate todo_id is a proper UUID
            import re
            uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
            if not re.match(uuid_pattern, request.todo_id.lower()):
                raise HTTPException(status_code=400, detail=f"Invalid todo_id format: {request.todo_id}. Please refresh the page and try again.")
            
            # Ensure interview_sessions is a dict (not None)
            if session.interview_sessions is None:
                session.interview_sessions = {}
            
            # Create a new dict to ensure SQLModel detects the change
            updated_interview_sessions = dict(session.interview_sessions)
            updated_interview_sessions[request.todo_id] = {
                "todo_id": request.todo_id,
                "todo_text": request.todo_text,
                "history": [
                    {"role": "assistant", "content": result.get("question", "")}
                ],
                "current_question": result.get("question_number", 1),
                "total_questions": result.get("total_questions", 4),
                "status": "in_progress"
            }
            
            # Assign the new dict to trigger SQLModel change detection
            session.interview_sessions = updated_interview_sessions
            
            # Explicitly mark the JSON field as modified (required for SQLModel/SQLAlchemy)
            flag_modified(session, "interview_sessions")
            
            db_session.add(session)
            db_session.commit()
            db_session.refresh(session)
            
            return InterviewResponse(
                question=InterviewQuestion(
                    question=result.get("question", ""),
                    question_number=result.get("question_number", 1),
                    total_questions=result.get("total_questions", 4)
                ),
                is_complete=False
            )
        except Exception as e:
            print(f"Error starting interview: {e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Failed to start interview: {str(e)}")


@app.post("/api/sessions/{session_id}/interview/{todo_id}/answer", response_model=InterviewResponse)
def answer_interview_question(session_id: str, todo_id: str, request: InterviewAnswerRequest):
    """Answer an interview question and get next question or results."""
    with Session(engine) as db_session:
        statement = select(SessionModel).where(SessionModel.id == session_id)
        session = db_session.exec(statement).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Ensure interview_sessions is a dict (not None)
        if session.interview_sessions is None:
            session.interview_sessions = {}
        
        # Convert to dict if needed (handle JSON deserialization)
        if not isinstance(session.interview_sessions, dict):
            session.interview_sessions = {}
        
        if todo_id not in session.interview_sessions:
            db_session.refresh(session)
            if todo_id not in (session.interview_sessions or {}):
                raise HTTPException(status_code=404, detail=f"Interview session not found for todo_id: {todo_id}")
        
        interview_session = session.interview_sessions[todo_id]
        
        # Add answer to history
        interview_session["history"].append({"role": "user", "content": request.answer})
        
        # Build context
        interview_context = {
            "user_goal_text": session.user_goal_text,
            **(session.context or {})
        }
        
        # Continue interview
        try:
            result = ai_service.continue_interview(
                todo_text=interview_session["todo_text"],
                todo_id=todo_id,
                context=interview_context,
                event_type=session.event_type,
                interview_history=interview_session["history"],
                answer=request.answer
            )
            
            if result.get("is_complete"):
                # Interview complete
                interview_session["status"] = "completed"
                interview_session["rating"] = result.get("rating", 0)
                interview_session["passed"] = result.get("passed", False)
                interview_session["overall_feedback"] = result.get("overall_feedback", "")
                
                # Update the session in the dictionary (important for SQLModel to detect changes)
                updated_interview_sessions = dict(session.interview_sessions) if session.interview_sessions else {}
                updated_interview_sessions[todo_id] = interview_session
                session.interview_sessions = updated_interview_sessions
                
                # Explicitly mark the field as modified
                flag_modified(session, "interview_sessions")
                
                db_session.add(session)
                db_session.commit()
                db_session.refresh(session)
                
                return InterviewResponse(
                    is_complete=True,
                    overall_feedback=result.get("overall_feedback", ""),
                    rating=result.get("rating", 0),
                    passed=result.get("passed", False)
                )
            else:
                # Add feedback and next question to history
                if result.get("feedback"):
                    interview_session["history"].append({"role": "assistant", "content": f"Feedback: {result.get('feedback')}"})
                
                if result.get("question"):
                    interview_session["history"].append({"role": "assistant", "content": result.get("question")})
                    interview_session["current_question"] = result.get("question_number", interview_session.get("current_question", 1) + 1)
                
                # Update the session in the dictionary (important for SQLModel to detect changes)
                updated_interview_sessions = dict(session.interview_sessions) if session.interview_sessions else {}
                updated_interview_sessions[todo_id] = interview_session
                session.interview_sessions = updated_interview_sessions
                
                # Explicitly mark the field as modified
                flag_modified(session, "interview_sessions")
                
                db_session.add(session)
                db_session.commit()
                db_session.refresh(session)
                
                return InterviewResponse(
                    question=InterviewQuestion(
                        question=result.get("question", ""),
                        question_number=result.get("question_number", interview_session.get("current_question", 1)),
                        total_questions=interview_session.get("total_questions", 4)
                    ),
                    feedback=result.get("feedback"),
                    is_complete=False
                )
        except Exception as e:
            print(f"Error continuing interview: {e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Failed to continue interview: {str(e)}")


@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

