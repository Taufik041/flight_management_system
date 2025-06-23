from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime


# ---------------------------
# USER TABLE
# ---------------------------
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    first_name: str
    last_name: str
    email: str
    password: str
    phone_number: int
    date_of_birth: datetime
    photo_path: Optional[str] = Field(default=None, description="Path to profile photo")

    enrollments: List["Enrollment"] = Relationship(back_populates="user")
    payment_logs: List["PaymentLog"] = Relationship(back_populates="user")
    task_completions: List["TaskCompletion"] = Relationship(back_populates="user")


# ---------------------------
# PROGRAM TABLE
# ---------------------------
class Program(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: str
    price: float

    enrollments: List["Enrollment"] = Relationship(back_populates="program")
    tasks: List["Task"] = Relationship(back_populates="program")
    payment_logs: List["PaymentLog"] = Relationship(back_populates="program")


# ---------------------------
# ENROLLMENT TABLE
# ---------------------------
class Enrollment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    program_id: int = Field(foreign_key="program.id")
    enrolled_at: datetime = Field(default_factory=datetime.utcnow)

    user: User = Relationship(back_populates="enrollments")
    program: Program = Relationship(back_populates="enrollments")


# ---------------------------
# TASK TABLE
# ---------------------------
class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    program_id: int = Field(foreign_key="program.id")
    title: str
    description: str
    cost: float
    duration: int  # in minutes or hours
    created_at: datetime = Field(default_factory=datetime.utcnow)

    program: Program = Relationship(back_populates="tasks")
    completions: List["TaskCompletion"] = Relationship(back_populates="task")


# ---------------------------
# TASK COMPLETION TABLE
# ---------------------------
class TaskCompletion(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    task_id: int = Field(foreign_key="task.id")
    flight_time: int  # actual minutes/hours flown
    charge_amount: float
    completed_at: datetime = Field(default_factory=datetime.utcnow)

    user: User = Relationship(back_populates="task_completions")
    task: Task = Relationship(back_populates="completions")


# ---------------------------
# PAYMENT LOG TABLE
# ---------------------------
class PaymentLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    program_id: int = Field(foreign_key="program.id")
    amount: float
    paid_at: datetime = Field(default_factory=datetime.utcnow)

    user: User = Relationship(back_populates="payment_logs")
    program: Program = Relationship(back_populates="payment_logs")
