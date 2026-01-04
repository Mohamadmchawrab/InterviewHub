import os
import json
import uuid
from typing import Dict, Any, List, Optional
from openai import OpenAI
from models import EventType, ChecklistStructure, ChecklistGroup, TodoItem, TodoStatus, Priority
from schemas import FollowupQuestion, FollowupQuestionField  # Still used for initial session creation
from dotenv import load_dotenv

load_dotenv()


class AIService:
    def __init__(self):
        self._client = None
        self._api_key = os.getenv("OPENAI_API_KEY")
        if not self._api_key:
            print("WARNING: OPENAI_API_KEY not found in environment variables")
        else:
            print(f"INFO: OpenAI API key loaded (starts with: {self._api_key[:10]}...)")
    
    @property
    def client(self):
        """Lazy initialization of OpenAI client."""
        if self._client is None and self._api_key:
            try:
                # Initialize with explicit parameters to avoid proxy issues
                import httpx
                self._client = OpenAI(
                    api_key=self._api_key,
                    http_client=httpx.Client(proxies=None, trust_env=False)
                )
            except Exception as e:
                print(f"Warning: Failed to initialize OpenAI client: {e}")
                # Fallback: try without explicit http_client
                try:
                    self._client = OpenAI(api_key=self._api_key)
                except Exception as e2:
                    print(f"Warning: Fallback initialization also failed: {e2}")
                    return None
        return self._client
    
    def _get_available_models(self):
        """Get list of available models from OpenAI, cached."""
        if not hasattr(self, '_cached_models'):
            try:
                if self.client:
                    models = self.client.models.list()
                    # Filter for chat-compatible models
                    chat_models = [
                        m.id for m in models.data 
                        if 'gpt' in m.id.lower() or 'chat' in m.id.lower()
                    ]
                    # Prioritize common models
                    preferred = ["gpt-4o-mini", "gpt-3.5-turbo-0125", "gpt-3.5-turbo-1106", "gpt-3.5-turbo"]
                    ordered = [m for m in preferred if m in chat_models] + [m for m in chat_models if m not in preferred]
                    self._cached_models = ordered[:5]  # Keep top 5
                    print(f"Found available models: {self._cached_models}")
                else:
                    self._cached_models = []
            except Exception as e:
                print(f"Error fetching available models: {e}")
                self._cached_models = []
        return self._cached_models or ["gpt-3.5-turbo-0125", "gpt-3.5-turbo-1106", "gpt-3.5-turbo"]
    
    def _create_completion_with_fallback(self, messages, temperature=0.7, max_tokens=1000, response_format=None):
        """Create a chat completion, trying multiple models if one fails."""
        models_to_try = self._get_available_models()
        last_error = None
        
        for model_name in models_to_try:
            try:
                params = {
                    "model": model_name,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
                if response_format:
                    params["response_format"] = response_format
                    
                response = self.client.chat.completions.create(**params)
                print(f"Successfully used model: {model_name}")
                return response
            except Exception as model_error:
                last_error = model_error
                error_str = str(model_error).lower()
                error_code = getattr(model_error, 'code', None)
                if ("not have access" in error_str or 
                    "model_not_found" in error_str or 
                    error_code == 'model_not_found' or
                    "403" in str(model_error)):
                    print(f"Model {model_name} not available, trying next...")
                    continue
                else:
                    raise
        
        if last_error:
            raise Exception(f"None of the models worked. Last error: {last_error}")
        raise Exception("No models available")
    
    def classify_event_type(self, user_goal_text: str) -> str:
        """Classify the event type from user goal text."""
        if not self.client:
            # Fallback to keyword matching
            text_lower = user_goal_text.lower()
            if "interview" in text_lower:
                return "interview"
            elif "presentation" in text_lower:
                return "presentation"
            elif "review" in text_lower or "performance" in text_lower:
                return "performance_review"
            elif "negotiation" in text_lower or "negotiate" in text_lower:
                return "negotiation"
            return "other"
        
        prompt = f"""Classify the following user goal into one of these event types: interview, presentation, performance_review, negotiation, other.

User goal: "{user_goal_text}"

Respond with ONLY the event type (one word, lowercase)."""
        
        try:
            response = self._create_completion_with_fallback(
                messages=[
                    {"role": "system", "content": "You are a classification assistant. Respond with only the event type."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=10
            )
            event_type = response.choices[0].message.content.strip().lower()
            
            # Validate event type
            valid_types = ["interview", "presentation", "performance_review", "negotiation", "other"]
            if event_type not in valid_types:
                # Try to match partial
                for vt in valid_types:
                    if vt in event_type or event_type in vt:
                        return vt
                return "other"
            return event_type
        except Exception as e:
            print(f"Error classifying event type: {e}")
            # Fallback: simple keyword matching
            text_lower = user_goal_text.lower()
            if "interview" in text_lower:
                return "interview"
            elif "presentation" in text_lower:
                return "presentation"
            elif "review" in text_lower or "performance" in text_lower:
                return "performance_review"
            elif "negotiation" in text_lower or "negotiate" in text_lower:
                return "negotiation"
            return "other"
    
    def generate_title(self, user_goal_text: str, event_type: str) -> str:
        """Generate a short title for the session."""
        if not self.client:
            # Fallback: use first 50 chars of user goal
            return user_goal_text[:50] if len(user_goal_text) > 50 else user_goal_text
        
        prompt = f"""Generate a short, concise title (max 50 characters) for this event:

User goal: "{user_goal_text}"
Event type: {event_type}

Respond with ONLY the title, no quotes."""
        
        try:
            response = self._create_completion_with_fallback(
                messages=[
                    {"role": "system", "content": "You are a title generator. Respond with only the title, no quotes or extra text."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=30
            )
            return response.choices[0].message.content.strip().strip('"').strip("'")
        except Exception as e:
            print(f"Error generating title: {e}")
            # Fallback
            return user_goal_text[:50] if len(user_goal_text) > 50 else user_goal_text
    
    def get_followup_question(self, event_type: str, context: Dict[str, Any] = None) -> FollowupQuestion:
        """Get follow-up question based on event type."""
        context = context or {}
        
        questions = {
            "interview": FollowupQuestion(
                id="q1",
                question="To create your personalized readiness checklist, I need a few details. If you've already shared some of this in our chat, feel free to copy it here or add any missing information.",
                fields=[
                    FollowupQuestionField(
                        key="job_description",
                        label="Job description * (Paste the full job description here)",
                        type="textarea",
                        required=True
                    ),
                    FollowupQuestionField(
                        key="company",
                        label="Company name (e.g., Google, Microsoft, Startup Inc.)",
                        type="input",
                        required=False
                    ),
                    FollowupQuestionField(
                        key="interview_format",
                        label="Interview format (e.g., Coding + System Design + Behavioral)",
                        type="input",
                        required=False
                    ),
                    FollowupQuestionField(
                        key="technologies",
                        label="Key technologies/frameworks (e.g., React, Node.js, Python, AWS)",
                        type="input",
                        required=False
                    ),
                    FollowupQuestionField(
                        key="timeline",
                        label="Interview timeline (e.g., Next week, In 2 weeks)",
                        type="input",
                        required=False
                    )
                ]
            ),
            "presentation": FollowupQuestion(
                id="q1",
                question="To create the best preparation plan, I need a few details about your presentation.",
                fields=[
                    FollowupQuestionField(
                        key="audience",
                        label="Who is your audience?",
                        type="textarea",
                        required=True
                    ),
                    FollowupQuestionField(
                        key="goal",
                        label="What is your main goal?",
                        type="textarea",
                        required=True
                    ),
                    FollowupQuestionField(
                        key="duration",
                        label="Duration (e.g., 30 minutes)",
                        type="input",
                        required=False
                    )
                ]
            ),
            "performance_review": FollowupQuestion(
                id="q1",
                question="Let me understand your performance review context better.",
                fields=[
                    FollowupQuestionField(
                        key="role_expectations",
                        label="What are your role expectations?",
                        type="textarea",
                        required=True
                    ),
                    FollowupQuestionField(
                        key="review_period",
                        label="Review period (e.g., Q4 2024)",
                        type="input",
                        required=False
                    ),
                    FollowupQuestionField(
                        key="previous_feedback",
                        label="Any previous feedback received?",
                        type="textarea",
                        required=False
                    )
                ]
            ),
            "negotiation": FollowupQuestion(
                id="q1",
                question="To prepare you effectively, I need to understand your negotiation context.",
                fields=[
                    FollowupQuestionField(
                        key="target_outcome",
                        label="What is your target outcome?",
                        type="textarea",
                        required=True
                    ),
                    FollowupQuestionField(
                        key="constraints",
                        label="Any constraints or limitations?",
                        type="textarea",
                        required=False
                    ),
                    FollowupQuestionField(
                        key="context",
                        label="Context (offer/raise/client/etc.)",
                        type="input",
                        required=False
                    )
                ]
            ),
            "other": FollowupQuestion(
                id="q1",
                question="Tell me more about what you're preparing for.",
                fields=[
                    FollowupQuestionField(
                        key="details",
                        label="Additional details",
                        type="textarea",
                        required=True
                    )
                ]
            )
        }
        
        return questions.get(event_type, questions["other"])
    
    def generate_conversational_response(
        self, 
        messages: List[Dict[str, str]], 
        event_type: str,
        context: Dict[str, Any]
    ) -> str:
        """Generate a conversational response based on the chat history."""
        if not self.client:
            if not self._api_key:
                return "I'm here to help you prepare! However, I need an OpenAI API key to provide full assistance. Please configure OPENAI_API_KEY in the backend .env file."
            else:
                return "I'm here to help you prepare! However, there's an issue with the OpenAI API client initialization. Please check the backend logs for more details."
        
        system_prompt = """You are InterviewHub, a structured AI preparation assistant. Your role is to efficiently gather information needed to create a personalized, actionable preparation checklist.

Your approach:
- Be friendly but focused - your goal is to gather key information quickly
- PROACTIVELY ask for essential information in a structured way
- For interviews, you MUST gather:
  1. Job description (most important - ask for this first!)
  2. Interview format (coding challenges, system design, behavioral, etc.)
  3. Company name
  4. Key technologies/frameworks mentioned
  5. Timeline (when is the interview?)
- For other events: Ask relevant structured questions based on the event type
- Once you have enough information, the system will automatically generate a personalized checklist
- Keep responses concise - focus on gathering information, not lengthy explanations

IMPORTANT - Structured information gathering:
- Don't wait for users to volunteer information - ask for it proactively!
- If they mention an interview, immediately ask: "That's exciting! To create the best preparation plan, could you share the job description? This will help me tailor the checklist to the specific role."
- Ask ONE question at a time, or group related questions together (max 2-3 questions per response)
- Once you've gathered key information (especially job description for interviews), acknowledge it briefly and wait for the system to generate the checklist automatically

Keep responses short and focused on information gathering. Be warm but efficient."""
        
        try:
            # Build conversation history
            conversation = [{"role": "system", "content": system_prompt}]
            
            # Add context about the event type and what information we need
            # (OpenAI doesn't allow multiple system messages)
            if event_type:
                context_guidance = {
                    "interview": "The user is preparing for an interview. IMPORTANT: You should proactively ask for the job description early in the conversation. Also ask about interview format (coding, system design, behavioral), company name, technologies mentioned, and timeline.",
                    "presentation": "The user is preparing for a presentation. Ask about the audience, topic, duration, format (in-person/virtual), and key objectives.",
                    "performance_review": "The user is preparing for a performance review. Ask about their role, achievements they want to highlight, areas for improvement, and goals.",
                    "negotiation": "The user is preparing for a negotiation. Ask about what they're negotiating (salary, contract, terms), their current situation, and desired outcomes.",
                }
                guidance = context_guidance.get(event_type, f"The user is preparing for a {event_type}.")
                conversation.append({
                    "role": "user",
                    "content": f"[Context: {guidance} Be proactive in asking for this information to create a personalized preparation plan.]"
                })
            
            # Add all previous messages (filter out any empty or invalid messages)
            for msg in messages:
                if msg and isinstance(msg, dict) and "role" in msg and "content" in msg:
                    if msg["role"] in ["user", "assistant"] and msg["content"]:
                        conversation.append({
                            "role": msg["role"],
                            "content": str(msg["content"])
                        })
            
            if not self.client:
                return "I'm here to help you prepare! However, I need an OpenAI API key to provide full assistance. Please configure your API key in the backend .env file."
            
            response = self._create_completion_with_fallback(
                messages=conversation,
                temperature=0.7,
                max_tokens=1000
            )
            
            if not response or not response.choices or not response.choices[0].message:
                return "I received an unexpected response format. Please try again."
            
            return response.choices[0].message.content or "I apologize, but I couldn't generate a response. Please try again."
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Error generating conversational response: {e}")
            print(f"Traceback: {error_details}")
            
            # Handle specific error cases
            error_str = str(e).lower()
            error_code = getattr(e, 'code', None) or getattr(e, 'status_code', None)
            error_type = getattr(e, 'type', None) or ''
            
            # Extract error details from OpenAI error response if available
            try:
                error_body = getattr(e, 'body', {}) or {}
                if isinstance(error_body, dict):
                    error_info = error_body.get('error', {}) or {}
                    if isinstance(error_info, dict):
                        error_type = error_info.get('type', error_type) or error_type
                        error_code = error_info.get('code', error_code) or error_code
                        error_message = error_info.get('message', '') or ''
                        error_str = error_str + ' ' + error_message.lower()
            except:
                pass  # If error extraction fails, use the original error
            
            # Check for quota/rate limit errors FIRST (most common issue)
            if (error_code == 429 or 
                "429" in str(e) or 
                "quota" in error_str or 
                "exceeded" in error_str or
                "insufficient_quota" in error_str or
                "rate_limit" in error_str or
                error_type == 'insufficient_quota' or
                "exceeded your current quota" in error_str):
                return """I'm currently unable to generate AI responses because your OpenAI API quota has been exceeded. 

To fix this:
1. Check your OpenAI account billing and usage at https://platform.openai.com/usage
2. Add a payment method at https://platform.openai.com/account/billing
3. Increase your quota limits or upgrade your plan
4. Wait for your quota to reset (usually monthly)

Once your quota is restored, I'll be able to help you prepare for your interview!"""
            
            # Check for model access errors
            if ("model" in error_str and "not have access" in error_str) or "model_not_found" in error_str or (error_code == 403 and "model" in error_str):
                return """I'm having trouble accessing the required AI models. Your API key is configured, but your OpenAI project doesn't have access to the models needed.

To fix this:
1. Check your OpenAI project settings at https://platform.openai.com/settings/organization
2. Ensure your project has access to GPT models
3. You may need to upgrade your plan or enable model access
4. Check the backend logs for the specific model access error"""
            
            if "api_key" in error_str or "authentication" in error_str or "invalid" in error_str:
                return "I need an OpenAI API key to help you. Please configure OPENAI_API_KEY in the backend .env file."
            
            # Return a more helpful error message
            return f"I apologize, but I'm having trouble generating a response right now. Error: {str(e)[:100]}. Please check the backend logs for more details."
    
    def has_enough_information(self, event_type: str, context: Dict[str, Any], messages: List[Dict[str, str]]) -> bool:
        """Check if we have enough information to generate a checklist."""
        if event_type == "interview":
            # For interviews, we need at least job description or key details
            required_fields = ["job_description", "company", "interview_format", "technologies", "timeline"]
            # Check if we have at least 2-3 key pieces of information
            info_count = sum(1 for field in required_fields if context.get(field) or any(field.replace("_", " ") in msg.get("content", "").lower() for msg in messages))
            
            # Also check if job description is mentioned in messages
            has_job_desc = any("job description" in msg.get("content", "").lower() or len(msg.get("content", "")) > 200 for msg in messages if msg.get("role") == "user")
            
            return info_count >= 3 or (has_job_desc and info_count >= 2)
        elif event_type == "presentation":
            return context.get("audience") and context.get("goal")
        elif event_type == "performance_review":
            return context.get("review_type") and context.get("goals")
        else:
            # For other types, check if we have at least some context
            return len(context) >= 2 or len([m for m in messages if m.get("role") == "user"]) >= 3
    
    def extract_context_from_messages(self, messages: List[Dict[str, str]], event_type: str) -> Dict[str, Any]:
        """Extract structured context from conversation messages."""
        context = {}
        conversation_text = " ".join([msg.get("content", "") for msg in messages])
        
        if event_type == "interview":
            # Try to extract key information from messages
            if "job description" in conversation_text.lower() or any(len(msg.get("content", "")) > 200 for msg in messages if msg.get("role") == "user"):
                # Find the longest user message (likely job description)
                user_messages = [msg for msg in messages if msg.get("role") == "user"]
                if user_messages:
                    longest_msg = max(user_messages, key=lambda m: len(m.get("content", "")))
                    if len(longest_msg.get("content", "")) > 200:
                        context["job_description"] = longest_msg.get("content", "")
            
            # Extract other fields from conversation
            if "company" not in context:
                for msg in messages:
                    content = msg.get("content", "").lower()
                    if any(company in content for company in ["google", "microsoft", "amazon", "meta", "apple", "netflix"]):
                        context["company"] = msg.get("content", "")
                        break
        
        return context
    
    def generate_checklist(self, event_type: str, user_goal_text: str, answers: Dict[str, Any]) -> ChecklistStructure:
        """Generate the readiness checklist using AI."""
        if not self.client:
            # Return fallback checklist if no API key
            return self._generate_fallback_checklist(event_type, user_goal_text)
        
        # Build context for AI
        context_text = f"Event type: {event_type}\n"
        context_text += f"User goal: {user_goal_text}\n"
        context_text += f"Answers provided:\n"
        for key, value in answers.items():
            context_text += f"- {key}: {value}\n"
        
        system_prompt = """You are InterviewHub, an expert preparation assistant. Your job is to create concise, actionable, checkable TODO items to prepare the user for an upcoming event.

Rules:
- Output ONLY valid JSON that matches this exact schema (no markdown, no code blocks):
{
  "title": "string",
  "event_type": "string",
  "assumptions": ["string"],
  "groups": [
    {
      "key": "context",
      "label": "Context Understanding",
      "items": [
        {
          "id": "uuid-string",
          "group_key": "context",
          "text": "Actionable task starting with a verb",
          "status": "todo",
          "priority": "high|med|low",
          "estimate_minutes": number,
          "rationale": "optional short reason"
        }
      ]
    },
    {
      "key": "skills",
      "label": "Skills / Knowledge Prep",
      "items": [...]
    },
    {
      "key": "evidence",
      "label": "Evidence & Examples",
      "items": [...]
    },
    {
      "key": "delivery",
      "label": "Delivery & Execution",
      "items": [...]
    },
    {
      "key": "logistics",
      "label": "Logistics & Risk",
      "items": [...]
    }
  ],
  "next_3_actions": ["action 1", "action 2", "action 3"]
}

Requirements:
- Group tasks into the 5 readiness dimensions (context, skills, evidence, delivery, logistics)
- Keep total tasks between 10 and 18
- Each task should start with a verb and be specific and checkable
- Include priority (high/med/low) for each task
- Include estimate_minutes when reasonable
- Include rationale for complex tasks
- Generate next_3_actions as the most urgent/immediate steps
- Include assumptions if information is missing
- Avoid generic advice - be specific to each users situation
- If time is short (<3 days mentioned), compress into urgent steps only"""
        
        user_prompt = f"""Generate a readiness checklist for this event:

{context_text}

Output the JSON checklist now."""
        
        try:
            response = self._create_completion_with_fallback(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            # Parse JSON
            checklist_dict = json.loads(content)
            
            # Validate and convert to ChecklistStructure
            # Ensure all required groups exist
            required_groups = {
                "context": "Context Understanding",
                "skills": "Skills / Knowledge Prep",
                "evidence": "Evidence & Examples",
                "delivery": "Delivery & Execution",
                "logistics": "Logistics & Risk"
            }
            
            groups = []
            for key, label in required_groups.items():
                group_data = None
                for g in checklist_dict.get("groups", []):
                    if g.get("key") == key:
                        group_data = g
                        break
                
                if group_data:
                    items = []
                    for item_data in group_data.get("items", []):
                        # Always generate a proper UUID - don't trust AI-generated IDs
                        item_id = item_data.get("id", "")
                        # Validate UUID format: should be 36 chars with dashes, or generate new one
                        is_valid_uuid = False
                        if item_id:
                            # Check if it looks like a UUID (has dashes and is the right length)
                            if len(item_id) == 36 and item_id.count("-") == 4:
                                # Check if it's a valid hex UUID format
                                parts = item_id.split("-")
                                if len(parts) == 5 and all(len(p) in [8, 4, 4, 4, 12] for p in parts):
                                    # Check if all parts are hex
                                    try:
                                        int(item_id.replace("-", ""), 16)
                                        is_valid_uuid = True
                                    except ValueError:
                                        pass
                        
                        if not is_valid_uuid:
                            item_id = str(uuid.uuid4())
                            print(f"Generated new UUID for item: {item_data.get('text', '')[:50]} -> {item_id}")
                        
                        items.append(TodoItem(
                            id=item_id,
                            group_key=key,
                            text=item_data.get("text", ""),
                            status=TodoStatus.TODO,
                            priority=Priority(item_data.get("priority", "med")) if item_data.get("priority") else None,
                            estimate_minutes=item_data.get("estimate_minutes"),
                            rationale=item_data.get("rationale")
                        ))
                    groups.append(ChecklistGroup(key=key, label=label, items=items))
                else:
                    # Create empty group if missing
                    groups.append(ChecklistGroup(key=key, label=label, items=[]))
            
            checklist = ChecklistStructure(
                title=checklist_dict.get("title", user_goal_text),
                event_type=event_type,
                assumptions=checklist_dict.get("assumptions", []),
                groups=groups,
                next_3_actions=checklist_dict.get("next_3_actions", [])
            )
            
            return checklist
            
        except Exception as e:
            print(f"Error generating checklist: {e}")
    
    def start_interview(self, todo_text: str, todo_id: str, context: Dict[str, Any], event_type: str) -> Dict[str, Any]:
        """Start an AI interview session for a specific checklist item."""
        if not self.client:
            raise Exception("OpenAI API client not available")
        
        # Build context for the interview
        context_text = f"Event type: {event_type}\n"
        context_text += f"User goal: {context.get('user_goal_text', '')}\n"
        if context.get('job_description'):
            context_text += f"Job description: {context.get('job_description')[:500]}\n"
        
        system_prompt = f"""You are an expert technical interviewer conducting a knowledge assessment. Your role is to test the candidate's understanding of: "{todo_text}"

Context about the interview preparation:
{context_text}

IMPORTANT RULES:
1. You MUST ask EXACTLY 4 questions before completing the interview
2. DO NOT complete the interview until all 4 questions have been asked AND answered
3. Evaluate each answer FAIRLY and ACCURATELY:
   - If an answer is CORRECT or shows good understanding, acknowledge this positively
   - If an answer is PARTIALLY correct, note what's right and what needs improvement
   - If an answer is WRONG, explain why and what the correct answer should be
3. Rating should be FAIR and reflect actual performance:
   - CORRECT answers should contribute positively to the rating
   - PARTIALLY correct answers should get moderate scores
   - WRONG answers should lower the score appropriately
4. Only complete the interview after asking EXACTLY 4 questions and receiving answers to all of them

Your task:
1. Ask EXACTLY 4 focused questions that test practical knowledge and understanding
2. Questions should be progressive (start easier, get more challenging)
3. After each answer, provide brief, constructive feedback that:
   - Clearly states if the answer is correct, partially correct, or incorrect
   - Explains what was good about the answer
   - Suggests improvements if needed
4. At the end (after minimum 3 questions), calculate rating based on performance:
   - Count how many answers were: fully correct, partially correct, incorrect
   - Calculate rating: (correct_answers * 2.5) + (partial_answers * 1.5) + (incorrect_answers * 0.5)
   - Example: 2 correct + 2 partial = (2*2.5) + (2*1.5) = 5 + 3 = 8.0/10 (PASS)
   - Example: 3 correct + 1 partial = (3*2.5) + (1*1.5) = 7.5 + 1.5 = 9.0/10 (PASS)
   - Example: 2 correct + 2 incorrect = (2*2.5) + (2*0.5) = 5 + 1 = 6.0/10 (FAIL)
   - Scale to 0-10 range, cap at 10
   - Pass = 7.0/10 or higher
5. Provide specific feedback on strengths and areas to improve

Format your responses as JSON:
- For questions: {{"type": "question", "question": "Your question here", "question_number": 1, "total_questions": 4}}
- For feedback: {{"type": "feedback", "feedback": "Your feedback here. Clearly state: CORRECT/PARTIALLY CORRECT/INCORRECT", "question_number": 1}}
- For completion (ONLY after EXACTLY 4 questions are asked and answered): {{"type": "complete", "overall_feedback": "Overall assessment with breakdown of correct/partial/incorrect answers", "rating": 8.5, "passed": true}}

Be encouraging but thorough. This is a learning opportunity. Rate FAIRLY based on actual performance - if answers are correct, give appropriate credit."""
        
        initial_prompt = f"""I'm ready to test my knowledge on: {todo_text}

Please start with the first question. Keep it focused and practical."""
        
        try:
            response = self._create_completion_with_fallback(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": initial_prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            content = response.choices[0].message.content.strip()
            
            # Try to parse JSON response
            try:
                import json
                # Remove markdown code blocks if present
                if content.startswith("```"):
                    content = content.split("```")[1]
                    if content.startswith("json"):
                        content = content[4:]
                parsed = json.loads(content)
                
                if parsed.get("type") == "question":
                    return {
                        "question": parsed.get("question", ""),
                        "question_number": parsed.get("question_number", 1),
                        "total_questions": parsed.get("total_questions", 4),
                        "is_complete": False
                    }
            except:
                pass
            
            # Fallback: treat as question
            return {
                "question": content,
                "question_number": 1,
                "total_questions": 4,
                "is_complete": False
            }
            
        except Exception as e:
            print(f"Error starting interview: {e}")
            raise Exception(f"Failed to start interview: {str(e)}")
    
    def continue_interview(self, todo_text: str, todo_id: str, context: Dict[str, Any], event_type: str, interview_history: List[Dict[str, str]], answer: str) -> Dict[str, Any]:
        """Continue an interview session with an answer."""
        if not self.client:
            raise Exception("OpenAI API client not available")
        
        # Build context
        context_text = f"Event type: {event_type}\n"
        context_text += f"User goal: {context.get('user_goal_text', '')}\n"
        if context.get('job_description'):
            context_text += f"Job description: {context.get('job_description')[:500]}\n"
        
        # Count how many questions have been asked so far
        # Questions are assistant messages that contain question marks and are not feedback
        question_count = 0
        for msg in interview_history:
            if msg.get("role") == "assistant":
                content = msg.get("content", "")
                # Count as question if it contains "?" and doesn't start with "Feedback:"
                if "?" in content and not content.strip().startswith("Feedback:"):
                    question_count += 1
        
        system_prompt = f"""You are an expert technical interviewer conducting a knowledge assessment. Your role is to test the candidate's understanding of: "{todo_text}"

Context about the interview preparation:
{context_text}

IMPORTANT RULES:
1. You MUST ask EXACTLY 4 questions before completing the interview. Currently {question_count} questions have been asked.
2. DO NOT complete the interview until all 4 questions have been asked AND answered.
3. Evaluate each answer FAIRLY and ACCURATELY:
   - If an answer is CORRECT or shows good understanding, acknowledge this positively
   - If an answer is PARTIALLY correct, note what's right and what needs improvement
   - If an answer is WRONG, explain why and what the correct answer should be
4. Rating should be FAIR and reflect actual performance:
   - CORRECT answers should contribute positively to the rating
   - PARTIALLY correct answers should get moderate scores
   - WRONG answers should lower the score appropriately
5. Only complete the interview after asking EXACTLY 4 questions and receiving answers to all of them

Your task:
1. Ask EXACTLY 4 focused questions that test practical knowledge and understanding
2. Questions should be progressive (start easier, get more challenging)
3. After each answer, provide brief, constructive feedback that:
   - Clearly states if the answer is correct, partially correct, or incorrect
   - Explains what was good about the answer
   - Suggests improvements if needed
4. At the end (after EXACTLY 4 questions are asked and answered), calculate rating based on performance:
   - Count how many answers were: fully correct, partially correct, incorrect
   - Calculate rating: (correct_answers * 2.5) + (partial_answers * 1.5) + (incorrect_answers * 0.5)
   - Example: 2 correct + 2 partial = (2*2.5) + (2*1.5) = 5 + 3 = 8.0/10 (PASS)
   - Example: 3 correct + 1 partial = (3*2.5) + (1*1.5) = 7.5 + 1.5 = 9.0/10 (PASS)
   - Example: 2 correct + 2 incorrect = (2*2.5) + (2*0.5) = 5 + 1 = 6.0/10 (FAIL)
   - Scale to 0-10 range, cap at 10
   - Pass = 7.0/10 or higher
5. Provide specific feedback on strengths and areas to improve

Format your responses as JSON:
- For questions: {{"type": "question", "question": "Your question here", "question_number": 2, "total_questions": 4}}
- For feedback: {{"type": "feedback", "feedback": "Your feedback here. Clearly state: CORRECT/PARTIALLY CORRECT/INCORRECT", "question_number": 1}}
- For completion (ONLY after EXACTLY 4 questions are asked and answered): {{"type": "complete", "overall_feedback": "Overall assessment with breakdown of correct/partial/incorrect answers", "rating": 8.5, "passed": true}}

Be encouraging but thorough. This is a learning opportunity. Rate FAIRLY based on actual performance - if answers are correct, give appropriate credit."""
        
        # Build conversation history
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(interview_history)
        messages.append({"role": "user", "content": answer})
        
        try:
            response = self._create_completion_with_fallback(
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            
            content = response.choices[0].message.content.strip()
            
            # Try to parse JSON response
            try:
                import json
                # Remove markdown code blocks if present
                if content.startswith("```"):
                    content = content.split("```")[1]
                    if content.startswith("json"):
                        content = content[4:]
                
                # Handle case where AI returns multiple JSON objects concatenated (e.g., {"type":"feedback"} {"type":"question"})
                # Find the first complete JSON object
                first_brace = content.find("{")
                parsed = None
                remaining_after_first = ""
                
                if first_brace >= 0:
                    # Find matching closing brace for first JSON
                    brace_count = 0
                    end_pos = first_brace
                    for i in range(first_brace, len(content)):
                        if content[i] == "{":
                            brace_count += 1
                        elif content[i] == "}":
                            brace_count -= 1
                            if brace_count == 0:
                                end_pos = i + 1
                                break
                    
                    first_json = content[first_brace:end_pos]
                    parsed = json.loads(first_json)
                    remaining_after_first = content[end_pos:].strip()
                else:
                    # No braces found, try parsing whole content
                    parsed = json.loads(content)
                
                if parsed.get("type") == "complete":
                    # Only allow completion if exactly 4 questions have been asked AND answered
                    # Count questions: assistant messages with "?" that are not feedback
                    question_count = 0
                    user_answer_count = 0
                    for msg in interview_history:
                        if msg.get("role") == "assistant":
                            content = msg.get("content", "")
                            if "?" in content and not content.strip().startswith("Feedback:"):
                                question_count += 1
                        elif msg.get("role") == "user":
                            user_answer_count += 1
                    
                    # Need exactly 4 questions asked AND 4 answers received
                    if question_count < 4 or user_answer_count < 4:  # Need exactly 4 Q&A pairs before completion
                        # Force another question instead
                        return {
                            "feedback": "Let me ask another question to complete the assessment.",
                            "question": f"Can you explain a different aspect of {todo_text}?",
                            "question_number": question_count + 1,
                            "total_questions": 4,
                            "is_complete": False
                        }
                    
                    return {
                        "is_complete": True,
                        "overall_feedback": parsed.get("overall_feedback", ""),
                        "rating": parsed.get("rating", 0),
                        "passed": parsed.get("passed", False)
                    }
                elif parsed.get("type") == "feedback":
                    # Check if there's another JSON object after this one (AI sometimes returns multiple JSON objects)
                    question_obj = None
                    
                    # Try to parse the next JSON object if it exists
                    if remaining_after_first.startswith("{"):
                        try:
                            # Find the second complete JSON object
                            second_brace = remaining_after_first.find("{")
                            if second_brace >= 0:
                                brace_count = 0
                                second_end = second_brace
                                for i in range(second_brace, len(remaining_after_first)):
                                    if remaining_after_first[i] == "{":
                                        brace_count += 1
                                    elif remaining_after_first[i] == "}":
                                        brace_count -= 1
                                        if brace_count == 0:
                                            second_end = i + 1
                                            break
                                second_json = remaining_after_first[second_brace:second_end]
                                question_obj = json.loads(second_json)
                        except (json.JSONDecodeError, ValueError):
                            pass
                    
                    # If we found a question object, use it
                    if question_obj and question_obj.get("type") == "question":
                        return {
                            "feedback": parsed.get("feedback", ""),
                            "question": question_obj.get("question", ""),
                            "question_number": question_obj.get("question_number", parsed.get("question_number", 1) + 1),
                            "total_questions": question_obj.get("total_questions", 4),
                            "is_complete": False
                        }
                    
                    # Otherwise, get next question from AI
                    next_response = self._create_completion_with_fallback(
                        messages=messages + [{"role": "assistant", "content": content}],
                        temperature=0.7,
                        max_tokens=300
                    )
                    next_content = next_response.choices[0].message.content.strip()
                    
                    # Try to parse the next response as JSON
                    try:
                        next_parsed = json.loads(next_content)
                        if next_parsed.get("type") == "question":
                            return {
                                "feedback": parsed.get("feedback", ""),
                                "question": next_parsed.get("question", ""),
                                "question_number": next_parsed.get("question_number", parsed.get("question_number", 1) + 1),
                                "total_questions": next_parsed.get("total_questions", 4),
                                "is_complete": False
                            }
                    except:
                        pass
                    
                    # Fallback: use the raw content as question
                    return {
                        "feedback": parsed.get("feedback", ""),
                        "question": next_content,
                        "question_number": parsed.get("question_number", 1) + 1,
                        "is_complete": False
                    }
                elif parsed.get("type") == "question":
                    return {
                        "question": parsed.get("question", ""),
                        "question_number": parsed.get("question_number", 1),
                        "total_questions": parsed.get("total_questions", 4),
                        "is_complete": False
                    }
            except:
                pass
            
            # Count actual questions asked (assistant messages with question marks, excluding feedback)
            question_count = 0
            for msg in interview_history:
                if msg.get("role") == "assistant":
                    content = msg.get("content", "")
                    # Count as question if it contains "?" and doesn't start with "Feedback:"
                    if "?" in content and not content.strip().startswith("Feedback:"):
                        question_count += 1
            
            # Check if this looks like final feedback (contains rating keywords)
            # BUT only allow completion if exactly 4 questions have been asked AND answered
            if any(keyword in content.lower() for keyword in ["rating", "overall", "passed", "score", "assessment", "final"]):
                # Count user answers too
                user_answer_count = sum(1 for msg in interview_history if msg.get("role") == "user")
                if question_count < 4 or user_answer_count < 4:  # Need exactly 4 Q&A pairs before completion
                    # Force another question
                    return {
                        "feedback": "Let me ask another question to complete the assessment.",
                        "question": f"Can you explain another aspect of {todo_text}?",
                        "question_number": question_count + 1,
                        "total_questions": 4,
                        "is_complete": False
                    }
                
                # Try to extract rating from AI response
                import re
                rating_match = re.search(r'(\d+\.?\d*)/10|rating[:\s]+(\d+\.?\d*)', content.lower())
                
                # Also analyze feedback history to calculate rating based on performance
                correct_count = 0
                partial_count = 0
                incorrect_count = 0
                
                # Analyze all feedback messages to count correct/incorrect answers
                # Look for feedback messages that come after user answers
                for i in range(len(interview_history) - 1, -1, -1):
                    msg = interview_history[i]
                    if msg.get("role") == "assistant":
                        feedback = msg.get("content", "").lower()
                        # Check if this is a feedback message (starts with "Feedback:" or contains feedback keywords)
                        if feedback.strip().startswith("feedback:") or ("feedback" in feedback and "?" not in feedback):
                            # Extract feedback text (remove "Feedback:" prefix if present)
                            feedback_text = feedback.split("feedback:", 1)[1].strip() if "feedback:" in feedback else feedback
                            
                            # More comprehensive keyword lists
                            positive_keywords = ["correct", "right", "good", "accurate", "well", "excellent", "perfect", "yes", "exactly", "that's correct", "you're right", "great answer", "that is correct", "you are right", "spot on", "precisely", "absolutely right"]
                            negative_keywords = ["incorrect", "wrong", "not quite", "misunderstanding", "needs improvement", "not correct", "not right", "unfortunately", "that's not", "that is not", "that's wrong", "that is wrong", "incorrectly", "mistaken"]
                            partial_keywords = ["partially", "mostly", "somewhat", "almost", "close", "partly", "partially correct", "mostly correct"]
                            
                            # Check in order: negative first (most specific), then positive, then partial
                            has_negative = any(keyword in feedback_text for keyword in negative_keywords)
                            has_positive = any(keyword in feedback_text for keyword in positive_keywords)
                            has_partial = any(keyword in feedback_text for keyword in partial_keywords)
                            
                            # If explicitly negative, mark as incorrect
                            if has_negative:
                                incorrect_count += 1
                            # If explicitly positive and not negative, mark as correct (unless partial)
                            elif has_positive and not has_negative:
                                if has_partial:
                                    partial_count += 1
                                else:
                                    correct_count += 1
                            # If only partial keywords, mark as partial
                            elif has_partial:
                                partial_count += 1
                            # Default: if feedback exists but no clear indicators, assume partial (conservative)
                            elif len(feedback_text) > 10:  # Only if there's substantial feedback
                                partial_count += 1
                
                # Calculate rating based on performance
                total_answers = correct_count + partial_count + incorrect_count
                if total_answers > 0:
                    # Formula: correct gets 2.5 points, partial gets 1.5, incorrect gets 0.5
                    # For 4 questions: max = 4*2.5 = 10.0
                    calculated_rating = (correct_count * 2.5) + (partial_count * 1.5) + (incorrect_count * 0.5)
                    # Scale to 0-10 range (already scaled since max is 10 for 4 questions)
                    calculated_rating = min(10.0, calculated_rating)
                    rating = calculated_rating
                elif rating_match:
                    # Use AI's rating if we can't calculate from feedback
                    rating = float(rating_match.group(1) or rating_match.group(2))
                else:
                    # Default to 7.0 if we can't determine (fair default)
                    rating = 7.0
                
                return {
                    "is_complete": True,
                    "overall_feedback": content,
                    "rating": rating,
                    "passed": rating >= 7.0
                }
            
            # Only complete if we've asked exactly 4 questions AND received 4 answers
            user_answer_count = sum(1 for msg in interview_history if msg.get("role") == "user")
            if question_count >= 4 and user_answer_count >= 4:  # Exactly 4 Q&A pairs done
                # We've asked enough questions, provide final assessment
                import re
                rating_match = re.search(r'(\d+\.?\d*)/10|rating[:\s]+(\d+\.?\d*)', content.lower())
                
                # Analyze feedback history to calculate rating based on performance
                correct_count = 0
                partial_count = 0
                incorrect_count = 0
                
                # Analyze all feedback messages to count correct/incorrect answers
                # Look for feedback messages that come after user answers
                for i in range(len(interview_history) - 1, -1, -1):
                    msg = interview_history[i]
                    if msg.get("role") == "assistant":
                        feedback = msg.get("content", "").lower()
                        # Check if this is a feedback message (starts with "Feedback:" or contains feedback keywords)
                        if feedback.strip().startswith("feedback:") or ("feedback" in feedback and "?" not in feedback):
                            # Extract feedback text (remove "Feedback:" prefix if present)
                            feedback_text = feedback.split("feedback:", 1)[1].strip() if "feedback:" in feedback else feedback
                            
                            # More comprehensive keyword lists
                            positive_keywords = ["correct", "right", "good", "accurate", "well", "excellent", "perfect", "yes", "exactly", "that's correct", "you're right", "great answer", "that is correct", "you are right", "spot on", "precisely", "absolutely right"]
                            negative_keywords = ["incorrect", "wrong", "not quite", "misunderstanding", "needs improvement", "not correct", "not right", "unfortunately", "that's not", "that is not", "that's wrong", "that is wrong", "incorrectly", "mistaken"]
                            partial_keywords = ["partially", "mostly", "somewhat", "almost", "close", "partly", "partially correct", "mostly correct"]
                            
                            # Check in order: negative first (most specific), then positive, then partial
                            has_negative = any(keyword in feedback_text for keyword in negative_keywords)
                            has_positive = any(keyword in feedback_text for keyword in positive_keywords)
                            has_partial = any(keyword in feedback_text for keyword in partial_keywords)
                            
                            # If explicitly negative, mark as incorrect
                            if has_negative:
                                incorrect_count += 1
                            # If explicitly positive and not negative, mark as correct (unless partial)
                            elif has_positive and not has_negative:
                                if has_partial:
                                    partial_count += 1
                                else:
                                    correct_count += 1
                            # If only partial keywords, mark as partial
                            elif has_partial:
                                partial_count += 1
                            # Default: if feedback exists but no clear indicators, assume partial (conservative)
                            elif len(feedback_text) > 10:  # Only if there's substantial feedback
                                partial_count += 1
                
                # Calculate rating based on performance
                total_answers = correct_count + partial_count + incorrect_count
                if total_answers > 0:
                    # Formula: correct gets 2.5 points, partial gets 1.5, incorrect gets 0.5
                    # For 4 questions: max = 4*2.5 = 10.0
                    calculated_rating = (correct_count * 2.5) + (partial_count * 1.5) + (incorrect_count * 0.5)
                    # Scale to 0-10 range (already scaled since max is 10)
                    calculated_rating = min(10.0, calculated_rating)
                    rating = calculated_rating
                elif rating_match:
                    # Use AI's rating if we can't calculate from feedback
                    rating = float(rating_match.group(1) or rating_match.group(2))
                else:
                    # Default to 7.0 if we can't determine (fair default)
                    rating = 7.0
                
                return {
                    "is_complete": True,
                    "overall_feedback": f"Based on your answers: {content}",
                    "rating": rating,
                    "passed": rating >= 7.0
                }
            
            # Fallback: treat as next question
            # Use question_count that was calculated earlier
            return {
                "question": content,
                "question_number": question_count + 1,
                "total_questions": 4,
                "is_complete": False
            }
            
        except Exception as e:
            print(f"Error continuing interview: {e}")
            raise Exception(f"Failed to continue interview: {str(e)}")
            
            # Check for quota/rate limit errors
            error_str = str(e).lower()
            error_code = getattr(e, 'code', None) or getattr(e, 'status_code', None)
            
            if (error_code == 429 or 
                "429" in str(e) or 
                "quota" in error_str or 
                "exceeded" in error_str or
                "insufficient_quota" in error_str or
                "rate_limit" in error_str):
                print("⚠️  Quota exceeded - using fallback checklist")
                # Still return fallback, but log the issue
                fallback = self._generate_fallback_checklist(event_type, user_goal_text)
                fallback.assumptions = [
                    "⚠️ Your OpenAI API quota has been exceeded. This is a basic fallback checklist.",
                    "Please check your billing at https://platform.openai.com/usage",
                    "Add payment method or wait for quota reset to get AI-generated checklists."
                ]
                return fallback
            
            # Return a fallback checklist for other errors
            return self._generate_fallback_checklist(event_type, user_goal_text)
    
    def _generate_fallback_checklist(self, event_type: str, user_goal_text: str) -> ChecklistStructure:
        """Generate a simple fallback checklist if AI fails."""
        from datetime import datetime
        import uuid
        
        base_items = [
            TodoItem(
                id=str(uuid.uuid4()),
                group_key="context",
                text="Review all available information about the event",
                status=TodoStatus.TODO,
                priority=Priority.HIGH
            ),
            TodoItem(
                id=str(uuid.uuid4()),
                group_key="skills",
                text="Identify key skills needed and assess current level",
                status=TodoStatus.TODO,
                priority=Priority.HIGH
            ),
            TodoItem(
                id=str(uuid.uuid4()),
                group_key="evidence",
                text="Prepare examples and evidence of relevant experience",
                status=TodoStatus.TODO,
                priority=Priority.MED
            ),
            TodoItem(
                id=str(uuid.uuid4()),
                group_key="delivery",
                text="Practice delivery and communication",
                status=TodoStatus.TODO,
                priority=Priority.MED
            ),
            TodoItem(
                id=str(uuid.uuid4()),
                group_key="logistics",
                text="Confirm time, location, and technical requirements",
                status=TodoStatus.TODO,
                priority=Priority.HIGH
            )
        ]
        
        return ChecklistStructure(
            title=user_goal_text[:50],
            event_type=event_type,
            assumptions=["Limited information available - please regenerate with more details"],
            groups=[
                ChecklistGroup(key="context", label="Context Understanding", items=[base_items[0]]),
                ChecklistGroup(key="skills", label="Skills / Knowledge Prep", items=[base_items[1]]),
                ChecklistGroup(key="evidence", label="Evidence & Examples", items=[base_items[2]]),
                ChecklistGroup(key="delivery", label="Delivery & Execution", items=[base_items[3]]),
                ChecklistGroup(key="logistics", label="Logistics & Risk", items=[base_items[4]])
            ],
            next_3_actions=[
                "Review all available information",
                "Identify key skills needed",
                "Confirm logistics"
            ]
        )
