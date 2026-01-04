from sqlmodel import SQLModel, Field, Column, JSON
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class EventType(str, Enum):
    INTERVIEW = "interview"
    PRESENTATION = "presentation"
    PERFORMANCE_REVIEW = "performance_review"
    NEGOTIATION = "negotiation"
    OTHER = "other"


class TodoStatus(str, Enum):
    TODO = "todo"
    DONE = "done"


class Priority(str, Enum):
    HIGH = "high"
    MED = "med"
    LOW = "low"


# Pydantic models for API responses
class TodoItem(BaseModel):
    id: str
    group_key: str
    text: str
    status: TodoStatus = TodoStatus.TODO
    priority: Optional[Priority] = None
    estimate_minutes: Optional[int] = None
    rationale: Optional[str] = None


class ChecklistGroup(BaseModel):
    key: str
    label: str
    items: List[TodoItem] = []


class ChecklistStructure(BaseModel):
    title: str
    event_type: str
    assumptions: List[str] = []
    groups: List[ChecklistGroup] = []
    next_3_actions: List[str] = []


class SessionModel(SQLModel, table=True):
    id: str = Field(primary_key=True)
    created_at: datetime
    event_type: EventType
    title: str
    user_goal_text: str
    context: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    checklist: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    messages: List[Dict[str, str]] = Field(default_factory=list, sa_column=Column(JSON))
    interview_sessions: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))  # Store interview sessions by todo_id

