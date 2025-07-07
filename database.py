from typing import Annotated
from datetime import datetime
from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select
from schemas import User, Program, PaymentLog, Enrollment, Task, TaskCompletion
from dotenv import load_dotenv
from utils.security import hash_password
import os

load_dotenv()

postgres_url = os.environ.get("postgres_url")
if postgres_url is None:
    raise RuntimeError("Environment variable 'postgres_url' is not set.")

engine = create_engine(postgres_url)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

    # ✅ Add default admin user if not exists
    with Session(engine) as session:
        existing_admin = session.exec(
            select(User).where(User.email == "admin@example.com")
        ).first()

        if not existing_admin:
            admin_user = User(
                first_name="Admin",
                last_name="User",
                email="admin@example.com",
                password=hash_password("admin"),
                phone_number="0000000000",
                date_of_birth=datetime(2000, 1, 1),
                is_active=True
            )
            session.add(admin_user)
            session.commit()



def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]