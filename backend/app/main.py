import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.auth.router import router as auth_router
from app.trends.router import router as trends_router
from app.scrapers.discovery import load_seed_keywords
from app.scheduler.jobs import start_scheduler, stop_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(title="Fashion Trend Forecaster", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(trends_router)


@app.on_event("startup")
def startup():
    init_db()
    load_seed_keywords()
    start_scheduler()


@app.on_event("shutdown")
def shutdown():
    stop_scheduler()


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
