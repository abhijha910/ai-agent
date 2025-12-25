"""
WebSocket manager for real-time communication
"""
from fastapi import WebSocket
from typing import List, Dict
import json
import asyncio


class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.user_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

    async def handle_message(self, websocket: WebSocket, data: dict):
        """Handle incoming WebSocket messages"""
        message_type = data.get("type")
        
        if message_type == "chat":
            # Handle chat message
            from app.services.ai_service import AIService
            from app.services.conversation_service import ConversationService
            
            ai_service = AIService()
            conv_service = ConversationService()
            
            # Get or create conversation
            conversation_id = data.get("conversation_id")
            if not conversation_id:
                # Create new conversation
                conv = conv_service.create_conversation()
                conversation_id = conv["id"]
                # Send conversation ID to client
                await self.send_personal_message({
                    "type": "conversation_created",
                    "conversation_id": conversation_id
                }, websocket)
            
            # Save user message
            user_message = data.get("message", "")
            attachments = data.get("attachments", [])
            
            # Save attachments in message metadata
            message_metadata = {}
            if attachments:
                message_metadata["attachments"] = attachments
            
            conv_service.save_message(
                conversation_id=conversation_id,
                role="user",
                content=user_message,
                model=data.get("model", "gemini-2.5-flash"),
                metadata=message_metadata if message_metadata else None
            )
            
            # Send acknowledgment
            await self.send_personal_message({
                "type": "status",
                "status": "processing"
            }, websocket)
            
            # Stream response - use gpt-3.5-turbo as default for better reliability
            requested_model = data.get("model", "gpt-3.5-turbo")
            full_response = ""
            try:
                async for chunk in ai_service.stream_chat(
                    message=user_message,
                    conversation_id=conversation_id,
                    model=requested_model,
                    attachments=attachments
                ):
                    full_response += chunk
                    await self.send_personal_message({
                        "type": "chunk",
                        "content": chunk
                    }, websocket)
                
                # Save assistant response
                conv_service.save_message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=full_response,
                    model=requested_model
                )
                
                await self.send_personal_message({
                    "type": "complete",
                    "conversation_id": conversation_id
                }, websocket)
            except Exception as e:
                error_message = str(e)
                if "quota" in error_message.lower() or "billing" in error_message.lower():
                    user_friendly_error = "⚠️ API Quota Exceeded\n\nYour AI provider has run out of credits. Please:\n\n1. Add billing/credits to your OpenAI account\n2. Or switch to Gemini model\n3. Check your API key is valid\n\n💡 Try sending a message again after adding credits!"
                elif "rate" in error_message.lower():
                    user_friendly_error = "⚠️ Rate Limit Hit\n\nToo many requests. Please wait 30 seconds and try again."
                elif "key" in error_message.lower() or "auth" in error_message.lower():
                    user_friendly_error = "⚠️ API Key Error\n\nPlease check your API keys in the .env file:\n\n- OPENAI_API_KEY\n- GOOGLE_API_KEY\n\nKeys may be invalid or expired."
                else:
                    user_friendly_error = f"❌ AI Error\n\n{error_message}\n\n💡 Try switching models or check your API keys."

                await self.send_personal_message({
                    "type": "error",
                    "message": user_friendly_error
                }, websocket)
                await self.send_personal_message({
                    "type": "complete",
                    "conversation_id": conversation_id
                }, websocket)

        elif message_type == "edit":
            # Handle message editing
            from app.services.ai_service import AIService
            from app.services.conversation_service import ConversationService

            ai_service = AIService()
            conv_service = ConversationService()

            message_id = data.get("message_id")
            new_content = data.get("new_content", "")
            conversation_id = data.get("conversation_id")
            model = data.get("model", "gpt-3.5-turbo")

            if not conversation_id or not message_id:
                await self.send_personal_message({
                    "type": "error",
                    "message": "❌ Invalid edit request: missing conversation_id or message_id"
                }, websocket)
                return

            # Update the user message in database
            success = conv_service.update_message_content(message_id, new_content)
            if not success:
                await self.send_personal_message({
                    "type": "error",
                    "message": "❌ Failed to update message"
                }, websocket)
                return

            # Remove all messages after the edited message
            conv_service.remove_messages_after(message_id, conversation_id)

            # Send acknowledgment
            await self.send_personal_message({
                "type": "status",
                "status": "processing"
            }, websocket)

            # Regenerate AI response based on edited conversation
            try:
                # Get the conversation history up to the edited message
                conversation = conv_service.get_conversation(conversation_id)
                if not conversation or not conversation.get("messages"):
                    await self.send_personal_message({
                        "type": "error",
                        "message": "❌ Conversation not found or empty"
                    }, websocket)
                    return

                # Find the edited message and get all messages up to it
                messages = conversation["messages"]
                edited_message_index = None
                for i, msg in enumerate(messages):
                    if str(msg["id"]) == str(message_id):
                        edited_message_index = i
                        break

                if edited_message_index is None:
                    await self.send_personal_message({
                        "type": "error",
                        "message": "❌ Edited message not found"
                    }, websocket)
                    return

                # Get conversation history up to and including the edited message
                conversation_history = messages[:edited_message_index + 1]

                # Build the prompt from the conversation history
                conversation_text = ""
                for msg in conversation_history:
                    role = msg["role"]
                    content = msg["content"]
                    conversation_text += f"{role}: {content}\n"

                # Generate new AI response
                full_response = ""
                async for chunk in ai_service.stream_chat(
                    message=conversation_text,
                    conversation_id=conversation_id,
                    model=model
                ):
                    full_response += chunk
                    await self.send_personal_message({
                        "type": "chunk",
                        "content": chunk
                    }, websocket)

                # Save the new AI response
                conv_service.save_message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=full_response,
                    model=model
                )

                await self.send_personal_message({
                    "type": "complete",
                    "conversation_id": conversation_id
                }, websocket)
            except Exception as e:
                error_message = str(e)
                if "quota" in error_message.lower() or "billing" in error_message.lower():
                    user_friendly_error = "⚠️ API Quota Exceeded\n\nYour AI provider has run out of credits. Please:\n\n1. Add billing/credits to your OpenAI account\n2. Or switch to Gemini model\n3. Check your API key is valid\n\n💡 Try sending a message again after adding credits!"
                elif "rate" in error_message.lower():
                    user_friendly_error = "⚠️ Rate Limit Hit\n\nToo many requests. Please wait 30 seconds and try again."
                elif "key" in error_message.lower() or "auth" in error_message.lower():
                    user_friendly_error = "⚠️ API Key Error\n\nPlease check your API keys in the .env file:\n\n- OPENAI_API_KEY\n- GOOGLE_API_KEY\n\nKeys may be invalid or expired."
                else:
                    user_friendly_error = f"❌ Edit Error\n\n{error_message}\n\n💡 Try again or check your connection."

                await self.send_personal_message({
                    "type": "error",
                    "message": user_friendly_error
                }, websocket)
                await self.send_personal_message({
                    "type": "complete",
                    "conversation_id": conversation_id
                }, websocket)

            except Exception as e:
                error_message = str(e)
                if "quota" in error_message.lower() or "billing" in error_message.lower():
                    user_friendly_error = "⚠️ API Quota Exceeded\n\nYour AI provider has run out of credits. Please:\n\n1. Add billing/credits to your OpenAI account\n2. Or switch to Gemini model\n3. Check your API key is valid\n\n💡 Try sending a message again after adding credits!"
                elif "rate" in error_message.lower():
                    user_friendly_error = "⚠️ Rate Limit Hit\n\nToo many requests. Please wait 30 seconds and try again."
                elif "key" in error_message.lower() or "auth" in error_message.lower():
                    user_friendly_error = "⚠️ API Key Error\n\nPlease check your API keys in the .env file:\n\n- OPENAI_API_KEY\n- GOOGLE_API_KEY\n\nKeys may be invalid or expired."
                else:
                    user_friendly_error = f"❌ Edit Error\n\n{error_message}\n\n💡 Try again or check your connection."

                await self.send_personal_message({
                    "type": "error",
                    "message": user_friendly_error
                }, websocket)
                await self.send_personal_message({
                    "type": "complete",
                    "conversation_id": conversation_id
                }, websocket)
            except Exception as e:
                error_message = str(e)
                # Provide user-friendly error messages
                if "quota" in error_message.lower() or "billing" in error_message.lower():
                    user_friendly_error = "⚠️ API Quota Exceeded\n\nYour AI provider has run out of credits. Please:\n\n1. Add billing/credits to your OpenAI account\n2. Or switch to Gemini model\n3. Check your API key is valid\n\n💡 Try sending a message again after adding credits!"
                elif "rate" in error_message.lower():
                    user_friendly_error = "⚠️ Rate Limit Hit\n\nToo many requests. Please wait 30 seconds and try again."
                elif "key" in error_message.lower() or "auth" in error_message.lower():
                    user_friendly_error = "⚠️ API Key Error\n\nPlease check your API keys in the .env file:\n\n- OPENAI_API_KEY\n- GOOGLE_API_KEY\n\nKeys may be invalid or expired."
                elif "network" in error_message.lower() or "connection" in error_message.lower():
                    user_friendly_error = "⚠️ Network Error\n\nConnection failed. Please check your internet and try again."
                else:
                    user_friendly_error = f"❌ AI Error\n\n{error_message}\n\n💡 Try switching models or check your API keys."

                await self.send_personal_message({
                    "type": "error",
                    "message": user_friendly_error
                }, websocket)
                await self.send_personal_message({
                    "type": "complete",
                    "conversation_id": conversation_id
                }, websocket)
