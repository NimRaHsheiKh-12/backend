from fastapi import FastAPI
from .config import settings
from .api import auth
from .api import todo
from .api import chat
from fastapi.middleware.cors import CORSMiddleware
from .database.database import create_db_and_tables
from contextlib import asynccontextmanager
from typing import AsyncGenerator


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup
    create_db_and_tables()
    print("Application started successfully")
    yield
    # Shutdown (if needed)


# Create FastAPI app instance
app = FastAPI(
    title=settings.app_name,
    description="API for Todo Fullstack Application",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware - this should be one of the first middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(todo.router, prefix="/todos", tags=["todos"])
app.include_router(chat.router, tags=["chat"])

@app.get("/")
def read_root():
    return {"message": "Welcome to Todo Fullstack App API"}