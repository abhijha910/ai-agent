"""
Main FastAPI application for Advanced AI Agent
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import uvicorn
from dotenv import load_dotenv
import os
from pathlib import Path

from app.routers import chat, agents, plugins, memory, tools
from app.services.websocket_manager import WebSocketManager
from app.database import init_db

load_dotenv()

# Create uploads directory
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./uploads"))
UPLOAD_DIR.mkdir(exist_ok=True)

# Initialize WebSocket manager
ws_manager = WebSocketManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    print("Starting AI Agent Server...")
    try:
        init_db()
        print("Database initialized")
    except Exception as e:
        print(f"Database initialization warning: {e}")
    print("Server ready!")
    print(f"WebSocket endpoint: ws://localhost:8000/ws")
    print(f"API docs: http://localhost:8000/docs")
    yield
    # Shutdown
    print("Shutting down...")


app = FastAPI(
    title="Advanced AI Agent API",
    description="Next-generation AI agent with advanced features",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url],  # Allow only frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
app.include_router(plugins.router, prefix="/api/plugins", tags=["plugins"])
app.include_router(memory.router, prefix="/api/memory", tags=["memory"])
app.include_router(tools.router, prefix="/api/tools", tags=["tools"])

# Serve uploaded files
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")


@app.get("/")
async def root():
    return {
        "message": "Advanced AI Agent API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time chat"""
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            await ws_manager.handle_message(websocket, data)
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )
