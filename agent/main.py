from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from agent.db.init_db import init_db
from agent.routes.routes import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="agent007", lifespan=lifespan)

app.mount("/static", StaticFiles(directory="agent/static"), name="static")
templates = Jinja2Templates(directory="agent/templates")

app.state.templates = templates

app.include_router(router)
