from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.database.connection import engine, Base, SessionLocal
from app.routes import health, sports, auth, athletes, coaches
from app.services.seed import seed_sports


@asynccontextmanager
async def lifespan(app):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_sports(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="TrainTime API",
    description="API da plataforma esportiva TrainTime",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(sports.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(athletes.router, prefix="/api")
app.include_router(coaches.router, prefix="/api")

frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"
app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
