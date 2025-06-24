from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from database import SessionDep
from schemas import User, Program, Task, Enrollment, TaskCompletion, PaymentLog
from typing import List
from datetime import datetime
from id_card import generate_id_card
from fastapi.responses import FileResponse
import os

student_router = APIRouter()

# ------------------------
# Route 1: Get Enrolled Program + Available Programs
# ------------------------
@student_router.get("/programs")
def get_programs(user_id: int, session: SessionDep):
    # Get enrolled program
    enrollment = session.exec(
        select(Enrollment).where(
            Enrollment.user_id == user_id,
            Enrollment.is_active == True
        )
    ).first()

    enrolled_program = None
    if enrollment:
        enrolled_program = session.exec(
            select(Program).where(
                Program.id == enrollment.program_id,
                Program.is_active == True
            )
        ).first()

    # Get all available programs
    programs = session.exec(select(Program).where(Program.is_active == True)).all()

    return {
        "current_program": enrolled_program,
        "available_programs": programs
    }


# ------------------------
# Route 2: Enroll in a Program
# ------------------------
@student_router.post("/programs/{program_id}/enroll")
def enroll_in_program(program_id: int, user_id: int, session: SessionDep):
    # Check if already enrolled
    existing = session.exec(
        select(Enrollment).where(
            Enrollment.user_id == user_id,
            Enrollment.is_active == True
        )
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Already enrolled in a program")

    program = session.exec(
        select(Program).where(
            Program.id == program_id,
            Program.is_active == True
            )
        ).first()
    
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")

    user = session.exec(
        select(User).where(
            User.id == user_id,
            User.is_active == True
        )
    ).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    payments = session.exec(
        select(PaymentLog).where(PaymentLog.user_id == user_id)
    ).all()
    
    completions = session.exec(
        select(TaskCompletion).where(TaskCompletion.user_id == user_id)
    ).all()
    
    balance = sum(p.amount for p in payments) - sum(c.charge_amount for c in completions)
    if balance < program.price:
        raise HTTPException(
            status_code=402,
            detail=f"❌ Insufficient balance. Required: ₹{program.price}, Available: ₹{balance:.2f}"
        )

    enrollment = Enrollment(user_id=user_id, program_id=program_id)
    session.add(enrollment)

    session.add(
        PaymentLog(
            user_id=user_id,
            program_id=program_id,
            amount =- program.price
        )
    )

    session.commit()
    return {"success": True, "message": "Enrolled successfully"}


# ------------------------
# Route 3: View Tasks (current, completed, upcoming)
# ------------------------
@student_router.get("/tasks")
def get_tasks(user_id: int, session: SessionDep):
    # Get enrolled program
    enrollment = session.exec(
        select(Enrollment).where(
            Enrollment.user_id == user_id,
            Enrollment.is_active == True
        )
    ).first()
    
    if not enrollment:
        raise HTTPException(status_code=400, detail="Not enrolled in any program")

    program_id = enrollment.program_id

    # Get all tasks in program
    tasks = session.exec(
        select(Task).where(
            Task.program_id == program_id,
            Task.is_active == True
        )
    ).all()

    # Get student's completed tasks
    completions = session.exec(
        select(TaskCompletion).where(TaskCompletion.user_id == user_id)
    ).all()
    completed_ids = {c.task_id for c in completions}

    task_list = {
        "completed": [],
        "upcoming": []
    }

    for task in tasks:
        task_data = {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "cost": task.cost,
            "duration": task.duration
        }
        if task.id in completed_ids:
            task_list["completed"].append(task_data)
        else:
            task_list["upcoming"].append(task_data)

    return task_list


# ------------------------
# Route 4: Mark Task Completed + Add Flight Time
# ------------------------
@student_router.post("/tasks/{task_id}/complete")
def complete_task(task_id: int, user_id: int, flight_time: int, session: SessionDep):
    # Check if already marked completed
    existing = session.exec(
        select(TaskCompletion).where(
            TaskCompletion.task_id == task_id,
            TaskCompletion.user_id == user_id
        )
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Task already completed")

    task = session.exec(
        select(Task).where(
            Task.id ==  task_id,
            Task.is_active == True
            )
        ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    completion = TaskCompletion(
        user_id=user_id,
        task_id=task_id,
        flight_time=flight_time,
        charge_amount=task.cost  # cost may vary later based on flight_time if needed
    )
    session.add(completion)
    session.commit()
    return {"success": True, "message": "Task marked as completed"}


# ------------------------
# Route 5: Account Summary
# ------------------------
@student_router.get("/account")
def get_account_summary(user_id: int, session: SessionDep):
    user = session.exec(
        select(User).where(
            User.id == user_id,
            User.is_active == True
            )
        ).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    payments = session.exec(
        select(PaymentLog).where(PaymentLog.user_id == user_id)
    ).all()

    completions = session.exec(
        select(TaskCompletion).where(TaskCompletion.user_id == user_id)
    ).all()

    balance = sum(p.amount for p in payments) - sum(c.charge_amount for c in completions)

    return {
        "balance": balance,
        "spent_summary": [
            {
                "task_id": c.task_id,
                "flight_time": c.flight_time,
                "amount": c.charge_amount
            } for c in completions
        ],
        "payments": [
            {
                "program_id": p.program_id,
                "amount": p.amount,
                "paid_at": p.paid_at
            } for p in payments
        ]
    }


# ------------------------
# Route 6: Make Payment
# ------------------------
@student_router.post("/pay")
def make_payment(user_id: int, program_id: int, amount: float, session: SessionDep):
    program = session.exec(
        select(Program).where(
            Program.id == program_id,
            Program.is_active == True
            )
        ).first()
    
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")

    payment = PaymentLog(
        user_id=user_id,
        program_id=program_id,
        amount=amount,
        paid_at=datetime.utcnow()
    )
    session.add(payment)
    session.commit()
    return {"success": True, "message": "Payment recorded"}


# ------------------------
# Route 7: New id card
# ------------------------
@student_router.post("/id_card")
def create_id_card(user_id: int, session: SessionDep):
    user = session.exec(
        select(User).where(
            User.id == user_id,
            User.is_active == True
        )
    ).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Get currently enrolled program title for instructor field
    enrollment = session.exec(
        select(Enrollment).where(Enrollment.user_id == user_id, Enrollment.is_active == True)
    ).first()

    program = session.get(Program, enrollment.program_id) if enrollment else None
    program_title = program.title if program else "N/A"

    user_data = {
        "first_name": user.first_name,
        "last_name": user.last_name
    }
    
    event_data = {
        "designation": "Student",
        "instructor": program_title,
        "place" : "Room X, Campus A"
    }
    padded_id = str(user_id).zfill(9)
    card_filename = f"{user.first_name}.png"
    card_path = os.path.join("assets/cards", card_filename)
    profile_img = user.photo_path
    generate_id_card(user_data, event_data, padded_id, padded_id, profile_img)
    
    if not os.path.exists(card_path):
        raise HTTPException(status_code=500, detail="ID card generation failed")
    
    return FileResponse(card_path, media_type="image/png", filename=card_filename)