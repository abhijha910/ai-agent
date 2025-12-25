"""
Agent Orchestrator - Multi-agent coordination
"""
from typing import List, Optional, Dict
import asyncio
import time
from app.services.ai_service import AIService
from app.services.tools.web_search import WebSearchTool
from app.services.tools.code_executor import CodeExecutor


class AgentOrchestrator:
    """Orchestrates multiple AI agents for complex tasks"""
    
    def __init__(self):
        self.ai_service = AIService()
        self.agents = {
            "researcher": self._research_agent,
            "coder": self._code_agent,
            "analyst": self._analysis_agent,
            "writer": self._writing_agent,
        }
    
    async def execute_task(
        self,
        task: str,
        agents: Optional[List[str]] = None,
        strategy: str = "parallel"
    ) -> Dict:
        """Execute task using specified agents and strategy"""
        start_time = time.time()
        
        if agents is None:
            agents = self._select_agents(task)
        
        if strategy == "parallel":
            results = await self._execute_parallel(task, agents)
        elif strategy == "sequential":
            results = await self._execute_sequential(task, agents)
        else:  # collaborative
            results = await self._execute_collaborative(task, agents)
        
        execution_time = time.time() - start_time
        
        return {
            "result": self._synthesize_results(results),
            "agents_used": agents,
            "execution_time": execution_time
        }
    
    def _select_agents(self, task: str) -> List[str]:
        """Automatically select agents based on task"""
        task_lower = task.lower()
        selected = []
        
        if any(word in task_lower for word in ["search", "find", "research", "information"]):
            selected.append("researcher")
        if any(word in task_lower for word in ["code", "program", "script", "function"]):
            selected.append("coder")
        if any(word in task_lower for word in ["analyze", "data", "statistics", "insight"]):
            selected.append("analyst")
        if any(word in task_lower for word in ["write", "content", "article", "blog"]):
            selected.append("writer")
        
        return selected if selected else ["researcher"]  # Default
    
    async def _execute_parallel(self, task: str, agents: List[str]) -> Dict:
        """Execute agents in parallel"""
        tasks = [self.agents[agent](task) for agent in agents if agent in self.agents]
        results = await asyncio.gather(*tasks)
        return {agent: result for agent, result in zip(agents, results)}
    
    async def _execute_sequential(self, task: str, agents: List[str]) -> Dict:
        """Execute agents sequentially"""
        results = {}
        current_task = task
        
        for agent in agents:
            if agent in self.agents:
                result = await self.agents[agent](current_task)
                results[agent] = result
                current_task = f"{task}\n\nPrevious results: {result}"
        
        return results
    
    async def _execute_collaborative(self, task: str, agents: List[str]) -> Dict:
        """Execute agents collaboratively with communication"""
        results = {}
        shared_context = task
        
        for agent in agents:
            if agent in self.agents:
                result = await self.agents[agent](shared_context)
                results[agent] = result
                shared_context += f"\n\n{agent} output: {result}"
        
        return results
    
    async def _research_agent(self, task: str) -> str:
        """Research agent for information gathering"""
        search_tool = WebSearchTool()
        results = await search_tool.search(task, max_results=3)
        
        summary = f"Research results for: {task}\n\n"
        for r in results:
            summary += f"- {r.get('title', '')}: {r.get('snippet', '')}\n"
        
        return summary
    
    async def _code_agent(self, task: str) -> str:
        """Code agent for code generation"""
        prompt = f"Generate code for: {task}. Provide only the code without explanations."
        response = ""
        async for chunk in self.ai_service.stream_chat(prompt, model="gpt-4"):
            response += chunk
        return response
    
    async def _analysis_agent(self, task: str) -> str:
        """Analysis agent for data analysis"""
        prompt = f"Analyze and provide insights for: {task}"
        response = ""
        async for chunk in self.ai_service.stream_chat(prompt, model="gpt-4"):
            response += chunk
        return response
    
    async def _writing_agent(self, task: str) -> str:
        """Writing agent for content creation"""
        prompt = f"Write high-quality content for: {task}"
        response = ""
        async for chunk in self.ai_service.stream_chat(prompt, model="gpt-4"):
            response += chunk
        return response
    
    def _synthesize_results(self, results: Dict) -> str:
        """Synthesize results from multiple agents"""
        synthesis = "Synthesized Results:\n\n"
        for agent, result in results.items():
            synthesis += f"[{agent.upper()}]\n{result}\n\n"
        return synthesis

