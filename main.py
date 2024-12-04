from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.database.db_connection import init_db
from src.minio.minio_client import create_bucket
from src.utils.routers import image_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("✅ Starting application")
    
    await init_db()
    
    app.state.minio_client = await create_bucket()
    
    yield
    print("⛔ Stopping application")

app = FastAPI(
    title="Vegetable Classification API",
    version="0.1",
    description="This is a simple image classification for Vegetable API",
    lifespan=lifespan
)

app.include_router(image_router, tags=["Image"])