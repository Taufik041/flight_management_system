from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from logger import logger
import os


app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/favicon.ico")
async def favicon():
    return FileResponse(os.path.join("static", "favicon.ico"))


@app.get("/")
def read_root():
    logger.info("Root endpoint accessed")
    return {"message": "Hello World"}

