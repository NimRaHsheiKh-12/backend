"""Initial migration for user and todo models

Revision ID: 001_initial
Revises: 
Create Date: 2026-01-03 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
import uuid
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False)
    )

    # Create todos table
    op.create_table('todos',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('is_completed', sa.Boolean, nullable=False, default=False),
        sa.Column('priority', sa.String(20), nullable=False, default='Medium'),
        sa.Column('category', sa.String(50), nullable=True),
        sa.Column('due_date', sa.Date, nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False)
    )

    # Create check constraint for priority
    op.create_check_constraint(
        'valid_priority_values',
        'todos',
        "priority IN ('Low', 'Medium', 'High')"
    )


def downgrade() -> None:
    # Drop check constraint first
    op.drop_constraint('valid_priority_values', 'todos', type_='check')
    
    # Drop tables
    op.drop_table('todos')
    op.drop_table('users')