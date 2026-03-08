"""
Main FastAPI application entry point for Retail Failure Simulator
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from database import init_db
from api import data_ingestion_routes, analysis_routes, transfer_routes
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle handler."""
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully")
    yield
    # Nothing to tear down currently


app = FastAPI(
    title="Retail Failure Simulator API",
    description="AI-powered Retail Failure Simulator & Market Intelligence Platform",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5175", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(data_ingestion_routes.router)
app.include_router(analysis_routes.router)
app.include_router(transfer_routes.router)


@app.get("/")
async def root():
    return {"message": "Retail Failure Simulator API", "status": "running"}


# Authentication endpoint
@app.post("/api/auth/login")
async def login(request: dict):
    """Dummy login endpoint."""
    if request.get("username") == "admin" and request.get("password") == "password":
        return {"token": "dummy_token"}
    raise HTTPException(status_code=401, detail="Invalid credentials")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "retail-failure-simulator"}
