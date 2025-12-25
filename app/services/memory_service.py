"""
Memory Service - Long-term memory management
"""
from typing import List, Dict, Optional
from app.database import SessionLocal
from app.models.memory import Memory
from sqlalchemy import or_


class MemoryService:
    """Service for managing AI agent memory"""
    
    async def create_memory(
        self,
        key: str,
        value: str,
        importance: float = 0.5,
        user_id: Optional[int] = None
    ) -> Dict:
        """Create a new memory"""
        db = SessionLocal()
        try:
            memory = Memory(
                key=key,
                value=value,
                importance=importance,
                user_id=user_id
            )
            db.add(memory)
            db.commit()
            db.refresh(memory)
            return {
                "id": memory.id,
                "key": memory.key,
                "value": memory.value,
                "importance": memory.importance
            }
        finally:
            db.close()
    
    async def search_memories(
        self,
        query: str,
        limit: int = 10,
        user_id: Optional[int] = None
    ) -> List[Dict]:
        """Search memories by query"""
        db = SessionLocal()
        try:
            memories = db.query(Memory).filter(
                or_(
                    Memory.key.contains(query),
                    Memory.value.contains(query)
                )
            )
            
            if user_id:
                memories = memories.filter(Memory.user_id == user_id)
            
            memories = memories.order_by(Memory.importance.desc()).limit(limit).all()
            
            return [
                {
                    "id": m.id,
                    "key": m.key,
                    "value": m.value,
                    "importance": m.importance
                }
                for m in memories
            ]
        finally:
            db.close()
    
    async def get_memory(self, memory_id: int) -> Optional[Dict]:
        """Get specific memory"""
        db = SessionLocal()
        try:
            memory = db.query(Memory).filter(Memory.id == memory_id).first()
            if memory:
                return {
                    "id": memory.id,
                    "key": memory.key,
                    "value": memory.value,
                    "importance": memory.importance
                }
            return None
        finally:
            db.close()

