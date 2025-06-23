from fastapi import APIRouter

admin_router = APIRouter()

@admin_router.get("/dashboard")
def dashboard():
    ...
    
@admin_router.get("/programs")
def programs():
    ...
    
@admin_router.get("/tasks")
def tasks():
    ...
    
@admin_router.get("/students")
def students():
    ...