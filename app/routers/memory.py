"""
Memory router - Memory management
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.services.memory_service import MemoryService

router = APIRouter()


class MemoryRequest(BaseModel):
    key: str
    value: str
    importance: float = 0.5


class MemoryResponse(BaseModel):
    id: int
    key: str
    value: str
    importance: float


@router.post("/", response_model=MemoryResponse)
async def create_memory(request: MemoryRequest):
    """Create a new memory"""
    memory_service = MemoryService()
    memory = await memory_service.create_memory(
        key=request.key,
        value=request.value,
        importance=request.importance
    )
    return memory


@router.get("/search")
async def search_memories(query: str, limit: int = 10):
    """Search memories by query"""
    memory_service = MemoryService()
    memories = await memory_service.search_memories(query, limit)
    return {"memories": memories}


@router.get("/{memory_id}")
async def get_memory(memory_id: int):
    """Get specific memory"""
    memory_service = MemoryService()
    memory = await memory_service.get_memory(memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    return memory

