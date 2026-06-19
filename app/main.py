from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.config import get_settings
from app.routers import analytics, events, orders

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="Commerce intelligence for growing D2C brands",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(orders.router, prefix="/api/v1")
app.include_router(events.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "app": settings.app_name,
    }


public_dir = Path(__file__).resolve().parents[1] / "public"


@app.get("/")
def serve_index():
    return FileResponse(public_dir / "index.html")


@app.get("/styles.css")
def serve_styles():
    return FileResponse(public_dir / "styles.css")


@app.get("/app.js")
def serve_app_js():
    return FileResponse(public_dir / "app.js")
