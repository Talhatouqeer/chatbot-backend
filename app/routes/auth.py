from fastapi import APIRouter, Depends, HTTPException, status # type: ignore
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    MessageResponse
)
from app.schemas.user import UserCreate, UserResponse
from app.services.auth_service import AuthService
from app.services.email_service import EmailService
from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user
    
    - **email**: Valid email address (unique)
    - **username**: Username (3-50 characters, unique)
    - **password**: Password (min 8 chars, 1 uppercase, 1 lowercase, 1 number)
    """
    user = AuthService.register_user(db, user_data)
    
    # Send welcome email (non-blocking)
    try:
        EmailService.send_welcome_email(user.email, user.username)
    except:
        pass  # Don't fail registration if email fails
    
    return user


@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login with email and password
    
    Returns JWT access token and user information
    """
    # Authenticate user
    user = AuthService.authenticate_user(db, login_data.email, login_data.password)
    
    # Create access token
    access_token = AuthService.create_user_token(user)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name
        }
    }


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Request password reset email
    
    Sends an email with a reset token that expires in 1 hour
    (Token is also printed in console for local testing)
    """
    try:
        user, token = AuthService.create_password_reset_token(db, request.email)
        
        # Send reset email (will print token in console if email fails)
        EmailService.send_password_reset_email(user.email, user.username, token)
        
        return {
            "message": "Password reset email sent successfully. Check your inbox (or console for testing)."
        }
    except HTTPException:
        # Return success message even if user not found (security best practice)
        return {
            "message": "If an account with that email exists, a password reset link has been sent."
        }


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Reset password using token from email
    
    - **token**: Reset token from email
    - **new_password**: New password (min 8 chars, 1 uppercase, 1 lowercase, 1 number)
    """
    AuthService.reset_password(db, request.token, request.new_password)
    
    return {
        "message": "Password has been reset successfully. You can now login with your new password."
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user information
    
    Requires valid JWT token
    """
    return current_user


@router.get("/verify-token")
async def verify_token(
    current_user: User = Depends(get_current_user)
):
    """
    Verify if JWT token is valid
    
    Returns user basic info if token is valid
    """
    return {
        "valid": True,
        "user": {
            "id": str(current_user.id),
            "email": current_user.email,
            "username": current_user.username
        }
    }

