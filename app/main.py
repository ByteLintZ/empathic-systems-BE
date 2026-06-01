from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.routing import APIRouter
import logging
import asyncio
import time
import os

from contextlib import asynccontextmanager
from dotenv import load_dotenv

from .routes.chat import router as chat_router
from .routes.token import router as token_router
from .utils.logger import setup_logging
from .services.request_queue import request_queue

# Load environment variables
load_dotenv()

# Setup logging
setup_logging()

# Get environment settings
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
IS_PRODUCTION = ENVIRONMENT == "production"

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    env_emoji = "🏭" if IS_PRODUCTION else "🔧"
    logging.info(f"{env_emoji} AI Chatbot Platform API starting up in {ENVIRONMENT} mode...")
    logging.info("📊 NO QUEUE MODE: Direct Groq API execution for maximum speed!")
    logging.info("🎯 User limits: 3 prompts per user per day")

    yield
    logging.info("🛑 AI Chatbot Platform API shutting down...")

app = FastAPI(
    title="AI Chatbot Platform",
    description="An empathetic AI chatbot that responds based on user emotions with improved load handling",
    version="1.1.0",
    lifespan=lifespan
)

# Add GZip
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Configure CORS
frontend_url = os.getenv("FRONTEND_URL")
extra_cors = os.getenv("EXTRA_CORS_ORIGINS")

allowed_origins = []
if frontend_url:
    allowed_origins.append(frontend_url)
if extra_cors:
    allowed_origins.extend([origin.strip() for origin in extra_cors.split(",") if origin.strip()])

if not allowed_origins:
    allowed_origins = ["*"]
    if IS_PRODUCTION:
        logging.warning("⚠️ No CORS origins configured for production! Defaulting to '*'. Please set FRONTEND_URL in .env.")

logging.info(f"✅ Allowed Origins: {allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Explicit preflight OPTIONS handler
@app.options("/{full_path:path}")
async def preflight_handler(full_path: str, request: Request):
    logging.debug(f"Preflight request to {request.url}")
    return JSONResponse(
        status_code=200,
        content={"message": "Preflight OK"},
        headers={
            "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "*, ngrok-skip-browser-warning",
        }
    )

# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_id = int(time.time())
    logging.error(f"Global exception [{error_id}] on {request.url}: {exc}")

    if IS_PRODUCTION:
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "message": "The server encountered an error while processing your request",
                "type": "server_error",
                "error_id": error_id
            }
        )
    else:
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "message": str(exc),
                "type": "server_error",
                "error_id": error_id
            }
        )

# Timeout exception handler
@app.exception_handler(asyncio.TimeoutError)
async def timeout_exception_handler(request: Request, exc: asyncio.TimeoutError):
    logging.warning(f"Request timeout on {request.url}")
    return JSONResponse(
        status_code=504,
        content={
            "error": "Request timeout",
            "message": "The request took too long to process",
            "type": "timeout_error"
        }
    )

# Routers
app.include_router(chat_router, prefix="/api/v1", tags=["chat"])
app.include_router(token_router, prefix="/api/v1", tags=["token"])

@app.get("/")
async def root():
    return {
        "message": "Welcome to AI Chatbot Platform API",
        "version": "1.0.0",
        "endpoints": {
            "chat": "/api/v1/chat",
            "health": "/api/v1/health",
            "emotions": "/api/v1/emotions"
        }
    }

@app.get("/api/v1/health")
async def health_check():
    stats = request_queue.get_stats()
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "queue_stats": stats,
        "server": "running"
    }

@app.get("/api/v1/queue/stats")
async def get_queue_stats():
    return request_queue.get_stats()
