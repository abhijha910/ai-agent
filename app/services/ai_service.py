"""
AI Service - Multi-model AI integration
"""
import os
from typing import AsyncGenerator, Optional, Dict, List
from pathlib import Path
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
try:
    import google.generativeai as genai
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False
from dotenv import load_dotenv

load_dotenv()

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./uploads"))


class AIService:
    """Unified AI service supporting multiple providers"""
    
    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY")) if os.getenv("OPENAI_API_KEY") else None
        self.anthropic_client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY")) if os.getenv("ANTHROPIC_API_KEY") else None
        self.groq_client = AsyncOpenAI(
            api_key=os.getenv("GROQ_API_KEY"),
            base_url="https://api.groq.com/openai/v1"
        ) if os.getenv("GROQ_API_KEY") else None

        if GOOGLE_AVAILABLE and os.getenv("GOOGLE_API_KEY"):
            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
            # Use gemini-2.5-flash (latest fast model) or gemini-flash-latest
            try:
                self.gemini_model = genai.GenerativeModel('gemini-2.5-flash')
            except:
                try:
                    self.gemini_model = genai.GenerativeModel('gemini-flash-latest')
                except:
                    # Fallback to any available model
                    self.gemini_model = genai.GenerativeModel('gemini-pro-latest')
        else:
            self.gemini_model = None

    async def stream_chat(
        self,
        message: str,
        conversation_id: Optional[int] = None,
        model: str = "gpt-4",
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict]] = None,
        attachments: Optional[List[Dict]] = None
    ) -> AsyncGenerator[str, None]:
        """Stream chat response from selected model with intelligent fallback"""

        # Get conversation history
        history = await self._get_conversation_history(conversation_id)

        # Process attachments (images) if any
        if attachments:
            images = [att for att in attachments if att.get("type") == "image"]
            if images and (model.startswith("gemini") or "gemini" in model.lower() or not self.openai_client):
                # Use Gemini for image analysis
                try:
                    async for chunk in self._stream_gemini_with_images(message, history, images, system_prompt):
                        yield chunk
                    return
                except Exception as e:
                    if "quota" in str(e).lower() or "billing" in str(e).lower():
                        yield "⚠️ Gemini API quota exceeded. Trying OpenAI as fallback...\n\n"
                    else:
                        yield f"❌ Gemini error: {str(e)}. Trying OpenAI...\n\n"

        # Intelligent fallback logic with retry
        models_to_try = []

        # Primary model first
        if (model.startswith("gpt") or "gpt" in model.lower()) and self.openai_client:
            models_to_try.append(("openai", model))
        elif (model.startswith("claude") or "claude" in model.lower()) and self.anthropic_client:
            models_to_try.append(("anthropic", model))
        elif (model.startswith("gemini") or "gemini" in model.lower()) and self.gemini_model:
            models_to_try.append(("gemini", model))

        # Add fallbacks - focus on reliable providers
        if self.gemini_model and ("gemini", "gemini-2.5-flash") not in [(m[0], m[1]) for m in models_to_try]:
            models_to_try.append(("gemini", "gemini-2.5-flash"))
        if self.openai_client and ("openai", "gpt-3.5-turbo") not in [(m[0], m[1]) for m in models_to_try]:
            models_to_try.append(("openai", "gpt-3.5-turbo"))
        if self.gemini_model and ("gemini", "gemini-2.5-flash") not in [(m[0], m[1]) for m in models_to_try]:
            models_to_try.append(("gemini", "gemini-2.5-flash"))
        if self.openai_client and ("openai", "gpt-3.5-turbo") not in [(m[0], m[1]) for m in models_to_try]:
            models_to_try.append(("openai", "gpt-3.5-turbo"))
        if self.anthropic_client and ("anthropic", "claude-3-haiku") not in [(m[0], m[1]) for m in models_to_try]:
            models_to_try.append(("anthropic", "claude-3-haiku"))

        for provider, model_name in models_to_try:
            try:
                if provider == "openai":
                    async for chunk in self._stream_openai(message, history, model_name, system_prompt, tools):
                        yield chunk
                elif provider == "anthropic":
                    async for chunk in self._stream_anthropic(message, history, model_name, system_prompt, tools):
                        yield chunk
                elif provider == "groq":
                    async for chunk in self._stream_groq(message, history, model_name, system_prompt, tools):
                        yield chunk
                elif provider == "gemini":
                    if attachments and images:
                        async for chunk in self._stream_gemini_with_images(message, history, images, system_prompt):
                            yield chunk
                    else:
                        async for chunk in self._stream_gemini(message, history, system_prompt):
                            yield chunk
                return  # Success, exit
            except Exception as e:
                error_msg = str(e).lower()
                if "quota" in error_msg or "billing" in error_msg or "insufficient" in error_msg:
                    yield f"⚠️ {provider.upper()} API quota exceeded. Trying next provider...\n\n"
                    continue
                elif "rate" in error_msg:
                    yield f"⚠️ {provider.upper()} rate limit hit. Retrying in 2 seconds...\n\n"
                    import asyncio
                    await asyncio.sleep(2)
                    continue
                else:
                    yield f"❌ {provider.upper()} error: {str(e)}. Trying next provider...\n\n"
                    continue

        # All providers failed
        yield "❌ All AI providers failed. Please check your API keys and billing status.\n\n💡 Try:\n- Adding credits to OpenAI\n- Checking Google AI Studio billing\n- Verifying API keys are correct"

    async def _stream_openai(
        self,
        message: str,
        history: List[Dict],
        model: str,
        system_prompt: Optional[str],
        tools: Optional[List[Dict]]
    ) -> AsyncGenerator[str, None]:
        """Stream from OpenAI"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.extend(history)
        messages.append({"role": "user", "content": message})
        
        stream = await self.openai_client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            stream=True
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def _stream_anthropic(
        self,
        message: str,
        history: List[Dict],
        model: str,
        system_prompt: Optional[str],
        tools: Optional[List[Dict]]
    ) -> AsyncGenerator[str, None]:
        """Stream from Anthropic Claude"""
        messages = history + [{"role": "user", "content": message}]

        async with self.anthropic_client.messages.stream(
            model=model,
            max_tokens=4096,
            system=system_prompt or "",
            messages=messages,
            tools=tools
        ) as stream:
            async for text in stream.text_stream:
                yield text

    async def _stream_groq(
        self,
        message: str,
        history: List[Dict],
        model: str,
        system_prompt: Optional[str],
        tools: Optional[List[Dict]]
    ) -> AsyncGenerator[str, None]:
        """Stream from Groq"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.extend(history)
        messages.append({"role": "user", "content": message})

        stream = await self.groq_client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            stream=True
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def _stream_gemini(
        self,
        message: str,
        history: List[Dict],
        system_prompt: Optional[str]
    ) -> AsyncGenerator[str, None]:
        """Stream from Google Gemini"""
        if not self.gemini_model:
            yield "Gemini model not available. Please check API key."
            return
        
        try:
            # Create a new model instance using the latest available model
            model_name = 'gemini-2.5-flash'
            try:
                current_model = genai.GenerativeModel(model_name)
            except:
                try:
                    current_model = genai.GenerativeModel('gemini-flash-latest')
                    model_name = 'gemini-flash-latest'
                except:
                    # Use the initialized model as fallback
                    current_model = self.gemini_model
            
            # Convert history to Gemini format
            chat = current_model.start_chat(history=[])
            
            full_prompt = message
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{message}"
            
            # Gemini streaming (synchronous API)
            response = chat.send_message(full_prompt, stream=True)
            
            for chunk in response:
                if hasattr(chunk, 'text') and chunk.text:
                    yield chunk.text
        except Exception as e:
            yield f"Error with Gemini: {str(e)}. Please check your API key and model availability."

    async def _get_conversation_history(self, conversation_id: Optional[int]) -> List[Dict]:
        """Get conversation history from database"""
        if not conversation_id:
            return []

        try:
            from app.database import SessionLocal
            from app.models.conversation import Message

            db = SessionLocal()
            messages = db.query(Message).filter(
                Message.conversation_id == conversation_id
            ).order_by(Message.created_at).all()

            history = []
            for msg in messages:
                history.append({
                    "role": msg.role,
                    "content": msg.content
                })

            db.close()
            return history
        except Exception as e:
            print(f"Error loading conversation history: {e}")
            return []

    async def generate_image(self, prompt: str, model: str = "dall-e-3") -> str:
        """Generate image from prompt"""
        if model == "dall-e-3" and self.openai_client:
            response = await self.openai_client.images.generate(
                model=model,
                prompt=prompt,
                n=1,
                size="1024x1024"
            )
            return response.data[0].url
        else:
            return "Image generation not available"

    async def _stream_gemini_with_images(
        self,
        message: str,
        history: List[Dict],
        images: List[Dict],
        system_prompt: Optional[str]
    ) -> AsyncGenerator[str, None]:
        """Stream from Gemini with image support"""
        if not self.gemini_model:
            yield "Gemini model not available. Please check API key."
            return
        
        try:
            from PIL import Image
            
            # Use gemini-pro-vision or latest flash model with vision support
            # Try multiple model names in order of preference
            vision_model = None
            model_names = [
                'gemini-1.5-pro-latest',  # Latest stable with vision
                'gemini-1.5-flash-latest',  # Flash version with vision
                'gemini-pro-vision',  # Older vision model
                'models/gemini-1.5-pro-latest',  # With models/ prefix
                'models/gemini-1.5-flash-latest',
            ]
            
            for model_name in model_names:
                try:
                    vision_model = genai.GenerativeModel(model_name)
                    break  # If successful, use this model
                except Exception as model_error:
                    continue  # Try next model
            
            # If no vision model works, use the default gemini model
            if not vision_model:
                vision_model = self.gemini_model
            
            # Prepare content with images
            content_parts = []
            if system_prompt:
                content_parts.append(system_prompt + "\n\n")
            content_parts.append(message)
            
            for img in images:
                # Get image path from attachment
                img_url = img.get("url", "")
                if img_url.startswith("/uploads/"):
                    img_path = UPLOAD_DIR / img_url.replace("/uploads/", "")
                elif img.get("path"):
                    img_path = Path(img.get("path"))
                else:
                    continue
                
                if img_path.exists():
                    img_file = Image.open(img_path)
                    content_parts.append(img_file)
            
            # Generate response
            response = vision_model.generate_content(
                content_parts,
                stream=True
            )
            
            for chunk in response:
                if hasattr(chunk, 'text') and chunk.text:
                    yield chunk.text
        except Exception as e:
            yield f"Error processing image: {str(e)}. Make sure Pillow is installed: pip install Pillow"

    async def analyze_image(self, image_url: str, prompt: str) -> str:
        """Analyze image with vision model"""
        if self.openai_client:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": image_url}}
                        ]
                    }
                ]
            )
            return response.choices[0].message.content
        return "Image analysis not available"

    async def text_to_speech(self, text: str, voice: str = "alloy") -> bytes:
        """Convert text to speech using OpenAI TTS with fallback"""
        if not self.openai_client:
            raise Exception("OpenAI client not available for TTS. Please add OPENAI_API_KEY to your .env file.")

        try:
            response = await self.openai_client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text
            )
            return b''.join([chunk async for chunk in response.aiter_bytes()])
        except Exception as e:
            error_msg = str(e).lower()
            if "quota" in error_msg or "billing" in error_msg or "insufficient" in error_msg:
                raise Exception("TTS unavailable: OpenAI quota exceeded. Please add credits to your OpenAI account.")
            elif "rate" in error_msg:
                raise Exception("TTS rate limit exceeded. Please wait a moment and try again.")
            else:
                raise Exception(f"TTS failed: {str(e)}")

    async def enhance_image(self, image_path: str, enhancement_type: str = "upscale") -> str:
        """Enhance image using AI"""
        try:
            from PIL import Image, ImageFilter, ImageEnhance
            import os

            img = Image.open(image_path)

            if enhancement_type == "upscale":
                # Use AI-powered upscaling with better quality
                # First apply some preprocessing
                img = img.convert('RGB')

                # Apply unsharp mask for better detail
                unsharp = ImageFilter.UnsharpMask(radius=1, percent=150, threshold=3)
                img = img.filter(unsharp)

                # Upscale using high-quality resampling
                new_size = (img.width * 2, img.height * 2)
                enhanced = img.resize(new_size, Image.Resampling.LANCZOS)

                # Apply slight sharpening after upscale
                enhancer = ImageEnhance.Sharpness(enhanced)
                enhanced = enhancer.enhance(1.3)

            elif enhancement_type == "sharpen":
                # Advanced sharpening with multiple passes
                enhanced = img.filter(ImageFilter.UnsharpMask(radius=1, percent=200, threshold=2))
                enhancer = ImageEnhance.Sharpness(enhanced)
                enhanced = enhancer.enhance(2.5)

            elif enhancement_type == "brighten":
                # Smart brightness enhancement
                enhancer = ImageEnhance.Brightness(img)
                enhanced = enhancer.enhance(1.4)
                # Also slightly increase contrast for better visibility
                contrast_enhancer = ImageEnhance.Contrast(enhanced)
                enhanced = contrast_enhancer.enhance(1.1)

            elif enhancement_type == "hdr":
                # HDR-like effect
                enhanced = img.filter(ImageFilter.UnsharpMask(radius=2, percent=300, threshold=1))
                enhancer = ImageEnhance.Contrast(enhanced)
                enhanced = enhancer.enhance(1.3)
                brightness_enhancer = ImageEnhance.Brightness(enhanced)
                enhanced = brightness_enhancer.enhance(1.1)

            else:
                enhanced = img

            # Save enhanced image with high quality
            base_name = os.path.basename(image_path)
            name, ext = os.path.splitext(base_name)
            enhanced_path = os.path.join(UPLOAD_DIR, f"{name}_enhanced{ext}")

            # Save with high quality settings
            if ext.lower() in ['.jpg', '.jpeg']:
                enhanced.save(enhanced_path, quality=95, optimize=True)
            else:
                enhanced.save(enhanced_path)

            return f"/uploads/{name}_enhanced{ext}"
        except Exception as e:
            raise Exception(f"Image enhancement failed: {str(e)}")
