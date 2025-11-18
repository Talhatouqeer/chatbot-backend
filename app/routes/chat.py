from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request # type: ignore
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
    request: Request,
    message: Optional[str] = Form(None),  # Optional text message
    voice: Optional[UploadFile] = File(None),  # Optional voice file
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Send a text message OR voice note to the chatbot
    
    - If voice file provided: STT (voice → text) → Agent response → TTS (text → audio)
    - If text provided: Direct agent response → TTS skipped for faster response
    
    Returns current chat + previous chat history
    """
    from app.services.speech_service import speech_service

    voice_file_path = None
    voice_url = None
    message_text = None

    # Handle voice file (STT)
    if voice:
        # Validate file type
        if voice.content_type not in settings.ALLOWED_AUDIO_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed types: {', '.join(settings.ALLOWED_AUDIO_TYPES)}"
            )

        # Read and save voice file
        contents = await voice.read()
        if len(contents) > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE / (1024*1024)}MB"
            )

        file_extension = voice.filename.split(".")[-1] if "." in voice.filename else "mp3"
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        voice_file_path = os.path.join(UPLOAD_DIR, unique_filename)

        async with aiofiles.open(voice_file_path, "wb") as f:
            await f.write(contents)

        try:
            # STT: Convert voice to text
            message_text = await speech_service.convert_voice_to_text(voice_file_path)

            # Generate voice URL
            base_url = str(request.base_url).rstrip('/')
            voice_url = f"{base_url}/uploads/{unique_filename}"
        except Exception as e:
            # Clean up file if processing fails
            if voice_file_path and os.path.exists(voice_file_path):
                try:
                    os.remove(voice_file_path)
                except:
                    pass
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error processing voice note: {str(e)}"
            )

    # Handle text message (if no voice file)
    elif message:
        message_text = message
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 'message' (text) or 'voice' (file) must be provided"
        )

    # Validate and process message
    message_text = gemini_service.validate_and_process_message(message_text)

    # Generate AI response (as usual)
    ai_response = await gemini_service.generate_text_response(message_text)

    # TTS: Only run for voice messages
    response_audio_url = None
    if voice:  # Only convert to audio if user sent a voice note
        try:
            response_audio_filename = f"{uuid.uuid4()}.mp3"
            response_audio_path = os.path.join(UPLOAD_DIR, response_audio_filename)
            await speech_service.convert_text_to_speech(ai_response, response_audio_path)

            base_url = str(request.base_url).rstrip('/')
            response_audio_url = f"{base_url}/uploads/{response_audio_filename}"
        except Exception as e:
            print(f"[WARNING] TTS failed: {str(e)}. Continuing without audio.")
            response_audio_url = None  # Keep None if TTS fails

    # Save to database
    chat_entry = ChatHistory(
        user_id=current_user.id,
        message=message_text,
        response=ai_response,
        message_type=MessageType.VOICE if voice else MessageType.TEXT,
        voice_url=voice_url,
        response_audio_url=response_audio_url
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
    request: Request,
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
        
        # Generate full URL for image (works for local and production)
        base_url = str(request.base_url).rstrip('/')
        full_image_url = f"{base_url}/uploads/{unique_filename}"
        
        # Save to database with full URL
        chat_entry = ChatHistory(
            user_id=current_user.id,
            message=message,
            response=ai_response,
            message_type=MessageType.IMAGE,
            image_url=full_image_url
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
            try:
                # Try to remove file, but don't fail if it's locked
                os.remove(file_path)
            except PermissionError:
                # File is locked by another process (Pillow), skip deletion
                # File will be cleaned up later or on server restart
                print(f"⚠️ Could not delete file {file_path} - file in use")
                pass
            except Exception as del_error:
                print(f"⚠️ Error deleting file: {str(del_error)}")
                pass
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

