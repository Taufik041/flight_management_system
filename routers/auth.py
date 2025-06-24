from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from sqlmodel import Session, select
from database import SessionDep, get_session
from schemas import User
from datetime import datetime
from typing import Optional
from models import LoginRequest, SignupRequest, AuthResponse
from fastapi import Form, File, UploadFile
import os
from utils.email import send_email
from id_card import generate_id_card
from schemas import Program, Enrollment

auth_router = APIRouter()


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
    statement = select(User).where(User.email == request.email, User.is_active == True)
    user = session.exec(statement).first()
    
    if not user or user.password != request.password or not User.is_active:
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
    firstName: str = Form(...),
    lastName: str = Form(...),
    phoneNumber: str = Form(...),
    dateOfBirth: str = Form(...),
    profilePhoto: UploadFile = File(...),
    session: Session = Depends(get_session)
):
    # Check if user exists
    statement = select(User).where(User.email == email, User.is_active == True)
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
        ext = "jpg"  # default extension
        
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

    # Get currently enrolled program title for instructor field
    enrollment = session.exec(
        select(Enrollment).where(Enrollment.user_id == new_user.id, Enrollment.is_active == True)
    ).first() or None

    program = session.get(Program, enrollment.program_id) if enrollment else None
    program_title = program.title if program else "N/A"

    user_data = {
        "first_name": new_user.first_name,
        "last_name": new_user.last_name
    }
    
    event_data = {
        "designation": "Student",
        "instructor": program_title,
        "place" : "Room X, Campus A"
    }
    roll_no = str(new_user.id)
    generate_id_card(user_data, event_data, roll_no, roll_no)
    card_path = f"assets/cards/{new_user.first_name}.png"
    
    email_body = {
        "recipient": email,
        "subject": "Welcome to the Program!",
        "body": f"Hi {firstName},\n\nWelcome to the program. We're glad to have you on board!",
        "attachments": card_path
    }
    
    send_email(
        to = email_body["recipient"],
        subject = email_body["subject"],
        body= email_body["body"],
        attachment_path = email_body["attachments"]
    )
    
    return AuthResponse(
        success=True,
        message="Account created successfully",
        user_type="user",
        user_id=new_user.id
    )
