"""
Chat router - Main chat endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import os
import shutil
from pathlib import Path
import uuid
from datetime import datetime
from app.services.ai_service import AIService
from app.database import get_db
from sqlalchemy.orm import Session

router = APIRouter()

# Create uploads directory if it doesn't exist
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./uploads"))
UPLOAD_DIR.mkdir(exist_ok=True)


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[int] = None
    model: str = "gpt-4"
    system_prompt: Optional[str] = None
    stream: bool = True


class ChatResponse(BaseModel):
    response: str
    conversation_id: int
    model: str
    tokens_used: Optional[int] = None


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """Send a chat message and get response"""
    try:
        ai_service = AIService()
        
        # For streaming, use WebSocket
        if request.stream:
            raise HTTPException(
                status_code=400,
                detail="Use WebSocket endpoint /ws for streaming"
            )
        
        # Non-streaming response
        response_text = ""
        async for chunk in ai_service.stream_chat(
            message=request.message,
            conversation_id=request.conversation_id,
            model=request.model,
            system_prompt=request.system_prompt
        ):
            response_text += chunk
        
        # TODO: Save to database
        # conversation_id = save_message(db, request.message, response_text, request.model)
        
        return ChatResponse(
            response=response_text,
            conversation_id=request.conversation_id or 0,
            model=request.model
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations")
async def get_conversations(db: Session = Depends(get_db)):
    """Get all conversations"""
    from app.services.conversation_service import ConversationService
    conv_service = ConversationService()
    conversations = conv_service.get_all_conversations()
    return {"conversations": conversations}


@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: int, db: Session = Depends(get_db)):
    """Get specific conversation"""
    from app.services.conversation_service import ConversationService
    conv_service = ConversationService()
    conversation = conv_service.get_conversation(conversation_id)
    if conversation:
        return conversation
    raise HTTPException(status_code=404, detail="Conversation not found")


@router.post("/conversations")
async def create_conversation(title: Optional[str] = None, db: Session = Depends(get_db)):
    """Create a new conversation"""
    from app.services.conversation_service import ConversationService
    conv_service = ConversationService()
    conversation = conv_service.create_conversation(title=title)
    return conversation


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: int, db: Session = Depends(get_db)):
    """Delete a conversation"""
    from app.services.conversation_service import ConversationService
    conv_service = ConversationService()
    success = conv_service.delete_conversation(conversation_id)
    if success:
        return {"message": "Conversation deleted"}
    raise HTTPException(status_code=404, detail="Conversation not found")


@router.post("/upload")
async def upload_files(
    files: List[UploadFile] = File(...),
    conversation_id: Optional[int] = Form(None)
):
    """Upload files and images with validation"""
    try:
        # Get upload limits from environment
        max_upload_size = int(os.getenv("MAX_UPLOAD_SIZE", 104857600))  # 100MB default
        allowed_image_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
        allowed_file_types = [
            "application/pdf", "text/plain", "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "text/csv", "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ]

        uploaded_files = []

        for file in files:
            # Validate file size
            file_size = 0
            content = await file.read()
            file_size = len(content)

            if file_size > max_upload_size:
                raise HTTPException(
                    status_code=413,
                    detail=f"File {file.filename} is too large. Maximum size is {max_upload_size // (1024*1024)}MB"
                )

            # Validate file type
            content_type = file.content_type or ""
            if content_type.startswith("image/") and content_type not in allowed_image_types:
                raise HTTPException(
                    status_code=400,
                    detail=f"Image type {content_type} not allowed. Allowed: {', '.join(allowed_image_types)}"
                )
            elif not content_type.startswith("image/") and content_type not in allowed_file_types:
                raise HTTPException(
                    status_code=400,
                    detail=f"File type {content_type} not allowed"
                )

            # Generate unique filename
            file_ext = Path(file.filename).suffix.lower()
            # Additional extension validation
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.pdf', '.txt', '.doc', '.docx', '.csv', '.xlsx']
            if file_ext not in allowed_extensions:
                raise HTTPException(
                    status_code=400,
                    detail=f"File extension {file_ext} not allowed"
                )

            unique_filename = f"{uuid.uuid4()}{file_ext}"
            file_path = UPLOAD_DIR / unique_filename

            # Save file
            with open(file_path, "wb") as buffer:
                buffer.write(content)

            # Determine file type
            file_type = "image" if content_type.startswith("image/") else "file"

            # Create URL (in production, use proper file serving)
            file_url = f"/uploads/{unique_filename}"

            uploaded_files.append({
                "id": str(uuid.uuid4()),
                "type": file_type,
                "name": file.filename,
                "url": file_url,
                "path": str(file_path),
                "size": file_size,
                "content_type": content_type
            })

        return JSONResponse(content={"files": uploaded_files})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


class TTSRequest(BaseModel):
    text: str
    voice: str = "alloy"

@router.post("/tts")
async def text_to_speech(request: TTSRequest):
    """Convert text to speech"""
    try:
        ai_service = AIService()
        audio_bytes = await ai_service.text_to_speech(request.text, request.voice)
        from fastapi.responses import StreamingResponse
        import io

        return StreamingResponse(
            io.BytesIO(audio_bytes),
            media_type="audio/mpeg",
            headers={"Content-Disposition": "attachment; filename=speech.mp3"}
        )
    except Exception as e:
        error_msg = str(e)
        if "insufficient_quota" in error_msg or "quota" in error_msg.lower():
            raise HTTPException(status_code=402, detail="TTS unavailable: OpenAI quota exceeded. Voice output disabled.")
        raise HTTPException(status_code=500, detail=f"TTS failed: {error_msg}")


@router.post("/enhance-image")
async def enhance_image(image_url: str, enhancement_type: str = "upscale"):
    """Enhance an image"""
    try:
        ai_service = AIService()

        # Convert URL to path
        if image_url.startswith("/uploads/"):
            image_path = UPLOAD_DIR / image_url.replace("/uploads/", "")
        else:
            raise HTTPException(status_code=400, detail="Invalid image URL")

        if not image_path.exists():
            raise HTTPException(status_code=404, detail="Image not found")

        enhanced_url = await ai_service.enhance_image(str(image_path), enhancement_type)

        return {"enhanced_url": enhanced_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image enhancement failed: {str(e)}")
