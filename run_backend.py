#!/usr/bin/env python
"""Simple script to run the backend server"""
import uvicorn
import os
from pathlib import Path

if __name__ == "__main__":
    print("=" * 50)
    print("Starting AI Agent Backend Server")
    print("=" * 50)
    print()
    
    # Check if .env exists
    if not Path(".env").exists():
        print("⚠️  Warning: .env file not found!")
        print("   Create .env file with your API keys")
        print()
    
    port = int(os.getenv("PORT", 8000))
    print(f"Starting server on http://0.0.0.0:{port}")
    print(f"WebSocket: ws://localhost:{port}/ws")
    print(f"API Docs: http://localhost:{port}/docs")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    print()
    
    try:
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=port,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        import traceback
        traceback.print_exc()

