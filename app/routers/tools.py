"""
Tools router - Tool integrations
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from app.services.tools.web_search import WebSearchTool
from app.services.tools.code_executor import CodeExecutor
from app.services.tools.image_generator import ImageGeneratorTool

router = APIRouter()


class ToolRequest(BaseModel):
    tool: str
    parameters: Dict[str, Any]


@router.post("/execute")
async def execute_tool(request: ToolRequest):
    """Execute a tool"""
    try:
        if request.tool == "web_search":
            tool = WebSearchTool()
            result = await tool.search(request.parameters.get("query", ""))
        elif request.tool == "code_execute":
            tool = CodeExecutor()
            result = await tool.execute(
                code=request.parameters.get("code", ""),
                language=request.parameters.get("language", "python")
            )
        elif request.tool == "image_generate":
            tool = ImageGeneratorTool()
            result = await tool.generate(request.parameters.get("prompt", ""))
        else:
            raise HTTPException(status_code=400, detail="Unknown tool")
        
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_tools():
    """List available tools"""
    return {
        "tools": [
            {"id": "web_search", "name": "Web Search", "description": "Search the web for information"},
            {"id": "code_execute", "name": "Code Executor", "description": "Execute code in multiple languages"},
            {"id": "image_generate", "name": "Image Generator", "description": "Generate images from text"},
            {"id": "document_parser", "name": "Document Parser", "description": "Parse PDF, Word, and other documents"},
        ]
    }

