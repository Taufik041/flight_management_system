from pydantic import BaseModel
from typing import Optional

# Request body model
class ProgramCreate(BaseModel):
    title: str
    description: str
    price: float
    
class TaskCreate(BaseModel):
    title: str
    description: str
    cost: float
    duration: int  # minutes
    
class TaskUpdate(BaseModel):
    title: Optional[str]
    description: Optional[str]
    cost: Optional[float]
    duration: Optional[int]