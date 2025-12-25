"""
Image Generator Tool
"""
from app.services.ai_service import AIService
from typing import Dict


class ImageGeneratorTool:
    """Tool for generating images"""
    
    def __init__(self):
        self.ai_service = AIService()
    
    async def generate(self, prompt: str, model: str = "dall-e-3") -> Dict:
        """Generate image from prompt"""
        try:
            image_url = await self.ai_service.generate_image(prompt, model)
            return {
                "success": True,
                "image_url": image_url,
                "prompt": prompt
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
