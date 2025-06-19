from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime

class User(SQLModel, table=True):
    id: Optional[int] = Field(
        default=None,
        primary_key=True,
        description="8-digit student ID or admin ID",
    )
    name: str
    email: str
    password_hash: str
    phone_number: int

    enrollments: List["Enrollment"] = Relationship(back_populates="user")
    payment_logs: List["PaymentLog"] = Relationship(back_populates="user")



class Program(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: str
    price: float

    enrollments: List["Enrollment"] = Relationship(back_populates="program")
    payment_logs: List["PaymentLog"] = Relationship(back_populates="program")



class Enrollment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    program_id: int = Field(foreign_key="program.id")
    enrolled_at: datetime = Field(default_factory=datetime.utcnow)

    user: User = Relationship(back_populates="enrollments")
    program: Program = Relationship(back_populates="enrollments")




class PaymentLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    program_id: int = Field(foreign_key="program.id")
    amount: float
    paid_at: datetime = Field(default_factory=datetime.utcnow)

    user: User = Relationship(back_populates="payment_logs")
    program: Program = Relationship(back_populates="payment_logs")



class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    program_id: int = Field(foreign_key="program.id")
    title: str
    cost: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)

    completions: List["TaskCompletion"] = Relationship(back_populates="task")



class TaskCompletion(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    task_id: int = Field(foreign_key="task.id")
    completed_at: datetime = Field(default_factory=datetime.utcnow)
    flight_time: int  # in minutes or hours
    charge_amount: float

    user: User = Relationship()
    task: Task = Relationship(back_populates="completions")
