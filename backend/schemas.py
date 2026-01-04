from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
from models import ChecklistStructure, TodoItem, Priority


class CreateSessionRequest(BaseModel):
    user_goal_text: str


class FollowupQuestionField(BaseModel):
    key: str
    label: str
    type: str  # "textarea", "input", "select"
    required: bool = True


class FollowupQuestion(BaseModel):
    id: str
    question: str
    fields: List[FollowupQuestionField]


class CreateSessionResponse(BaseModel):
    session_id: str
    event_type: str
    title: str
    followup_question: FollowupQuestion  # Still used for initial response structure


class SendMessageRequest(BaseModel):
    content: str


class SendMessageResponse(BaseModel):
    session_id: str
    message: Dict[str, str]  # {role: "assistant", content: "..."}
    messages: List[Dict[str, str]]
    checklist: Optional[ChecklistStructure] = None  # Include checklist if auto-generated


class GetSessionResponse(BaseModel):
    session_id: str
    created_at: datetime
    event_type: str
    title: str
    user_goal_text: str
    context: Dict[str, Any]
    checklist: Optional[ChecklistStructure]
    messages: List[Dict[str, str]]


class UpdateTodoRequest(BaseModel):
    status: Optional[str] = None
    text: Optional[str] = None


class StartInterviewRequest(BaseModel):
    todo_id: str
    todo_text: str
    context: Optional[Dict[str, Any]] = None


class InterviewQuestion(BaseModel):
    question: str
    question_number: int
    total_questions: int


class InterviewAnswerRequest(BaseModel):
    answer: str


class InterviewResponse(BaseModel):
    question: Optional[InterviewQuestion] = None  # Next question or None if done
    feedback: Optional[str] = None  # Feedback on current answer
    is_complete: bool
    overall_feedback: Optional[str] = None  # Final feedback when complete
    rating: Optional[float] = None  # 0-10 rating
    passed: Optional[bool] = None  # Whether they passed the test
