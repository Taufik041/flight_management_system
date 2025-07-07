from fastapi import APIRouter, HTTPException, Depends, Form, File, UploadFile
from pydantic import BaseModel, EmailStr
from sqlmodel import Session, select
from database import SessionDep, get_session
from schemas import User, Program, Enrollment
from datetime import datetime
from typing import Optional
from models import LoginRequest, SignupRequest, AuthResponse
import os
from logger import logger
from utils.email import send_email
from utils.security import hash_password, verify_password
from id_card import generate_id_card

auth_router = APIRouter()

@auth_router.post("/login", response_model=AuthResponse)
def login(request: LoginRequest, session: SessionDep):
    # ✅ Hardcoded Admin Login
    if request.email == "admin@gmail.com" and request.password == "Admin123":
        return AuthResponse(
            success=True,
            message="Admin login successful",
            user_type="admin",
            user_id=0
        )

    # ✅ Check DB User
    statement = select(User).where(User.email == request.email, User.is_active == True)
    user = session.exec(statement).first()

    if not user or not verify_password(request.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return AuthResponse(
        success=True,
        message="Login successful",
        user_type="user",
        user_id=user.id
    )



@auth_router.post("/signup", response_model=AuthResponse)
async def signup(
    email: EmailStr = Form(...),
    password: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    phone_number: str = Form(...),
    date_of_birth: str = Form(...),
    profile_photo: Optional[UploadFile] = File(None),
    session: Session = Depends(get_session)
):
    # Check if user exists
    statement = select(User).where(User.email == email, User.is_active == True)
    if session.exec(statement).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Parse date
    try:
        dob = datetime.strptime(date_of_birth, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    # Clean phone number
    cleaned_phone = int("".join(filter(str.isdigit, phone_number)))

    # Save profile photo if provided, else use default
    os.makedirs("media/photos", exist_ok=True)
    if profile_photo and profile_photo.filename and "." in profile_photo.filename:
        ext = profile_photo.filename.split(".")[-1]
        filename = f"{email.replace('@', '_')}_{int(datetime.utcnow().timestamp())}.{ext}"
        filepath = os.path.join("D:/bipros_evaluation/flight_management_system/media/photos", filename)
        with open(filepath, "wb") as f:
            f.write(await profile_photo.read())
        photo_path = filepath
    else:
        # Use a default placeholder image (ensure this file exists in your static/media/photos folder)
        photo_path = "D:/bipros_evaluation/flight_management_system/media/photos/placeholder-user.jpg"

    # Save user to DB
    new_user = User(
        first_name=first_name,
        last_name=last_name,
        email=email,
        password=hash_password(password),
        phone_number=str(cleaned_phone),
        date_of_birth=dob,
        photo_path=photo_path,
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    # Try to send welcome email - don't fail signup if email fails
    try:
        email_sent = send_email(
            to=email,
            subject="Welcome to the Flight Management System!",
            body=f"Hi {first_name},\n\nWelcome to the Flight Management System! We're excited to have you on board.\n\nYou can now log in to your account and explore our programs.\n\nBest regards,\nFlight Management Team"
        )
        if not email_sent:
            logger.warning(f"Welcome email could not be sent to {email}")
    except Exception as e:
        logger.error(f"Email service error during signup for {email}: {str(e)}")
        # Continue without failing the signup
    
    return AuthResponse(
        success=True,
        message="Account created successfully",
        user_type="user",
        user_id=new_user.id
    )
