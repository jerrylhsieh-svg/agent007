from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from agent.routes.routes import router

app = FastAPI(title="agent007")

app.mount("/static", StaticFiles(directory="agent/static"), name="static")
templates = Jinja2Templates(directory="agent/templates")

app.state.templates = templates

app.include_router(router)