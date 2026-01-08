from typing import Optional, List
from sqlmodel import Session, select
from ..models.todo import Todo
from ..schemas.todo import TodoCreate, TodoUpdate
from uuid import UUID


class TodoService:
    @staticmethod
    def create_todo(db: Session, todo_data: TodoCreate, user_id: UUID) -> Todo:
        """
        Create a new todo for a user.

        Args:
            db: Database session
            todo_data: Todo creation data
            user_id: ID of the user who owns the todo

        Returns:
            Created Todo object
        """
        # Create the todo object with the user_id
        db_todo = Todo(
            **todo_data.model_dump(),
            user_id=user_id
        )

        # Add to database
        db.add(db_todo)
        db.commit()
        db.refresh(db_todo)

        return db_todo

    @staticmethod
    def get_todo_by_id(db: Session, todo_id: UUID, user_id: UUID) -> Optional[Todo]:
        """
        Get a specific todo by its ID for a specific user.

        Args:
            db: Database session
            todo_id: ID of the todo to retrieve
            user_id: ID of the user who owns the todo

        Returns:
            Todo object if found, None otherwise
        """
        statement = select(Todo).where(Todo.id == todo_id, Todo.user_id == user_id)
        result = db.execute(statement)
        return result.scalar_one_or_none()

    @staticmethod
    def get_todos_by_user(
        db: Session,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        status: Optional[bool] = None,
        priority: Optional[str] = None,
        category: Optional[str] = None,
        due_date: Optional[str] = None
    ) -> List[Todo]:
        """
        Get all todos for a specific user with optional filtering and pagination.

        Args:
            db: Database session
            user_id: ID of the user whose todos to retrieve
            skip: Number of records to skip
            limit: Maximum number of records to return
            search: Optional search term to filter by title
            status: Optional filter by completion status
            priority: Optional filter by priority
            category: Optional filter by category
            due_date: Optional filter by due date ("today", "upcoming", "overdue", or specific date)

        Returns:
            List of Todo objects
        """
        statement = select(Todo).where(Todo.user_id == user_id)

        # Apply search filter if provided
        if search:
            statement = statement.where(Todo.title.contains(search))

        # Apply status filter if provided
        if status is not None:
            statement = statement.where(Todo.is_completed == status)

        # Apply priority filter if provided
        if priority:
            statement = statement.where(Todo.priority == priority)

        # Apply category filter if provided
        if category:
            statement = statement.where(Todo.category == category)

        # Apply due date filter if provided
        if due_date:
            from datetime import date, timedelta
            today = date.today()

            if due_date == "today":
                statement = statement.where(Todo.due_date == today)
            elif due_date == "upcoming":
                statement = statement.where(Todo.due_date > today)
            elif due_date == "overdue":
                statement = statement.where(Todo.due_date < today)
            else:
                # Try to parse as specific date (YYYY-MM-DD format)
                try:
                    specific_date = date.fromisoformat(due_date)
                    statement = statement.where(Todo.due_date == specific_date)
                except ValueError:
                    # If the date format is invalid, ignore the filter
                    pass

        statement = statement.offset(skip).limit(limit)
        result = db.execute(statement)
        return result.scalars().all()

    @staticmethod
    def update_todo(db: Session, todo_id: UUID, todo_update: TodoUpdate, user_id: UUID) -> Optional[Todo]:
        """
        Update a specific todo for a user.

        Args:
            db: Database session
            todo_id: ID of the todo to update
            todo_update: Update data
            user_id: ID of the user who owns the todo

        Returns:
            Updated Todo object if successful, None otherwise
        """
        # Get the existing todo
        statement = select(Todo).where(Todo.id == todo_id, Todo.user_id == user_id)
        result = db.execute(statement)
        db_todo = result.scalar_one_or_none()

        if not db_todo:
            return None

        # Update the todo with the new values
        for field, value in todo_update.model_dump(exclude_unset=True).items():
            setattr(db_todo, field, value)

        # Update the updated_at timestamp
        from datetime import datetime
        db_todo.updated_at = datetime.utcnow()

        # Commit changes to database
        db.add(db_todo)
        db.commit()
        db.refresh(db_todo)

        return db_todo

    @staticmethod
    def delete_todo(db: Session, todo_id: UUID, user_id: UUID) -> bool:
        """
        Delete a specific todo for a user.

        Args:
            db: Database session
            todo_id: ID of the todo to delete
            user_id: ID of the user who owns the todo

        Returns:
            True if deletion was successful, False otherwise
        """
        statement = select(Todo).where(Todo.id == todo_id, Todo.user_id == user_id)
        result = db.execute(statement)
        db_todo = result.scalar_one_or_none()

        if not db_todo:
            return False

        # Delete the todo from database
        db.delete(db_todo)
        db.commit()

        return True

    @staticmethod
    def toggle_todo_completion(db: Session, todo_id: UUID, user_id: UUID) -> Optional[Todo]:
        """
        Toggle the completion status of a specific todo for a user.

        Args:
            db: Database session
            todo_id: ID of the todo to toggle
            user_id: ID of the user who owns the todo

        Returns:
            Updated Todo object if successful, None otherwise
        """
        statement = select(Todo).where(Todo.id == todo_id, Todo.user_id == user_id)
        result = db.execute(statement)
        db_todo = result.scalar_one_or_none()

        if not db_todo:
            return None

        # Toggle the completion status
        db_todo.is_completed = not db_todo.is_completed

        # Update the updated_at timestamp
        from datetime import datetime
        db_todo.updated_at = datetime.utcnow()

        # Commit changes to database
        db.add(db_todo)
        db.commit()
        db.refresh(db_todo)

        return db_todo