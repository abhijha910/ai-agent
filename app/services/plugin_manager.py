"""
Plugin Manager - Plugin system management
"""
from typing import List, Dict
import os
import importlib
from pathlib import Path


class PluginManager:
    """Manages plugins for extensibility"""
    
    def __init__(self):
        self.plugins_dir = Path("app/plugins")
        self.enabled_plugins = set()
        self._load_plugins()
    
    def _load_plugins(self):
        """Load available plugins"""
        if not self.plugins_dir.exists():
            self.plugins_dir.mkdir(parents=True, exist_ok=True)
    
    def list_plugins(self) -> List[Dict]:
        """List all available plugins"""
        plugins = []
        
        # Built-in plugins
        built_in = [
            {"id": "web_search", "name": "Web Search", "description": "Search the web", "enabled": True},
            {"id": "code_executor", "name": "Code Executor", "description": "Execute code", "enabled": True},
            {"id": "image_generator", "name": "Image Generator", "description": "Generate images", "enabled": True},
        ]
        
        plugins.extend(built_in)
        
        # Load custom plugins
        for plugin_file in self.plugins_dir.glob("*.py"):
            if plugin_file.name != "__init__.py":
                plugin_id = plugin_file.stem
                plugins.append({
                    "id": plugin_id,
                    "name": plugin_id.replace("_", " ").title(),
                    "description": "Custom plugin",
                    "enabled": plugin_id in self.enabled_plugins
                })
        
        return plugins
    
    def enable_plugin(self, plugin_id: str) -> bool:
        """Enable a plugin"""
        self.enabled_plugins.add(plugin_id)
        return True
    
    def disable_plugin(self, plugin_id: str) -> bool:
        """Disable a plugin"""
        if plugin_id in self.enabled_plugins:
            self.enabled_plugins.remove(plugin_id)
        return True

