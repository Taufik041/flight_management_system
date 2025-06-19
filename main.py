from logger import logger
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from database import engine, SessionDep, create_db_and_tables
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        create_db_and_tables()
        yield
    finally:
        logger.info("Application shutdown complete.")
        engine.dispose()


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="./assets/static"), name="static")


@app.get("/favicon.ico")
async def favicon():
    return FileResponse(os.path.join("./assets/static", "favicon.ico"))


@app.get("/")
def read_root():
   return {"message": "Hello World"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="localhost", reload=True, port=8000)