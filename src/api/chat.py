"""
API endpoints for the TaskBox Chatbot Assistant (Taskie)
"""
from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List, Optional, Optional
import uuid
from datetime import datetime

from ..models.todo import Todo
from ..schemas.todo import TodoCreate, TodoUpdate, TodoResponse
from ..schemas.chat import ChatMessageRequest, ChatMessageResponse
from ..services.chat_service import ChatService
from ..utils.message_parser import MessageParser
from ..auth.auth_bearer import JWTBearer

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/")
async def chat_endpoint(
    request_body: ChatMessageRequest = Body(...),
    token: str = Depends(JWTBearer())
):
    """
    Simple chat endpoint that matches the frontend expectation.
    CRITICAL: Extract user_id ONLY from JWT token.
    Extract message ONLY from request body.
    """
    # Extract user info from the token
    from jose import jwt
    from ..config import settings
    from ..database.database import get_db_session
    from ..models.todo import Todo
    from ..services.todo_service import TodoService
    from sqlmodel import select
    from uuid import UUID

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Could not validate credentials - no user ID in token")

        # Validate that user_id is a proper UUID string
        try:
            user_uuid = UUID(user_id)
        except ValueError:
            print(f"DEBUG: Invalid UUID format for user_id: {user_id}")
            raise HTTPException(status_code=401, detail="Invalid user ID format in token")

    except jwt.JWTError as e:
        print(f"DEBUG: JWT Error occurred: {str(e)}")
        raise HTTPException(status_code=401, detail="Could not validate credentials")

    # Log the user_id for debugging
    print(f"DEBUG: chat_endpoint - user_id from token: {user_id}")

    # Extract message from request body (NOT from user_id or anywhere else)
    message = request_body.message
    print(f"\n" + "="*70)
    print(f"DEBUG [/chat endpoint] - RECEIVED REQUEST")
    print(f"  user_id from token: '{user_id}'")
    print(f"  message from body: '{message}'")
    print(f"  message type: {type(message)}")
    print(f"="*70)

    if not message:
        raise HTTPException(status_code=400, detail="Message is required")

    # Initialize services
    chat_service = ChatService()

    try:
        with get_db_session() as db:
            # Process the message and get response
            result = await chat_service.process_message(
                db=db,
                user_id=user_id,
                message=message
            )

        # Return the full response with all required fields
        return {
            "reply": result.get("reply", ""),
            "action_performed": result.get("action_performed", "NONE"),
            "updated_tasks": result.get("updated_tasks", []),
            "success": result.get("success", True)
        }
    except Exception as e:
        # Log the actual error for debugging
        import traceback
        print(f"Error in chat endpoint: {str(e)}")
        print(traceback.format_exc())

        # Return a safe fallback response with all required fields
        return {
            "reply": "I'm sorry, I encountered an issue processing your request. Could you try again? 😊",
            "action_performed": "NONE",
            "updated_tasks": [],
            "success": False
        }



