import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.expenses import router as expenses_router
from app.api.health import router as health_router
from app.api.categories import router as categories_router
from app.api.receipts import router as receipts_router

app = FastAPI(title="Шурале — Финансовый трекер")

receipts_dir = os.getenv("RECEIPTS_DIR", "/data/receipts")
Path(receipts_dir).mkdir(parents=True, exist_ok=True)
app.mount("/receipts", StaticFiles(directory=receipts_dir), name="receipts")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(categories_router)
app.include_router(expenses_router)
app.include_router(receipts_router)
