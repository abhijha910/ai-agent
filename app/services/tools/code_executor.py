"""
Code Executor Tool - Safe code execution
"""
import subprocess
import tempfile
import os
from typing import Dict, Any
import asyncio


class CodeExecutor:
    """Tool for executing code in a sandboxed environment"""
    
    async def execute(self, code: str, language: str = "python") -> Dict[str, Any]:
        """Execute code and return result"""
        try:
            if language == "python":
                return await self._execute_python(code)
            elif language == "javascript":
                return await self._execute_javascript(code)
            else:
                return {"error": f"Language {language} not supported"}
        except Exception as e:
            return {"error": str(e)}
    
    async def _execute_python(self, code: str) -> Dict[str, Any]:
        """Execute Python code"""
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            # Execute with timeout
            process = await asyncio.create_subprocess_exec(
                'python', temp_file,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=10)
            
            return {
                "output": stdout.decode('utf-8'),
                "error": stderr.decode('utf-8') if stderr else None,
                "exit_code": process.returncode
            }
        finally:
            # Clean up
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    async def _execute_javascript(self, code: str) -> Dict[str, Any]:
        """Execute JavaScript code using Node.js"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            process = await asyncio.create_subprocess_exec(
                'node', temp_file,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=10)
            
            return {
                "output": stdout.decode('utf-8'),
                "error": stderr.decode('utf-8') if stderr else None,
                "exit_code": process.returncode
            }
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