@router.post("/process")
async def process_chat_message(
    request_body: ChatMessageRequest = Body(...),
    token: Optional[str] = Depends(JWTBearer())
):
    """
    Process a user's chat message and perform appropriate action on their tasks.
    Frontend sends { message: "..." } - user_id is extracted from JWT token if authenticated.
    """
    import logging
    from jose import jwt
    from ..config import settings
    from ..database.database import get_db_session
    from ..models.todo import Todo
    from ..services.todo_service import TodoService
    from sqlmodel import select
    from uuid import UUID

    user_id = None
    user_uuid = None

    if token:
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm]
            )
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(status_code=401, detail="Could not validate credentials - no user ID in token")

            # Validate that user_id is a proper UUID string
            try:
                user_uuid = UUID(user_id)
            except ValueError:
                print(f"DEBUG: Invalid UUID format for user_id: {user_id}")
                raise HTTPException(status_code=401, detail="Invalid user ID format in token")
        except jwt.JWTError as e:
            print(f"DEBUG: JWT Error occurred: {str(e)}")
            raise HTTPException(status_code=401, detail="Could not validate credentials")
    else:
        user_id = request_body.user_id or ""

    # Extract message - this is required
    message = request_body.message
    
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")

    logging.info(f"Processing {'authenticated' if token else 'public'} chat message for user_id: {user_id}, message: {message}")
    chat_service = ChatService()

    try:
        if token:
            # Load user's tasks from the database
            with get_db_session() as db:
                statement = select(Todo).where(Todo.user_id == user_uuid)
                result = db.execute(statement)
                db_tasks = result.scalars().all()

                # Access and serialize attributes INSIDE the session context
                current_tasks = []
                for task in db_tasks:
                    current_tasks.append({
                        "id": str(task.id),
                        "user_id": str(task.user_id),
                        "title": task.title,
                        "description": task.description or "",
                        "is_completed": task.is_completed,
                        "priority": task.priority or "Medium",
                        "category": task.category or "Personal",
                        "due_date": task.due_date.isoformat() if task.due_date else None,
                        "created_at": task.created_at.isoformat() if task.created_at else None,
                        "updated_at": task.updated_at.isoformat() if task.updated_at else None
                    })
        else:
            # `request_body` is a Pydantic model; `current_tasks` may be None
            # (we changed the default to None). Ensure we always pass a list.
            current_tasks = request_body.current_tasks or []

        # Process the message and get response
        result = await chat_service.process_message(
            user_id=user_id,
            message=message,
            current_tasks=current_tasks
        )

        # If the action was successful and involved a change, save back to DB
        # NOTE: The chat_service already handles creating, updating, and deleting tasks.
        # We only need to sync deletions here to remove tasks that were deleted by the service
        # but might still be in the UI. CREATE and UPDATE are already handled by the service.
        if result and result.get("success", False) and result.get("action_performed") in ["DELETE", "COMPLETE"] and token:
            with get_db_session() as db:
                # Only handle deletions - don't recreate tasks that the service already created
                updated_tasks = result.get("updated_tasks", [])
                original_task_ids = {task['id'] for task in current_tasks}
                updated_task_ids = {task['id'] for task in updated_tasks}
                deleted_task_ids = original_task_ids - updated_task_ids

                for deleted_id in deleted_task_ids:
                    deleted_uuid = UUID(deleted_id)
                    TodoService.delete_todo(db, deleted_uuid, user_uuid)

        # Ensure result is valid before returning
        if result is None:
            result = {
                "reply": "I'm sorry, I encountered an issue processing your request. Could you try again? 😊",
                "action_performed": "NONE",
                "updated_tasks": current_tasks,
                "success": False
            }
        else:
            if "reply" not in result:
                result["reply"] = "I'm Taskie, your friendly task assistant! How can I help you?"
            if "action_performed" not in result:
                result["action_performed"] = "NONE"
            if "updated_tasks" not in result:
                result["updated_tasks"] = current_tasks
            if "success" not in result:
                result["success"] = True

        logging.info(f"Successfully processed chat message for user_id: {user_id}")
        return result
    except Exception as e:
        logging.error(f"Error processing chat message for user_id {user_id}: {str(e)}")
        logging.error(f"Full traceback: {__import__('traceback').format_exc()}")
        return {
            "reply": "I'm sorry, I encountered an issue processing your request. Could you try again? 😊",
            "action_performed": "NONE",
            "updated_tasks": current_tasks,
            "success": False
        }

