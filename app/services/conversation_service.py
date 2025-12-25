"""
Conversation Service - Handle conversation and message persistence
"""
from typing import Optional, List, Dict
from app.database import SessionLocal
from app.models.conversation import Conversation, Message
from sqlalchemy.orm import Session
from datetime import datetime


class ConversationService:
    """Service for managing conversations and messages"""
    
    def create_conversation(self, title: Optional[str] = None, user_id: Optional[int] = None) -> Dict:
        """Create a new conversation"""
        db = SessionLocal()
        try:
            conversation = Conversation(
                title=title or "New Chat",
                user_id=user_id
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
            return {
                "id": conversation.id,
                "title": conversation.title,
                "created_at": conversation.created_at.isoformat(),
                "updated_at": conversation.updated_at.isoformat()
            }
        finally:
            db.close()
    
    def get_conversation(self, conversation_id: int) -> Optional[Dict]:
        """Get conversation with messages"""
        db = SessionLocal()
        try:
            conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
            if conversation:
                messages = [
                    {
                        "id": m.id,
                        "role": m.role,
                        "content": m.content,
                        "model": m.model,
                        "created_at": m.created_at.isoformat()
                    }
                    for m in conversation.messages
                ]
                return {
                    "id": conversation.id,
                    "title": conversation.title,
                    "created_at": conversation.created_at.isoformat(),
                    "updated_at": conversation.updated_at.isoformat(),
                    "messages": messages
                }
            return None
        finally:
            db.close()
    
    def get_all_conversations(self, user_id: Optional[int] = None, limit: int = 50) -> List[Dict]:
        """Get all conversations"""
        db = SessionLocal()
        try:
            query = db.query(Conversation)
            if user_id:
                query = query.filter(Conversation.user_id == user_id)
            
            conversations = query.order_by(Conversation.updated_at.desc()).limit(limit).all()
            
            return [
                {
                    "id": conv.id,
                    "title": conv.title or "New Chat",
                    "created_at": conv.created_at.isoformat(),
                    "updated_at": conv.updated_at.isoformat(),
                    "message_count": len(conv.messages)
                }
                for conv in conversations
            ]
        finally:
            db.close()
    
    def save_message(
        self,
        conversation_id: int,
        role: str,
        content: str,
        model: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """Save a message to a conversation"""
        db = SessionLocal()
        try:
            # Update conversation timestamp
            conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
            if not conversation:
                return {"error": "Conversation not found"}
            
            # Auto-generate title from first user message if not set
            if not conversation.title or conversation.title == "New Chat":
                if role == "user" and len(content) > 0:
                    # Use first 50 chars of first message as title
                    title = content[:50] + ("..." if len(content) > 50 else "")
                    conversation.title = title
            
            conversation.updated_at = datetime.utcnow()
            
            # Create message
            message = Message(
                conversation_id=conversation_id,
                role=role,
                content=content,
                model=model or "unknown",
                meta_data=metadata or {}
            )
            db.add(message)
            db.commit()
            db.refresh(message)
            
            return {
                "id": message.id,
                "conversation_id": message.conversation_id,
                "role": message.role,
                "content": message.content,
                "model": message.model,
                "created_at": message.created_at.isoformat()
            }
        finally:
            db.close()
    
    def update_conversation_title(self, conversation_id: int, title: str) -> bool:
        """Update conversation title"""
        db = SessionLocal()
        try:
            conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
            if conversation:
                conversation.title = title
                db.commit()
                return True
            return False
        finally:
            db.close()
    
    def delete_conversation(self, conversation_id: int) -> bool:
        """Delete a conversation"""
        db = SessionLocal()
        try:
            conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
            if conversation:
                db.delete(conversation)
                db.commit()
                return True
            return False
        finally:
            db.close()

    def update_message_content(self, message_id: int, new_content: str) -> bool:
        """Update the content of a specific message"""
        db = SessionLocal()
        try:
            message = db.query(Message).filter(Message.id == message_id).first()
            if message:
                message.content = new_content
                message.updated_at = datetime.utcnow()
                db.commit()
                return True
            return False
        finally:
            db.close()

    def remove_messages_after(self, message_id: int, conversation_id: int) -> bool:
        """Remove all messages after a specific message in a conversation"""
        db = SessionLocal()
        try:
            # Find the message to get its creation time
            message = db.query(Message).filter(
                Message.id == message_id,
                Message.conversation_id == conversation_id
            ).first()

            if not message:
                return False

            # Delete all messages in this conversation that were created after this message
            deleted_count = db.query(Message).filter(
                Message.conversation_id == conversation_id,
                Message.created_at > message.created_at
            ).delete()

            db.commit()
            return True
        finally:
            db.close()

