from pydantic import BaseModel, EmailStr, Field, field_validator # type: ignore
from datetime import datetime
from uuid import UUID


class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    first_name: str = Field(..., min_length=2, max_length=50)
    last_name: str = Field(..., min_length=2, max_length=50)
    
    @field_validator('email', mode='before')
    @classmethod
    def normalize_email(cls, v):
        """Convert email to lowercase"""
        if isinstance(v, str):
            return v.lower().strip()
        return v
    
    @field_validator('first_name', 'last_name', mode='before')
    @classmethod
    def trim_names(cls, v):
        """Trim whitespace from names"""
        if isinstance(v, str):
            return v.strip()
        return v


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)


class UserUpdate(BaseModel):
    username: str | None = Field(None, min_length=3, max_length=50)
    email: EmailStr | None = None
    first_name: str | None = Field(None, min_length=2, max_length=50)
    last_name: str | None = Field(None, min_length=2, max_length=50)
    
    @field_validator('email', mode='before')
    @classmethod
    def normalize_email(cls, v):
        """Convert email to lowercase"""
        if v and isinstance(v, str):
            return v.lower().strip()
        return v
    
    @field_validator('first_name', 'last_name', mode='before')
    @classmethod
    def trim_names(cls, v):
        """Trim whitespace from names"""
        if v and isinstance(v, str):
            return v.strip()
        return v


class UserResponse(UserBase):
    id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True

