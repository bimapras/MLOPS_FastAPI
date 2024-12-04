import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from src.database.db_model import Base

load_dotenv()

# Create an async engine
engine = create_async_engine(os.getenv("DATABASE_URL"), echo=True)

# Create an async session
async def get_session() -> AsyncSession:
    async_session = sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=True
    )
    
    async with async_session() as session:
        yield session
        
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)