"""add_voice_message_type_and_audio_urls

Revision ID: 7fc6d2bfe359
Revises: d35d5da547bd
Create Date: 2025-11-18 20:43:05.171442

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7fc6d2bfe359'
down_revision = 'd35d5da547bd'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add 'VOICE' to MessageType enum
    op.execute("ALTER TYPE messagetype ADD VALUE IF NOT EXISTS 'VOICE'")
    
    # Add voice_url column
    op.add_column('chat_history', sa.Column('voice_url', sa.String(), nullable=True))
    
    # Add response_audio_url column
    op.add_column('chat_history', sa.Column('response_audio_url', sa.String(), nullable=True))


def downgrade() -> None:
    # Remove columns
    op.drop_column('chat_history', 'response_audio_url')
    op.drop_column('chat_history', 'voice_url')
    
    # Note: PostgreSQL doesn't support removing enum values directly
    # The 'VOICE' enum value will remain but won't be used

