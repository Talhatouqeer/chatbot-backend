"""audio-upload

Revision ID: d44abe45f251
Revises: 7fc6d2bfe359
Create Date: 2025-11-18 20:57:11.636713

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = 'd44abe45f251'
down_revision = '7fc6d2bfe359'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if columns already exist (they were added in previous migration 7fc6d2bfe359)
    # This prevents duplicate column error during deployment
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('chat_history')]
    
    # Only add columns if they don't exist
    if 'voice_url' not in columns:
        op.add_column('chat_history', sa.Column('voice_url', sa.String(), nullable=True))
    
    if 'response_audio_url' not in columns:
        op.add_column('chat_history', sa.Column('response_audio_url', sa.String(), nullable=True))


def downgrade() -> None:
    # Check if columns exist before dropping
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('chat_history')]
    
    if 'response_audio_url' in columns:
        op.drop_column('chat_history', 'response_audio_url')
    
    if 'voice_url' in columns:
        op.drop_column('chat_history', 'voice_url')

