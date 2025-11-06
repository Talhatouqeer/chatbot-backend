from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form # type: ignore
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid
import aiofiles # type: ignore
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.chat import ChatHistory, MessageType
from app.schemas.chat import ChatMessageRequest, ChatMessageResponse, ChatHistoryResponse, ChatMessageWithHistoryResponse
from app.services.gemini_service import gemini_service
from app.config import settings

router = APIRouter(prefix="/api/chat", tags=["Chat"])

# Create uploads directory if it doesn't exist
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/message", response_model=ChatMessageWithHistoryResponse)
async def send_message(
    request: ChatMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Send a text message to the chatbot
    
    Returns current chat + previous chat history
    Supports English and Roman Urdu text
    """
    # Validate and process message
    message = gemini_service.validate_and_process_message(request.message)
    
    # Generate AI response
    ai_response = await gemini_service.generate_text_response(message)
    
    # Save to database
    chat_entry = ChatHistory(
        user_id=current_user.id,
        message=message,
        response=ai_response,
        message_type=MessageType.TEXT
    )
    
    db.add(chat_entry)
    db.commit()
    db.refresh(chat_entry)
    
    # Get previous chat history (excluding current one, last 20 chats)
    previous_chats = db.query(ChatHistory).filter(
        ChatHistory.user_id == current_user.id,
        ChatHistory.id != chat_entry.id
    ).order_by(ChatHistory.created_at.desc()).limit(20).all()
    
    # Get total chat count
    total_chats = db.query(ChatHistory).filter(
        ChatHistory.user_id == current_user.id
    ).count()
    
    return {
        "current_chat": chat_entry,
        "chat_history": previous_chats,
        "total_chats": total_chats
    }


@router.post("/upload-image", response_model=ChatMessageWithHistoryResponse)
async def upload_image(
    message: str = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload an image with a text message
    
    Returns current chat + previous chat history
    The AI will analyze the image and respond based on the message
    """
    # Validate message
    message = gemini_service.validate_and_process_message(message)
    
    # Validate file type
    if image.content_type not in settings.ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(settings.ALLOWED_IMAGE_TYPES)}"
        )
    
    # Validate file size
    contents = await image.read()
    if len(contents) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE / (1024*1024)}MB"
        )
    
    # Generate unique filename
    file_extension = image.filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    # Save file
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(contents)
    
    try:
        # Generate AI response with image
        ai_response = await gemini_service.generate_image_response(message, file_path)
        
        # Save to database
        chat_entry = ChatHistory(
            user_id=current_user.id,
            message=message,
            response=ai_response,
            message_type=MessageType.IMAGE,
            image_url=f"/uploads/{unique_filename}"
        )
        
        db.add(chat_entry)
        db.commit()
        db.refresh(chat_entry)
        
        # Get previous chat history (excluding current one, last 20 chats)
        previous_chats = db.query(ChatHistory).filter(
            ChatHistory.user_id == current_user.id,
            ChatHistory.id != chat_entry.id
        ).order_by(ChatHistory.created_at.desc()).limit(20).all()
        
        # Get total chat count
        total_chats = db.query(ChatHistory).filter(
            ChatHistory.user_id == current_user.id
        ).count()
        
        return {
            "current_chat": chat_entry,
            "chat_history": previous_chats,
            "total_chats": total_chats
        }
    
    except Exception as e:
        # Clean up file if processing fails
        if os.path.exists(file_path):
            os.remove(file_path)
        raise e


@router.get("/history", response_model=List[ChatHistoryResponse])
async def get_chat_history(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get user's chat history
    
    Returns most recent chats first (ordered by created_at DESC)
    
    - **skip**: Number of records to skip (default: 0)
    - **limit**: Maximum number of records to return (default: 50, max: 100)
    """
    if limit > 100:
        limit = 100
    
    chats = db.query(ChatHistory).filter(
        ChatHistory.user_id == current_user.id
    ).order_by(
        ChatHistory.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    return chats


@router.get("/history/{chat_id}", response_model=ChatHistoryResponse)
async def get_chat_by_id(
    chat_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get specific chat by ID
    """
    chat = db.query(ChatHistory).filter(
        ChatHistory.id == chat_id,
        ChatHistory.user_id == current_user.id
    ).first()
    
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    
    return chat


@router.delete("/history/{chat_id}")
async def delete_chat(
    chat_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete specific chat
    """
    chat = db.query(ChatHistory).filter(
        ChatHistory.id == chat_id,
        ChatHistory.user_id == current_user.id
    ).first()
    
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    
    # Delete associated image file if exists
    if chat.image_url:
        filename = chat.image_url.split("/")[-1]
        file_path = os.path.join(UPLOAD_DIR, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
    
    db.delete(chat)
    db.commit()
    
    return {"message": "Chat deleted successfully"}


@router.delete("/history")
async def delete_all_chats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete all chat history for current user
    """
    # Get all user's chats
    chats = db.query(ChatHistory).filter(
        ChatHistory.user_id == current_user.id
    ).all()
    
    # Delete associated image files
    for chat in chats:
        if chat.image_url:
            filename = chat.image_url.split("/")[-1]
            file_path = os.path.join(UPLOAD_DIR, filename)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass  # Continue even if file deletion fails
    
    # Delete all chats
    db.query(ChatHistory).filter(
        ChatHistory.user_id == current_user.id
    ).delete()
    
    db.commit()
    
    return {"message": f"Deleted {len(chats)} chat(s) successfully"}

