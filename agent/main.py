from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from agent.db.init_db import init_db
from agent.db.session import SessionLocal
from agent.learning_models.train_merchant_model import train
from agent.routes.routes import router
from agent.routes.labeling_routes import router as labeling_router
import logging

logger = logging.getLogger(__name__)

def train_models_on_startup() -> None:
    db = SessionLocal()
    try:
        train("transaction", db)
        train("statement", db)
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    try:
        train_models_on_startup()
    except Exception as e:
        logger.warning(f"Not able to generate the artifact due to {e}")
    yield

app = FastAPI(title="agent007", lifespan=lifespan)

app.mount("/static", StaticFiles(directory="agent/static"), name="static")
templates = Jinja2Templates(directory="agent/templates")

app.state.templates = templates

app.include_router(router)
app.include_router(labeling_router)
