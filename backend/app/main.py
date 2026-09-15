import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.session import engine, Base
from app.api import routes_health, routes_jobs
from app.core.cleanup import cleanup_old_jobs_loop

# Create database tables
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start cleanup task
    task = asyncio.create_task(cleanup_old_jobs_loop())
    yield
    # Cancel task on shutdown
    task.cancel()

app = FastAPI(title="Transcriber API", version="1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_health.router, prefix="/api", tags=["health"])
app.include_router(routes_jobs.router, prefix="/api", tags=["jobs"])