@router.post("/process_public")
async def process_chat_message_public(
    request_body: ChatMessageRequest = Body(...)
):
    """
    Public process endpoint that doesn't require authentication.
    Frontend sends ONLY { message: "..." } - user_id and current_tasks are optional.
    """
    import logging
    from ..database.database import get_db
    from ..models.todo import Todo
    from ..services.todo_service import TodoService
    from ..services.user_service import UserService
    from ..schemas.user import UserRegistrationRequest
    from sqlmodel import select
    from uuid import UUID

    # Extract message - this is required
    message = request_body.message
    user_id = request_body.user_id or "anonymous"  # Default to anonymous if not provided
    
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")

    # Log incoming request for debugging
    logging.info(f"Processing public chat message for user_id: {user_id}, message: {message}")

    # Initialize services
    chat_service = ChatService()

    try:
        # Handle user identification - create anonymous user if needed
        from ..database.database import get_db_session

        user_uuid = None
        # Try to parse as UUID and verify existence
        try:
            if user_id != "anonymous" and user_id is not None:
                user_uuid = UUID(user_id)
                with get_db_session() as db:
                    user = UserService.get_user_by_id(db, user_uuid)
                    if not user:
                        user_uuid = None
        except Exception:
            user_uuid = None

        # If no valid user found, create an anonymous user
        if user_uuid is None:
            anonymous_email = f"anonymous_{user_id}@temp.local"
            try:
                with get_db_session() as db:
                    anonymous_user_data = UserRegistrationRequest(
                        email=anonymous_email,
                        password="anonymous_temp_password"
                    )
                    anonymous_user = UserService.create_user(db, anonymous_user_data)
                    user_uuid = anonymous_user.id
            except Exception:
                try:
                    with get_db_session() as db:
                        existing_user = UserService.get_user_by_email(db, anonymous_email)
                        if existing_user:
                            user_uuid = existing_user.id
                        else:
                            import uuid as _uuid
                            user_uuid = _uuid.uuid4()
                except Exception:
                    import uuid as _uuid
                    user_uuid = _uuid.uuid4()

        # Load user's tasks
        try:
            with get_db_session() as db:
                statement = select(Todo).where(Todo.user_id == user_uuid)
                result = db.execute(statement)
                db_tasks = result.scalars().all()

            current_tasks = []
            for task in db_tasks:
                current_tasks.append({
                    "id": str(task.id),
                    "user_id": str(task.user_id),
                    "title": task.title,
                    "description": task.description or "",
                    "is_completed": task.is_completed,
                    "priority": task.priority or "Medium",
                    "category": task.category or "Personal",
                    "due_date": task.due_date.isoformat() if task.due_date else None,
                    "created_at": task.created_at.isoformat() if task.created_at else None,
                    "updated_at": task.updated_at.isoformat() if task.updated_at else None
                })
        except Exception as e:
            logging.error(f"Error loading tasks for user {user_uuid}: {str(e)}")
            current_tasks = []

        # Process the message and get response
        result = await chat_service.process_message(
            user_id=str(user_uuid),
            message=message,
            current_tasks=current_tasks
        )

        # If the action was successful and involved a change, save back to DB
        if result and result.get("success", False) and result.get("action_performed") != "NONE":
            try:
                with get_db_session() as db:
                    updated_tasks = result.get("updated_tasks", [])

                    original_task_ids = {task['id'] for task in current_tasks}
                    updated_task_ids = {task['id'] for task in updated_tasks}
                    deleted_task_ids = original_task_ids - updated_task_ids

                    for task_data in updated_tasks:
                        task_id_str = task_data['id']
                        if task_id_str not in original_task_ids:
                            from ..schemas.todo import TodoCreate
                            new_task_data = TodoCreate(
                                title=task_data['title'],
                                description=task_data.get('description', ''),
                                is_completed=task_data.get('is_completed', False),
                                priority=task_data.get('priority', 'Medium'),
                                category=task_data.get('category', 'Personal'),
                                due_date=task_data.get('due_date')
                            )
                            TodoService.create_todo(db, new_task_data, user_uuid)
                        else:
                            from ..schemas.todo import TodoUpdate
                            update_data = TodoUpdate(
                                title=task_data['title'],
                                description=task_data.get('description', ''),
                                is_completed=task_data.get('is_completed', False),
                                priority=task_data.get('priority', 'Medium'),
                                category=task_data.get('category', 'Personal'),
                                due_date=task_data.get('due_date')
                            )
                            task_uuid = UUID(task_id_str)
                            TodoService.update_todo(db, task_uuid, update_data, user_uuid)

                    for deleted_id in deleted_task_ids:
                        deleted_uuid = UUID(deleted_id)
                        TodoService.delete_todo(db, deleted_uuid, user_uuid)
            except Exception as e:
                logging.error(f"Error saving updated tasks to database: {str(e)}")

        # Ensure result is valid before returning
        if result is None:
            result = {
                "reply": "I'm sorry, I encountered an issue processing your request. Could you try again? 😊",
                "action_performed": "NONE",
                "updated_tasks": current_tasks,
                "success": False
            }
        else:
            if "reply" not in result:
                result["reply"] = "I'm Taskie, your friendly task assistant! How can I help you?"
            if "action_performed" not in result:
                result["action_performed"] = "NONE"
            if "updated_tasks" not in result:
                result["updated_tasks"] = current_tasks
            if "success" not in result:
                result["success"] = True

        logging.info(f"Successfully processed public chat message for user_id: {user_id}")
        return result
    except Exception as e:
        logging.error(f"Error processing public chat message for user_id {user_id}: {str(e)}")
        logging.error(f"Full traceback: {__import__('traceback').format_exc()}")
        return {
            "reply": "I'm sorry, I encountered an issue processing your request. Could you try again? 😊",
            "action_performed": "NONE",
            "updated_tasks": [],
            "success": False
        }

