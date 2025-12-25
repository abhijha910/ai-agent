"""
Web Search Tool
"""
from duckduckgo_search import DDGS
from typing import List, Dict
import httpx


class WebSearchTool:
    """Tool for searching the web"""
    
    async def search(self, query: str, max_results: int = 5) -> List[Dict]:
        """Search the web and return results"""
        try:
            with DDGS() as ddgs:
                results = []
                for r in ddgs.text(query, max_results=max_results):
                    results.append({
                        "title": r.get("title", ""),
                        "url": r.get("href", ""),
                        "snippet": r.get("body", "")
                    })
                return results
        except Exception as e:
            return [{"error": str(e)}]

