from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict

app = FastAPI(
    title="BackLogAI API",
    description="Intelligent Backlog Generator & Prioritization System",
    version="0.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root() -> Dict[str, str]:
    return {
        "status": "online",
        "message": "BackLogAI API is running! 🚀"
    }

@app.get("/health")
async def health_check() -> Dict[str, str]:
    return {"status": "ok"}
