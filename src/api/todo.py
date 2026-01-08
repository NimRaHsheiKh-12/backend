from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database.database import get_db
from ..schemas.todo import TodoCreate, TodoUpdate, TodoResponse
from ..services.todo_service import TodoService
from ..auth.auth_handler import get_current_user
from ..models.user import User
from uuid import UUID
from ..models.todo import PriorityEnum


router = APIRouter()


@router.post("/", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
async def create_todo(
    todo: TodoCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new todo for the authenticated user.
    """
    return TodoService.create_todo(db, todo, current_user.id)


@router.get("/", response_model=List[TodoResponse])
async def get_todos(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search todos by title"),
    status_filter: Optional[bool] = Query(None, description="Filter by completion status (true for completed, false for pending)"),
    priority: Optional[PriorityEnum] = Query(None, description="Filter by priority"),
    category: Optional[str] = Query(None, description="Filter by category"),
    due_date: Optional[str] = Query(None, description="Filter by due date (today, upcoming, overdue, or specific date in YYYY-MM-DD format)")
):
    """
    Get all todos for the authenticated user with optional filtering and pagination.
    """
    todos = TodoService.get_todos_by_user(
        db,
        current_user.id,
        skip=skip,
        limit=limit,
        search=search,
        status=status_filter,
        priority=priority,
        category=category,
        due_date=due_date
    )
    return todos


@router.get("/{todo_id}", response_model=TodoResponse)
async def get_todo(
    todo_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific todo by ID for the authenticated user.
    """
    todo = TodoService.get_todo_by_id(db, todo_id, current_user.id)
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found"
        )
    return todo


@router.put("/{todo_id}", response_model=TodoResponse)
async def update_todo(
    todo_id: UUID,
    todo_update: TodoUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a specific todo by ID for the authenticated user.
    """
    updated_todo = TodoService.update_todo(db, todo_id, todo_update, current_user.id)
    if not updated_todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found"
        )
    return updated_todo


@router.patch("/{todo_id}/toggle", response_model=TodoResponse)
async def toggle_todo_completion(
    todo_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Toggle the completion status of a specific todo for the authenticated user.
    """
    updated_todo = TodoService.toggle_todo_completion(db, todo_id, current_user.id)
    if not updated_todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found"
        )
    return updated_todo


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(
    todo_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a specific todo by ID for the authenticated user.
    """
    success = TodoService.delete_todo(db, todo_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found"
        )
    # Return 204 No Content for successful deletion
    return