@router.get("/history/{user_id}")
async def get_chat_history(
    user_id: str,
    token: str = Depends(JWTBearer())
):
    """
    Retrieve the chat history for a specific user
    """
    from jose import jwt
    from ..config import settings
    from ..database.database import get_db_session
    from ..models.chat_history import ChatHistory
    from sqlmodel import select

    # Verify that the authenticated user is accessing their own history
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        authenticated_user_id = payload.get("sub")
    except jwt.JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token"
        )

    # Ensure users can only access their own chat history
    if authenticated_user_id != user_id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to access this chat history"
        )

    with get_db_session() as session:
        # Query the database for chat history records for this user
        statement = select(ChatHistory).where(ChatHistory.user_id == user_id)
        results = session.exec(statement)
        history_records = results.all()

        # Convert to dictionary format
        history_list = []
        for record in history_records:
            history_list.append({
                "id": str(record.id),
                "user_message": record.user_message,
                "chatbot_reply": record.chatbot_reply,
                "timestamp": record.timestamp.isoformat(),
                "associated_task_id": str(record.associated_task_id) if record.associated_task_id else None,
                "session_id": str(record.session_id) if record.session_id else None
            })

        return {
            "history": history_list,
            "success": True
        }

@router.post("/session")
async def initialize_chat_session(
    request: dict,
    token: str = Depends(JWTBearer())
):
    """
    Initialize a new chat session for a user
    """
    from ..database.database import get_db_session
    from ..models.chat_session import ChatSession
    from sqlmodel import select
    from jose import jwt
    from ..config import settings

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        user_id = payload.get("sub")
    except jwt.JWTError:
        user_id = None

    # Override with user_id from request if provided
    request_user_id = request.get("user_id")
    if request_user_id:
        user_id = request_user_id

    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")

    with get_db_session() as session:
        # Create a new chat session
        new_session = ChatSession(
            user_id=user_id,
            context_data={}  # Initialize with empty context
        )

        session.add(new_session)
        session.commit()
        session.refresh(new_session)

        # Get the count of current tasks for the user
        from ..models.todo import Todo
        todo_statement = select(Todo).where(Todo.user_id == user_id)
        todo_results = session.exec(todo_statement)
        current_tasks = todo_results.all()
        current_tasks_count = len(current_tasks)

        return {
            "session_id": str(new_session.session_id),
            "welcome_message": "Hello! I'm Taskie, your friendly task assistant! How can I help you with your tasks today? 😊",
            "current_tasks_count": current_tasks_count,
            "success": True
        }


@router.delete("/session/{session_id}")
async def end_chat_session(
    session_id: str,
    token: str = Depends(JWTBearer())
):
    """
    End an active chat session
    """
    from ..database.database import get_db_session
    from ..models.chat_session import ChatSession
    from sqlmodel import select
    from jose import jwt
    from ..config import settings

    # Verify the token and get the authenticated user ID
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        authenticated_user_id = payload.get("sub")
    except jwt.JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token"
        )

    with get_db_session() as session:
        # Find the session
        statement = select(ChatSession).where(ChatSession.session_id == uuid.UUID(session_id))
        result = session.exec(statement)
        chat_session = result.first()

        if not chat_session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Verify that the session belongs to the authenticated user
        if chat_session.user_id != authenticated_user_id:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to end this session"
            )

        # Update the session to mark as inactive
        chat_session.is_active = False
        session.add(chat_session)
        session.commit()

        return {
            "message": "Session ended successfully",
            "success": True
        }