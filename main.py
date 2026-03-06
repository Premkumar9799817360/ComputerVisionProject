import logging
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from backend.routers.session_router import router as session_router
from backend.routers.ws_router import router as ws_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SightFlow",
    description="Vision-Powered AI for Intelligent Proctoring & Visual Monitoring",
    version="1.0.0",
)

REPORT_DIR = "reports"

os.makedirs(REPORT_DIR, exist_ok=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
templates = Jinja2Templates(directory="frontend/templates")

# Include routers
app.include_router(session_router)
app.include_router(ws_router)


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    # return {"message": "Welcome to SightFlow - AI Proctoring & Visual Monitoring System!"}
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/monitor", response_class=HTMLResponse)
def monitor_page(request: Request):
    return templates.TemplateResponse("monitor.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/health")
def health():
    return {"status": "ok", "service": "SightFlow"}