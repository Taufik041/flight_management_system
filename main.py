from logger import logger
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os


app = FastAPI()

app.mount("/static", StaticFiles(directory="./assets/static"), name="static")


@app.get("/favicon.ico")
async def favicon():
    return FileResponse(os.path.join("./assets/static", "favicon.ico"))


@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.get("/one")
def read_one():
    return {"message": "One"}

@app.get("/one2")
def read_one2():
    return {"message": "One2"}