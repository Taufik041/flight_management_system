from logger import logger
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from database import engine, SessionDep, create_db_and_tables
from contextlib import asynccontextmanager
from routers.admin import admin_router
from routers.students import student_router
from routers.auth import auth_router
from tasks.scheduler import scheduler
from dotenv import load_dotenv
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        logger.info("Application startup initiated")
        create_db_and_tables()
        scheduler.start()
        load_dotenv()
        logger.info("Database tables created")
        yield
    finally:
        logger.info("Application shutdown complete.")
        engine.dispose()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.mount("/static", StaticFiles(directory="./assets/static"), name="static")
app.mount("/media", StaticFiles(directory="media"), name="media")


app.include_router(admin_router, prefix="/admin", tags=["admin"])
app.include_router(student_router, prefix="/student", tags=["student"])
app.include_router(auth_router, prefix="/auth", tags=["auth"])


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"{request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"{response.status_code} {request.method} {request.url.path}")
    return response


@app.get("/favicon.ico")
async def favicon():
    return FileResponse(os.path.join("./assets/static", "favicon.ico"))


@app.get("/")
def read_root():
   return {"message": "Hello World"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="localhost",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True
    )
