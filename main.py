from logger import logger
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from database import engine, SessionDep, create_db_and_tables
from contextlib import asynccontextmanager
from routers.admin import admin_router
from routers.students import student_router
from routers.auth import auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        create_db_and_tables()
        yield
    finally:
        logger.info("Application shutdown complete.")
        engine.dispose()


app = FastAPI(lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="./assets/static"), name="static")

app.include_router(admin_router, prefix="/admin", tags=["admin"])
app.include_router(student_router, prefix="/student", tags=["student"])
app.include_router(auth_router, prefix="/auth", tags=["auth"])


@app.get("/favicon.ico")
async def favicon():
    return FileResponse(os.path.join("./assets/static", "favicon.ico"))


@app.get("/")
def read_root():
   return {"message": "Hello World"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="localhost", reload=True, port=8000)