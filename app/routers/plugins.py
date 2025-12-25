"""
Plugins router - Plugin management
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from app.services.plugin_manager import PluginManager

router = APIRouter()


class PluginInfo(BaseModel):
    id: str
    name: str
    description: str
    enabled: bool


@router.get("/", response_model=List[PluginInfo])
async def list_plugins():
    """List all available plugins"""
    plugin_manager = PluginManager()
    return plugin_manager.list_plugins()


@router.post("/{plugin_id}/enable")
async def enable_plugin(plugin_id: str):
    """Enable a plugin"""
    plugin_manager = PluginManager()
    success = plugin_manager.enable_plugin(plugin_id)
    if not success:
        raise HTTPException(status_code=404, detail="Plugin not found")
    return {"status": "enabled", "plugin_id": plugin_id}


@router.post("/{plugin_id}/disable")
async def disable_plugin(plugin_id: str):
    """Disable a plugin"""
    plugin_manager = PluginManager()
    success = plugin_manager.disable_plugin(plugin_id)
    if not success:
        raise HTTPException(status_code=404, detail="Plugin not found")
    return {"status": "disabled", "plugin_id": plugin_id}

