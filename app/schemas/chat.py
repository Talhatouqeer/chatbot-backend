from pydantic import BaseModel, Field, ConfigDict # type: ignore
from datetime import datetime
from uuid import UUID
from typing import Optional, List


class ChatMessageRequest(BaseModel):
    message: str = Field(..., min_length=1)


class ChatMessageResponse(BaseModel):
    id: UUID
    message: str
    response: str
    message_type: str
    image_url: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(
        from_attributes=True,
        protected_namespaces=()
    )


class ChatHistoryResponse(BaseModel):
    id: UUID
    user_id: UUID
    message: str
    response: str
    message_type: str
    image_url: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(
        from_attributes=True,
        protected_namespaces=()
    )


class ChatMessageWithHistoryResponse(BaseModel):
    """Response with current chat and previous chat history"""
    current_chat: ChatMessageResponse
    chat_history: List[ChatHistoryResponse]
    total_chats: int
    
    model_config = ConfigDict(
        from_attributes=True,
        protected_namespaces=()
    )

