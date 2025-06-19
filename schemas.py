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

    applications: List["Application"] = Relationship(back_populates="user")
    payment_logs: List["PaymentLog"] = Relationship(back_populates="user")



class Program(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: str
    price: float

    applications: List["Application"] = Relationship(back_populates="program")
    payment_logs: List["PaymentLog"] = Relationship(back_populates="program")



class Application(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    program_id: int = Field(foreign_key="program.id")
    status: str  # e.g., "pending", "approved", "rejected"
    applied_at: datetime = Field(default_factory=datetime.utcnow)

    user: User = Relationship(back_populates="applications")
    program: Program = Relationship(back_populates="applications")




class PaymentLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    program_id: int = Field(foreign_key="program.id")
    amount: float
    paid_at: datetime = Field(default_factory=datetime.utcnow)

    user: User = Relationship(back_populates="payment_logs")
    program: Program = Relationship(back_populates="payment_logs")