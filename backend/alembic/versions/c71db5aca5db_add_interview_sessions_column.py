"""add_interview_sessions_column

Revision ID: c71db5aca5db
Revises: 
Create Date: 2026-01-02 00:54:28.497656

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c71db5aca5db'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add interview_sessions column if it doesn't exist
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='sessionmodel' AND column_name='interview_sessions'
            ) THEN
                ALTER TABLE sessionmodel 
                ADD COLUMN interview_sessions JSON DEFAULT '{}'::JSON;
            END IF;
        END $$;
    """)


def downgrade() -> None:
    # Remove interview_sessions column
    op.drop_column('sessionmodel', 'interview_sessions')
