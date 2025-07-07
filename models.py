from pydantic import BaseModel, EmailStr
from typing import Optional

# Request body model
class ProgramCreate(BaseModel):
    title: str
    description: str
    price: float
    
class TaskCreate(BaseModel):
    program_id: int
    title: str
    description: str
    cost: float
    duration: int  # minutes
    
class TaskUpdate(BaseModel):
    title: Optional[str]
    description: Optional[str]
    cost: Optional[float]
    duration: Optional[int]
    
class LoginRequest(BaseModel):
    email: str
    password: str

class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    firstName: str
    lastName: str
    phoneNumber: str
    dateOfBirth: str
    profilePhoto: Optional[str] = None

class AuthResponse(BaseModel):
    success: bool
    message: str
    user_type: Optional[str] = None
    user_id: Optional[int] = None