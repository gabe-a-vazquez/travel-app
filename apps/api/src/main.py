from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.routers import chat

app = FastAPI(
    title="Travel App API",
    description="API for travel itinerary planning with LLM integration",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api")


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
