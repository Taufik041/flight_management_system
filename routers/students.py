from fastapi import APIRouter

student_router = APIRouter()

@student_router.get("/dashboard")
def dashboard():
    ...
    
@student_router.get("/programs")
def programs():
    ...
    
@student_router.get("/tasks")
def tasks():
    ...
    
@student_router.get("/students")
def students():
    ...