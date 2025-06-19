from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select
from schemas import User, Program, PaymentLog, Enrollment, Task, TaskCompletion
from dotenv import load_dotenv
import os

load_dotenv()

postgres_url = os.environ.get("postgres_url")
if postgres_url is None:
    raise RuntimeError("Environment variable 'postgres_url' is not set.")

engine = create_engine(postgres_url)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]