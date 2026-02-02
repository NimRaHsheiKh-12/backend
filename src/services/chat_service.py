"""
Core chatbot logic for TaskBox Chatbot Assistant (Taskie)
"""
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

from ..models.todo import Todo
from ..models.chat_session import ChatSession
from ..models.chat_history import ChatHistory
from ..database.database import get_db_session
from sqlmodel import select, Session
from ..utils.message_parser import MessageParser
from ..utils.task_enums import TaskAction
from ..utils.emoji_utils import get_random_positive_emoji
from ..utils.taskie_responses import format_task_response
from .todo_service import TodoService
from ..schemas.todo import TodoCreate, TodoUpdate
from uuid import UUID


class ChatService:
    def __init__(self):
        self.parser = MessageParser()
    async def process_message(self, db: Session = None, user_id: str = "", message: str = "", current_tasks: List[Dict] = None) -> Dict[str, Any]:
        """
        Process a user's message and return a result dict with the expected
        keys for the API endpoints: `reply`, `action_performed`,
        `updated_tasks`, and `success`.

        This function accepts an optional `db` session. If none is provided,
        it will open one internally. It also accepts `current_tasks` to avoid
        hitting the DB when callers already have the tasks loaded.
        """

        # Normalize inputs
        if current_tasks is None:
            current_tasks = []

        # Helper to convert Todo objects to dicts
        def todos_to_dicts(todos):
            out = []
            for t in todos:
                out.append({
                    "id": str(t.id),
                    "user_id": str(t.user_id),
                    "title": t.title,
                    "description": t.description or "",
                    "is_completed": t.is_completed,
                    "priority": t.priority or "Medium",
                    "category": t.category or "Personal",
                    "due_date": t.due_date.isoformat() if t.due_date else None,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                    "updated_at": t.updated_at.isoformat() if t.updated_at else None
                })
            return out

        async def _process_with_db(db_session: Session):
            # Parse and validate user UUID
            try:
                user_uuid = UUID(user_id)
            except Exception:
                # If user_id is not a valid UUID, try to proceed but return safe fallback
                user_uuid = None

            # If current_tasks not provided, load from DB when possible
            if not current_tasks and user_uuid is not None:
                try:
                    fetched = TodoService.get_todos_by_user(db_session, user_uuid)
                    tasks_for_processing = todos_to_dicts(fetched)
                except Exception:
                    tasks_for_processing = []
            else:
                tasks_for_processing = current_tasks

            # Parse the message to determine the intent
            intent = self.parser.parse_intent(message, tasks_for_processing)

            # Determine confidence
            confidence_threshold = 0.5
            if hasattr(intent, 'confidence'):
                confidence = intent.confidence
            else:
                confidence = 1.0

            # If ambiguous or NONE, provide fallback/guidance/greeting
            if intent is None or getattr(intent, 'action', TaskAction.NONE) == TaskAction.NONE or confidence < confidence_threshold:
                if self._is_greeting(message) and user_uuid is not None:
                    reply = await self._handle_greeting(db_session, user_uuid)
                    action = TaskAction.NONE.value
                    updated = tasks_for_processing
                    success = True
                else:
                    # Try common questions first
                    common = self._answer_common_questions(message, tasks_for_processing)
                    if common is not None:
                        return common
                    # If the parser was ambiguous but the user's message clearly
                    # requests to view tasks (e.g. "show my tasks"), handle it
                    # with a simple keyword-based fallback to improve reliability.
                    message_lower = message.lower() if isinstance(message, str) else ''
                    if any(k in message_lower for k in ("show", "list", "view", "see")) and "task" in message_lower:
                        # Handle READ request even if user_uuid is None
                        if user_uuid is not None:
                            reply = await self._handle_read_tasks(db_session, user_uuid, intent)
                        else:
                            # Fallback when user context not available
                            reply = f"You don't have any tasks on your list right now! Would you like to add one? 😊"
                        return {
                            "reply": reply,
                            "action_performed": TaskAction.READ.value,
                            "updated_tasks": tasks_for_processing,
                            "success": True
                        }

                    # Guidance requests
                    if self._is_guidance_request(message):
                        return await self._provide_guidance(tasks_for_processing)

                    # General fallback
                    fallback = await self._handle_fallback_response(user_id, message, tasks_for_processing)
                    return fallback
            else:
                # CRUD operations
                action = intent.action.value if hasattr(intent, 'action') else TaskAction.NONE.value

                if intent.action == TaskAction.CREATE:
                    reply = await self._handle_create_task(db_session, user_uuid, message, intent)
                elif intent.action == TaskAction.READ:
                    reply = await self._handle_read_tasks(db_session, user_uuid, intent)
                elif intent.action == TaskAction.COMPLETE:
                    reply = await self._handle_complete_task(db_session, user_uuid, message, intent)
                elif intent.action == TaskAction.UPDATE:
                    reply = await self._handle_update_task(db_session, user_uuid, message, intent)
                elif intent.action == TaskAction.DELETE:
                    reply = await self._handle_delete_task(db_session, user_uuid, message, intent)
                else:
                    reply = await self._handle_general_request(message)

                # After doing a CRUD action, fetch updated tasks when possible
                if user_uuid is not None:
                    try:
                        fetched_after = TodoService.get_todos_by_user(db_session, user_uuid)
                        updated = todos_to_dicts(fetched_after)
                    except Exception:
                        updated = tasks_for_processing
                else:
                    updated = tasks_for_processing

                success = True

            return {
                "reply": reply if isinstance(reply, str) else str(reply),
                "action_performed": action,
                "updated_tasks": updated,
                "success": success
            }

        # If caller provided a db session, use it; otherwise open one
        if db is not None:
            return await _process_with_db(db)
        else:
            from ..database.database import get_db_session as _get_db_session
            with _get_db_session() as db_session:
                return await _process_with_db(db_session)

    async def _handle_create_task(self, db: Session, user_uuid: UUID, message: str, intent) -> str:
        """
        Handle requests to create a new task
        """
        print(f"DEBUG: _handle_create_task called with user_uuid: {user_uuid}, message: {message}")

        # Check if user_uuid is valid
        if user_uuid is None:
            return "I'm sorry, I can't create tasks without a valid user account. Please try logging in again. 😊"

        # Extract task details from the message
        task_title = self.parser.extract_task_title(message)

        if not task_title:
            print("DEBUG: No task title extracted, returning error response")
            return f"I couldn't understand the task you want to add. Could you please rephrase that? {get_random_positive_emoji()}"

        # Create the task using TodoService
        todo_data = TodoCreate(
            title=task_title,
            description="",
            is_completed=False,
            priority="Medium",
            category="Personal",
            due_date=None
        )
        TodoService.create_todo(db, todo_data, user_uuid)

        # Create a friendly response
        reply = f"Great! I've added '{task_title}' to your task list. You've got this! {get_random_positive_emoji()}"

        print(f"DEBUG: Create task completed")
        return reply

    async def _handle_read_tasks(self, db: Session, user_uuid: UUID, intent) -> str:
        """
        Handle requests to view current tasks
        """
        print(f"DEBUG: _handle_read_tasks called")

        # Check if user_uuid is valid
        if user_uuid is None:
            return "I'm sorry, I can't access tasks without a valid user account. Please try logging in again. 😊"

        # Get tasks from DB
        tasks = TodoService.get_todos_by_user(db, user_uuid)

        if not tasks:
            reply = "You don't have any tasks on your list right now! Would you like to add one? 😊"
            print("DEBUG: No tasks found")
            return reply

        # Convert to dict format for formatting
        task_dicts = []
        for task in tasks:
            task_dicts.append({
                "id": str(task.id),
                "title": task.title,
                "is_completed": task.is_completed
            })

        # Format the task list response
        reply = format_task_response(task_dicts)
        print(f"DEBUG: Read tasks completed, returning response for {len(tasks)} tasks")

        return reply

    async def _handle_complete_task(self, db: Session, user_uuid: UUID, message: str, intent) -> str:
        """
        Handle requests to mark a task as completed
        """
        print(f"DEBUG: _handle_complete_task called with user_uuid: {user_uuid}, message: {message}")

        # Check if user_uuid is valid
        if user_uuid is None:
            return "I'm sorry, I can't update tasks without a valid user account. Please try logging in again. 😊"

        # Get tasks from DB
        tasks = TodoService.get_todos_by_user(db, user_uuid)

        # Find the task to complete by title
        task_to_complete = None
        for task in tasks:
            if task.title.lower() in message.lower():
                task_to_complete = task
                break

        if not task_to_complete:
            print("DEBUG: Task not found")
            # Get current tasks for the error message
            task_dicts = [{"title": t.title, "is_completed": t.is_completed} for t in tasks]
            reply = f"I couldn't find that task in your list. Here are your current tasks: {format_task_response(task_dicts)}"
            return reply

        # Update the task as completed
        update_data = TodoUpdate(is_completed=True)
        TodoService.update_todo(db, task_to_complete.id, update_data, user_uuid)

        reply = f"Awesome job! I've marked '{task_to_complete.title}' as completed. Way to go! 🎉"
        print(f"DEBUG: Complete task completed")

        return reply

    async def _handle_update_task(self, db: Session, user_uuid: UUID, message: str, intent) -> str:
        """
        Handle requests to update/edit a task
        """
        print(f"DEBUG: _handle_update_task called with user_uuid: {user_uuid}, message: {message}")

        # Check if user_uuid is valid
        if user_uuid is None:
            return "I'm sorry, I can't update tasks without a valid user account. Please try logging in again. 😊"

        # Get tasks from DB
        tasks = TodoService.get_todos_by_user(db, user_uuid)

        # Find the task to update by title (simple match)
        task_to_update = None
        for task in tasks:
            if task.title.lower() in message.lower():
                task_to_update = task
                break

        # Extract new title (simple extraction)
        new_title = None
        words = message.lower().split()
        if "to" in words:
            to_index = words.index("to")
            if to_index + 1 < len(words):
                new_title = " ".join(words[to_index + 1:])

        if not task_to_update or not new_title:
            print("DEBUG: Task or new title not found")
            reply = f"I couldn't understand which task to update or what the new details should be. Could you please clarify? {get_random_positive_emoji()}"
            return reply

        # Update the task
        update_data = TodoUpdate(title=new_title)
        TodoService.update_todo(db, task_to_update.id, update_data, user_uuid)

        reply = f"Got it! I've updated '{task_to_update.title}' to '{new_title}'. Looking good! ✨"
        print(f"DEBUG: Update task completed")

        return reply

    async def _handle_delete_task(self, db: Session, user_uuid: UUID, message: str, intent) -> str:
        """
        Handle requests to delete a task
        """
        print(f"DEBUG: _handle_delete_task called with user_uuid: {user_uuid}, message: {message}")

        # Check if user_uuid is valid
        if user_uuid is None:
            return "I'm sorry, I can't delete tasks without a valid user account. Please try logging in again. 😊"

        # Get tasks from DB
        tasks = TodoService.get_todos_by_user(db, user_uuid)

        # Find the task to delete by title
        task_to_delete = None
        for task in tasks:
            if task.title.lower() in message.lower():
                task_to_delete = task
                break

        if not task_to_delete:
            print("DEBUG: Task not found")
            # Get current tasks for the error message
            task_dicts = [{"title": t.title, "is_completed": t.is_completed} for t in tasks]
            reply = f"I couldn't find that task in your list. Here are your current tasks: {format_task_response(task_dicts)}"
            return reply

        # Delete the task
        TodoService.delete_todo(db, task_to_delete.id, user_uuid)

        reply = f"Done! I've removed '{task_to_delete.title}' from your task list. {get_random_positive_emoji()}"
        print(f"DEBUG: Delete task completed")

        return reply

    async def _handle_general_request(self, message: str) -> str:
        """
        Handle general requests that don't map to specific task actions
        """
        print(f"DEBUG: _handle_general_request called with message: {message}")

        # For other general requests, provide a default response with Taskie's personality
        reply = f"Hey there! I'm Taskie, your friendly task assistant! 😊 I can help you add, view, update, complete, or delete tasks. Just tell me what you'd like to do!"

        print(f"DEBUG: Returning general request response: {reply}")
        return reply

    def _is_greeting(self, message: str) -> bool:
        """
        Check if the message is a greeting
        """
        message_lower = message.lower().strip()
        greetings = [
            "hi", "hello", "hey", "greetings", "good morning", "good afternoon",
            "good evening", "good day", "howdy", "hi there", "hello there"
        ]

        return message_lower in greetings or any(greeting in message_lower for greeting in greetings)

    async def _handle_greeting(self, db: Session, user_uuid: Optional[UUID] = None) -> str:
        """
        Handle greeting messages
        """
        if user_uuid is None:
            reply = "Hello! 👋 I'm Taskie, your friendly task assistant! How can I help you with your tasks today?"
        else:
            tasks = TodoService.get_todos_by_user(db, user_uuid)
            if not tasks:
                reply = f"Hello there! 👋 I'm Taskie, your friendly task assistant! It looks like you don't have any tasks on your list yet. Would you like to add a new task? 😊"
            else:
                completed_count = sum(1 for task in tasks if task.is_completed)
                total_count = len(tasks)
                reply = f"Hello! 👋 I'm Taskie, your friendly task assistant! You currently have {total_count} tasks, with {completed_count} completed. How can I help you today? 😊"

        return reply

    async def _handle_fallback_response(self, user_id: str, message: str, current_tasks: List[Dict]) -> Dict[str, Any]:
        """
        Handle ambiguous requests with fallback responses
        """

        fallback_responses = [
            f"I'm not quite sure what you mean by '{message[:30]}...'. Could you rephrase that? I can help with adding, viewing, updating, completing, or deleting tasks! 😊",
            f"Sorry, I didn't quite understand that. You can ask me to add, view, update, complete, or delete tasks. What would you like to do? 🤔",
            f"Hmm, I'm having trouble understanding your request. Try telling me something like 'Add buy groceries' or 'Show my tasks'. I'm here to help! 💪"
        ]

        import random
        reply = random.choice(fallback_responses)

        return {
            "reply": reply,
            "action_performed": TaskAction.NONE.value,
            "updated_tasks": current_tasks,
            "success": True
        }

    def _is_guidance_request(self, message: str) -> bool:
        """
        Check if the message is requesting guidance or suggestions
        """
        message_lower = message.lower()
        guidance_indicators = [
            "suggest", "recommend", "advice", "tips", "help me organize",
            "how should", "what should", "guide", "guidance", "productivity",
            "better way", "improve", "assist", "motivate", "encourage"
        ]

        return any(indicator in message_lower for indicator in guidance_indicators)

    async def _provide_guidance(self, current_tasks: List[Dict]) -> Dict[str, Any]:
        """
        Provide guidance and suggestions to the user
        """
        # Generate guidance based on current tasks
        if not current_tasks:
            guidance = (
                "It looks like you don't have any tasks on your list right now! "
                "That's a great opportunity to start fresh. 🌟 "
                "Consider adding tasks that align with your goals for today. "
                "Remember, even small steps lead to big achievements! 💪 "
                "What would you like to accomplish today? 😊"
            )
        else:
            # Count completed vs incomplete tasks
            completed_count = sum(1 for task in current_tasks if task.get('is_completed', False))
            total_count = len(current_tasks)

            if completed_count == total_count:
                guidance = (
                    f"Congratulations! You've completed all {total_count} of your tasks! 🎉 "
                    "Take a moment to celebrate your accomplishments. "
                    "What new goals would you like to set for yourself? 🌟"
                )
            elif completed_count == 0:
                guidance = (
                    "I see you have several tasks to tackle! Here's a tip: "
                    "Start with the most important or urgent one to build momentum. "
                    "Breaking larger tasks into smaller steps can make them feel more manageable. "
                    "You've got this! 💪 "
                    f"You currently have {total_count} tasks on your list. "
                    "Which one feels most important to start with? 😊"
                )
            else:
                remaining_count = total_count - completed_count
                guidance = (
                    f"Great progress! You've completed {completed_count} out of {total_count} tasks. "
                    f"That means you have {remaining_count} tasks left to conquer! 🌟 "
                    "Keep up the excellent work. Remember to take breaks when needed "
                    "and celebrate each completed task along the way. 🎉 "
                    "What would you like to focus on next? 💪"
                )

        return {
            "reply": guidance,
            "action_performed": TaskAction.NONE.value,
            "updated_tasks": current_tasks,
            "success": True
        }

    def _answer_common_questions(self, message: str, current_tasks: List[Dict]) -> Dict[str, Any]:
        """
        Answer common questions that users might ask
        """
        message_lower = message.lower().strip()

        # How are you / How do you do
        if any(phrase in message_lower for phrase in ["how are you", "how do you do", "how's it going", "how are things"]):
            return {
                "reply": "I'm doing great, thank you for asking! 😊 I'm here and ready to help you manage your tasks. How can I assist you today?",
                "action_performed": TaskAction.NONE.value,
                "updated_tasks": current_tasks,
                "success": True
            }

        # What can you do / Help
        if any(phrase in message_lower for phrase in ["what can you do", "help", "what do you do", "commands", "features"]):
            reply = (
                "I'm Taskie, your friendly task assistant! I can help you with:\n"
                "• Add new tasks (e.g., 'Add buy groceries')\n"
                "• View your tasks (e.g., 'Show my tasks')\n"
                "• Update tasks (e.g., 'Change buy groceries to buy groceries and milk')\n"
                "• Complete tasks (e.g., 'Complete buy groceries')\n"
                "• Delete tasks (e.g., 'Delete buy groceries')\n"
                "Just tell me what you'd like to do! 😊"
            )
            return {
                "reply": reply,
                "action_performed": TaskAction.NONE.value,
                "updated_tasks": current_tasks,
                "success": True
            }

        # Who are you / What is your name
        if any(phrase in message_lower for phrase in ["who are you", "what is your name", "what's your name", "introduce yourself"]):
            return {
                "reply": "I'm Taskie, your friendly task management assistant! 🤖 I help you organize and track your tasks. Nice to meet you! 😊",
                "action_performed": TaskAction.NONE.value,
                "updated_tasks": current_tasks,
                "success": True
            }

        # Thank you
        if any(phrase in message_lower for phrase in ["thank you", "thanks", "thank you very much", "thanks a lot"]):
            return {
                "reply": "You're very welcome! 😊 I'm always here to help. Is there anything else I can do for you?",
                "action_performed": TaskAction.NONE.value,
                "updated_tasks": current_tasks,
                "success": True
            }

        # Status questions
        if any(phrase in message_lower for phrase in ["status", "progress", "how am i doing", "how's my progress"]):
            if not current_tasks:
                reply = "You don't have any tasks yet, so you're doing great by staying organized! 🌟 Would you like to add your first task?"
            else:
                completed_count = sum(1 for task in current_tasks if task.get('is_completed', False))
                total_count = len(current_tasks)
                if completed_count == total_count:
                    reply = f"Excellent progress! You've completed all {total_count} of your tasks! 🎉 Keep up the great work!"
                else:
                    reply = f"You're doing great! You've completed {completed_count} out of {total_count} tasks. Keep it up! 💪"
            return {
                "reply": reply,
                "action_performed": TaskAction.NONE.value,
                "updated_tasks": current_tasks,
                "success": True
            }

        # No matching question found
        return None

    def _is_greeting(self, message: str) -> bool:
        """
        Check if the message is a greeting
        """
        message_lower = message.lower().strip()
        return message_lower in ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening', 'hi there', 'hello there']