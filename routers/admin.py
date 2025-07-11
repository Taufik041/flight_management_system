from fastapi import APIRouter, Depends, HTTPException, Path
from sqlmodel import Session, select, delete
from database import SessionDep
from schemas import User, Program, Task, Enrollment, TaskCompletion, PaymentLog
from typing import List, Optional
from models import ProgramCreate, TaskCreate, TaskUpdate
from pydantic import BaseModel
from datetime import datetime, timedelta

admin_router = APIRouter()

class StudentUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None

@admin_router.post("/programs/", response_model=None)
def create_program(program_data: ProgramCreate, session: SessionDep):
    program_data_dict = dict(program_data)
    new_program = Program(**program_data_dict)
    session.add(new_program)
    session.commit()
    session.refresh(new_program)
    return {"success": True, "program": new_program.dict()}

@admin_router.get("/programs/", response_model=List[Program])
def list_programs(session: SessionDep):
    programs = session.exec(select(Program).where(Program.is_active == True)).all()
    return programs

@admin_router.get("/programs/{program_id}")
def get_program_details(program_id: int, session: SessionDep):
    program = session.exec(
        select(Program).where(Program.id == program_id, Program.is_active == True)
    ).first()
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")

    # Get enrolled students
    enrollments = session.exec(
        select(Enrollment).where(
            Enrollment.program_id == program_id,
            Enrollment.is_active == True
        )
    ).all()
    students = []
    for enrollment in enrollments:
        user = session.get(User, enrollment.user_id)
        if user:
            students.append({
                "id": user.id,
                "name": f"{user.first_name} {user.last_name}",
                "email": user.email
            })

    # Get tasks for this program
    tasks = session.exec(
        select(Task).where(
            Task.program_id == program_id,
            Task.is_active == True
        )
    ).all()

    return {
        "id": program.id,
        "title": program.title,
        "description": program.description,
        "price": program.price,
        "student_count": len(students),
        "students": students,
        "tasks": tasks
    }

@admin_router.delete("/programs/{program_id}")
def deactivate_program(program_id: int, session: SessionDep):
    program = session.get(Program, program_id)
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    
    program.is_active = False
    session.add(program)
    session.commit()
    
    return {"success": True, "message": "Program deactivated"}

@admin_router.post("/programs/{program_id}/toggle")
def toggle_program_status(program_id: int, session: SessionDep):
    program = session.get(Program, program_id)
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    program.is_active = not program.is_active
    session.add(program)
    session.commit()
    return {"success": True, "is_active": program.is_active}

@admin_router.post("/programs/{program_id}/tasks/")
def add_task_to_program(program_id: int, task_data: TaskCreate, session: SessionDep):
    # Ensure program exists
    program = session.exec(
        select(Program).where(
            Program.id == program_id,
            Program.is_active == True
            )
    ).first()
    
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")

    new_task = Task(**dict(task_data), program_id=program_id)
    program.price = program.price + new_task.cost
    session.add(new_task)
    session.commit()
    session.refresh(new_task)

    return new_task

@admin_router.get("/tasks/{task_id}")
def get_task_detail(task_id: int, session: SessionDep):
    
    task = session.exec(
        select(Task).where(
            Task.id == task_id, 
            Task.is_active == True
            )
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Get list of students who have enrolled in this task
    completions = session.exec(
        select(TaskCompletion).where(TaskCompletion.task_id == task_id)
    ).all()

    students = []
    for completion in completions:
        user = session.get(User, completion.user_id)
        if user:
            students.append({
                "student_id": user.id,
                "name": f"{user.first_name} {user.last_name}",
                "completed": True,
                "flight_time": completion.flight_time,
                "charge_amount": completion.charge_amount
            })

    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "cost": task.cost,
        "duration": task.duration,
        "created_at": task.created_at,
        "students": students
    }

@admin_router.put("/tasks/{task_id}")
def update_task(task_id: int, task_data: TaskUpdate, session: SessionDep):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    for field, value in task_data.dict(exclude_unset=True).items():
        setattr(task, field, value)

    session.add(task)
    session.commit()
    session.refresh(task)
    return task

@admin_router.delete("/tasks/{task_id}")
def deactivate_task(task_id: int, session: SessionDep):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.is_active = False
    session.add(task)
    session.commit()
    return {"success": True, "message": "Task deactivated"}

@admin_router.delete("/tasks/{task_id}/students/{student_id}")
def remove_student_from_task(task_id: int, student_id: int, session: SessionDep):
    completion = session.exec(
        select(TaskCompletion)
        .where(TaskCompletion.task_id == task_id)
        .where(TaskCompletion.user_id == student_id)
    ).first()

    if not completion:
        raise HTTPException(status_code=404, detail="Student not found in task")

    session.delete(completion)
    session.commit()
    return {"success": True, "message": "Student removed from task"}

