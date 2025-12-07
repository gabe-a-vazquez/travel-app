import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.routers import chat

app = FastAPI(
    title="Travel App API",
    description="API for travel itinerary planning with LLM integration",
    version="0.1.0",
)

# Configure CORS for local development and production
allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Add Railway frontend URL if in production
frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    allowed_origins.append(frontend_url)

# In production, allow all origins (you can restrict this later with specific Railway URLs)
allow_origin_regex = None
if os.getenv("RAILWAY_ENVIRONMENT"):
    allow_origin_regex = r"https://.*\.up\.railway\.app"

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=allow_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api")


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
