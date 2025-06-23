from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from sqlmodel import Session, select
from database import SessionDep, get_session
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

from fastapi import Form, File, UploadFile
import os

@auth_router.post("/signup", response_model=AuthResponse)
async def signup(
    email: EmailStr = Form(...),
    password: str = Form(...),
    firstName: str = Form(...),
    lastName: str = Form(...),
    phoneNumber: str = Form(...),
    dateOfBirth: str = Form(...),
    profilePhoto: UploadFile = File(...),
    session: Session = Depends(get_session)
):
    # Check if user exists
    statement = select(User).where(User.email == email)
    if session.exec(statement).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Parse date
    try:
        dob = datetime.strptime(dateOfBirth, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    # Clean phone number
    cleaned_phone = int("".join(filter(str.isdigit, phoneNumber)))

    # Save profile photo
    os.makedirs("media/photos", exist_ok=True)
    if profilePhoto.filename and "." in profilePhoto.filename:
        ext = profilePhoto.filename.split(".")[-1]
    else:
        ext = "jpg"  # default extension if filename is missing or has no extension
    filename = f"{email.replace('@', '_')}_{int(datetime.utcnow().timestamp())}.{ext}"
    filepath = os.path.join("media/photos", filename)

    with open(filepath, "wb") as f:
        f.write(await profilePhoto.read())

    # Save user to DB
    new_user = User(
        first_name=firstName,
        last_name=lastName,
        email=email,
        password=password,
        phone_number=str(cleaned_phone),
        date_of_birth=dob,
        photo_path=filepath,
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
