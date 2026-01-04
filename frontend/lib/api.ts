const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface CreateSessionRequest {
  user_goal_text: string;
}

export interface CreateSessionResponse {
  session_id: string;
  event_type: string;
  title: string;
}

export interface TodoItem {
  id: string;
  group_key: string;
  text: string;
  status: "todo" | "done";
  priority?: "high" | "med" | "low";
  estimate_minutes?: number;
  rationale?: string;
}

export interface ChecklistGroup {
  key: string;
  label: string;
  items: TodoItem[];
}

export interface ChecklistStructure {
  title: string;
  event_type: string;
  assumptions: string[];
  groups: ChecklistGroup[];
  next_3_actions: string[];
}

export interface GetSessionResponse {
  session_id: string;
  created_at: string;
  event_type: string;
  title: string;
  user_goal_text: string;
  context: Record<string, any>;
  checklist: ChecklistStructure | null;
  messages: Array<{ role: string; content: string }>;
}

export async function createSession(
  request: CreateSessionRequest
): Promise<CreateSessionResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/sessions`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error("API Error:", errorText);
      throw new Error(`Failed to create session: ${response.status} ${response.statusText}`);
    }

    return response.json();
  } catch (error) {
    if (error instanceof TypeError && error.message.includes("fetch")) {
      throw new Error(`Network error: Unable to connect to backend at ${API_BASE_URL}. Make sure the backend is running.`);
    }
    throw error;
  }
}

export async function getSession(
  sessionId: string
): Promise<GetSessionResponse> {
  const response = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}`);

  if (!response.ok) {
    throw new Error(`Failed to get session: ${response.statusText}`);
  }

  return response.json();
}

export async function updateTodo(
  sessionId: string,
  todoId: string,
  updates: { status?: string; text?: string }
): Promise<TodoItem> {
  const response = await fetch(
    `${API_BASE_URL}/api/sessions/${sessionId}/todos/${todoId}`,
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(updates),
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to update todo: ${response.statusText}`);
  }

  return response.json();
}

export interface InterviewQuestion {
  question: string;
  question_number: number;
  total_questions: number;
}

export interface InterviewResponse {
  question?: InterviewQuestion;
  feedback?: string;
  is_complete: boolean;
  overall_feedback?: string;
  rating?: number;
  passed?: boolean;
}

export async function startInterview(
  sessionId: string,
  todoId: string,
  todoText: string
): Promise<InterviewResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/sessions/${sessionId}/interview/start`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        todo_id: todoId,
        todo_text: todoText,
      }),
    }
  );

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to start interview: ${response.statusText} - ${errorText}`);
  }

  return response.json();
}

export async function answerInterviewQuestion(
  sessionId: string,
  todoId: string,
  answer: string
): Promise<InterviewResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/sessions/${sessionId}/interview/${todoId}/answer`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ answer }),
    }
  );

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to answer question: ${response.statusText} - ${errorText}`);
  }

  return response.json();
}

export interface SessionListItem {
  session_id: string;
  title: string;
  event_type: string;
  created_at: string;
}

export async function listSessions(): Promise<SessionListItem[]> {
  const response = await fetch(`${API_BASE_URL}/api/sessions`);

  if (!response.ok) {
    throw new Error(`Failed to list sessions: ${response.statusText}`);
  }

  return response.json();
}

export async function deleteSession(sessionId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}`, {
    method: "DELETE",
  });

  if (!response.ok) {
    throw new Error(`Failed to delete session: ${response.statusText}`);
  }
}

export interface SendMessageRequest {
  content: string;
}

export interface SendMessageResponse {
  session_id: string;
  message: { role: string; content: string };
  messages: Array<{ role: string; content: string }>;
  checklist?: ChecklistStructure; // Include checklist if auto-generated
}

export async function sendMessage(
  sessionId: string,
  request: SendMessageRequest
): Promise<SendMessageResponse> {
  const response = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}/message`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error("API Error:", errorText);
    throw new Error(`Failed to send message: ${response.statusText} - ${errorText}`);
  }

  return response.json();
}