@admin_router.get("/students/")
def list_students(session: SessionDep):
    users = session.exec(
        select(User).where(
            User.is_active == True
            )
        ).all()
    
    students = []
    
    for user in users:
        # Check if not admin
        if user.email != "admin":
            # Calculate balance from payment logs and task charges
            balance = 0
            for payment in user.payment_logs:
                balance += payment.amount

            completions = session.exec(
                select(TaskCompletion).where(TaskCompletion.user_id == user.id)
            ).all()

            for c in completions:
                balance -= c.charge_amount

            students.append({
                "id": user.id,
                "name": f"{user.first_name} {user.last_name}",
                "balance": balance
            })

    return students

@admin_router.get("/students/{student_id}")
def get_student_detail(student_id: int, session: SessionDep):
    user = session.exec(
        select(User).where(
            User.id == student_id,
            User.is_active == True
        )
    ).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="Student not found")

    enrollment = session.exec(
        select(Enrollment).where(
            Enrollment.user_id == student_id,
            Enrollment.is_active == True
        )
    ).first()

    current_program = session.exec(
        select(Program).where(
            Program.id == enrollment.program_id, 
            Program.is_active == True)
        ).first() if enrollment else None

    task_completions = session.exec(
        select(TaskCompletion).where(TaskCompletion.user_id == student_id)
    ).all()

    payments = session.exec(
        select(PaymentLog).where(PaymentLog.user_id == student_id)
    ).all()

    balance = sum(p.amount for p in payments) - sum(c.charge_amount for c in task_completions)

    return {
        "id": user.id,
        "name": f"{user.first_name} {user.last_name}",
        "email": user.email,
        "phone": user.phone_number,
        "program": current_program.title if current_program else None,
        "task_count": len(task_completions),
        "account_balance": balance,
        "tasks": [
            {
                "task_id": t.task_id,
                "flight_time": t.flight_time,
                "charge": t.charge_amount
            } for t in task_completions
        ]
    }

@admin_router.delete("/programs/{program_id}/students/{student_id}")
def remove_student_from_program(program_id: int, student_id: int, session: SessionDep):
    # Find active enrollment
    enrollment = session.exec(
        select(Enrollment)
        .where(Enrollment.user_id == student_id)
        .where(Enrollment.program_id == program_id)
        .where(Enrollment.is_active == True)
    ).first()

    if not enrollment:
        raise HTTPException(status_code=404, detail="Student not enrolled in this program")

    # Soft delete the enrollment
    enrollment.is_active = False
    session.add(enrollment)

    session.commit()

    return {"success": True, "message": "Student removed from program"}

@admin_router.post("/tasks")
def create_task(task_data: TaskCreate, session: SessionDep):
    program = session.get(Program, task_data.program_id)
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    new_task = Task(
        program_id=task_data.program_id,
        title=task_data.title,
        description=task_data.description,
        cost=task_data.cost,
        duration=task_data.duration
    )
    session.add(new_task)
    session.commit()
    session.refresh(new_task)
    return {"success": True, "task": new_task.dict()}

@admin_router.put("/students/{student_id}/update")
def update_student_profile(student_id: int, update_data: StudentUpdate, session: SessionDep):
    user = session.get(User, student_id)
    if not user:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Update only provided fields
    if update_data.first_name is not None:
        user.first_name = update_data.first_name
    if update_data.last_name is not None:
        user.last_name = update_data.last_name
    if update_data.phone_number is not None:
        user.phone_number = update_data.phone_number
    
    session.add(user)
    session.commit()
    
    return {"success": True, "message": "Profile updated successfully"}

@admin_router.get("/tasks")
def list_tasks(session: SessionDep):
    tasks = session.exec(select(Task)).all()
    result = []
    for task in tasks:
        program = session.get(Program, task.program_id)
        result.append({
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "cost": task.cost,
            "duration": task.duration,
            "is_active": task.is_active,
            "program_title": program.title if program else "",
        })
    return result

@admin_router.get("/enrollments/last24h")
def enrollments_last_24h(session: SessionDep):
    since = datetime.utcnow() - timedelta(hours=24)
    enrollments = session.exec(
        select(Enrollment).where(Enrollment.enrolled_at >= since)
    ).all()
    return {"count": len(enrollments)}

@admin_router.post("/tasks/{task_id}/toggle")
def toggle_task_status(task_id: int, session: SessionDep):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.is_active = not task.is_active
    session.add(task)
    session.commit()
    return {"success": True, "is_active": task.is_active}
