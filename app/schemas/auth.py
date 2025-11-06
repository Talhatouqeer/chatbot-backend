from pydantic import BaseModel, EmailStr, Field, field_validator # type: ignore


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    
    @field_validator('email', mode='before')
    @classmethod
    def normalize_email(cls, v):
        """Convert email to lowercase for consistent login"""
        if isinstance(v, str):
            return v.lower().strip()
        return v


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class ForgotPasswordRequest(BaseModel):
    email: EmailStr
    
    @field_validator('email', mode='before')
    @classmethod
    def normalize_email(cls, v):
        """Convert email to lowercase"""
        if isinstance(v, str):
            return v.lower().strip()
        return v


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)


class MessageResponse(BaseModel):
    message: str

