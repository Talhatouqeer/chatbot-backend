from sqlalchemy.orm import Session
from fastapi import HTTPException, status # type: ignore
from app.models.user import User
from app.models.chat import PasswordResetToken
from app.schemas.user import UserCreate
from app.utils.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    generate_reset_token,
    create_reset_token_expiry
)
from app.utils.validators import validate_password_strength, validate_username
from datetime import datetime, timedelta, timezone


class AuthService:
    @staticmethod
    def register_user(db: Session, user_data: UserCreate) -> User:
        """Register a new user"""
        # Validate username
        validate_username(user_data.username)
        
        # Validate password strength
        validate_password_strength(user_data.password)
        
        # Check if email already exists
        if db.query(User).filter(User.email == user_data.email).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Check if username already exists
        if db.query(User).filter(User.username == user_data.username).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        
        # Create new user
        hashed_password = get_password_hash(user_data.password)
        new_user = User(
            email=user_data.email,
            username=user_data.username,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            hashed_password=hashed_password
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return new_user
    
    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> User:
        """Authenticate user with email and password"""
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        if not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        return user
    
    @staticmethod
    def create_user_token(user: User) -> str:
        """Create JWT token for user"""
        access_token_expires = timedelta(minutes=10080)  # 7 days
        access_token = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=access_token_expires
        )
        return access_token
    
    @staticmethod
    def create_password_reset_token(db: Session, email: str) -> tuple[User, str]:
        """Create password reset token"""
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User with this email not found"
            )
        
        # Generate reset token
        token = generate_reset_token()
        expires_at = create_reset_token_expiry()
        
        # Save token to database
        reset_token = PasswordResetToken(
            user_id=user.id,
            token=token,
            expires_at=expires_at
        )
        
        db.add(reset_token)
        db.commit()
        
        return user, token
    
    @staticmethod
    def reset_password(db: Session, token: str, new_password: str) -> None:
        """Reset user password with token"""
        # Validate password strength
        validate_password_strength(new_password)
        
        # Find token
        reset_token = db.query(PasswordResetToken).filter(
            PasswordResetToken.token == token
        ).first()
        
        if not reset_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        # Check if token is expired
        if reset_token.expires_at < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reset token has expired"
            )
        
        # Check if token is already used
        if reset_token.is_used:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reset token has already been used"
            )
        
        # Get user
        user = db.query(User).filter(User.id == reset_token.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update password
        user.hashed_password = get_password_hash(new_password)
        
        # Mark token as used
        reset_token.is_used = True
        
        db.commit()

