from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from sqlmodel import Session, select
from database import SessionDep
from schemas import User
from datetime import datetime
from typing import Optional

auth_router = APIRouter()

# Request/Response Models
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

@auth_router.post("/login", response_model=AuthResponse)
def login(request: LoginRequest, session: SessionDep):
    # Check hardcoded admin credentials
    if request.email == "admin" and request.password == "admin":
        return AuthResponse(
            success=True,
            message="Admin login successful",
            user_type="admin",
            user_id=0
        )
    
    # Check regular user credentials
    statement = select(User).where(User.email == request.email)
    user = session.exec(statement).first()
    
    if not user or user.password != request.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    return AuthResponse(
        success=True,
        message="Login successful",
        user_type="user",
        user_id=user.id
    )

@auth_router.post("/signup", response_model=AuthResponse)
def signup(request: SignupRequest, session: SessionDep):
    # Check if user already exists
    statement = select(User).where(User.email == request.email)
    existing_user = session.exec(statement).first()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Parse date of birth
    try:
        dob = datetime.strptime(request.dateOfBirth, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Create new user
    new_user = User(
        first_name=request.firstName,
        last_name=request.lastName,
        email=request.email,
        password=request.password,
        phone_number=int(request.phoneNumber.replace("+", "").replace("(", "").replace(")", "").replace("-", "").replace(" ", "")),
        date_of_birth=dob,
        photo_path=request.profilePhoto
    )
    
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    
    return AuthResponse(
        success=True,
        message="Account created successfully",
        user_type="user",
        user_id=new_user.id
    )