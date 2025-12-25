# 🤖 Advanced AI Agent

A powerful, feature-rich AI agent that goes beyond ChatGPT and Gemini with unique capabilities.

## ✨ Key Features

- **Multi-Model Support** - GPT-4, Claude, Gemini
- **Real-Time Streaming** - WebSocket-based responses
- **Web Search** - Live information retrieval
- **Code Execution** - Safe code running
- **Image Generation** - DALL-E integration
- **Memory System** - Long-term conversation memory
- **Multi-Agent** - Collaborative AI agents
- **Plugin System** - Extensible architecture

## 🚀 Quick Start

### 1. Get API Key (Choose ONE)

**Google Gemini (FREE, Recommended):**
- Visit: https://makersuite.google.com/app/apikey
- Create API key
- Copy the key

### 2. Setup

```bash
# Create .env file
copy env.example .env

# Edit .env and add your API key:
# GOOGLE_API_KEY=your-key-here

# Install dependencies
python -m venv venv
venv\Scripts\activate
pip install -r requirements-working.txt

# Initialize database
python -c "from app.database import init_db; init_db()"
```

### 3. Start Servers

**Terminal 1 - Backend:**
```bash
venv\Scripts\activate
python -m uvicorn app.main:app --reload
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm install
npm run dev
```

### 4. Open Browser

Go to: **http://localhost:3000** and start chatting!

## 📚 Documentation

- **SETUP.md** - Complete setup instructions
- **FEATURES.md** - All available features

## 🛠️ Tech Stack

- **Backend:** FastAPI, Python, SQLAlchemy
- **Frontend:** Next.js, React, TypeScript
- **AI:** OpenAI, Anthropic, Google Gemini

## 📝 License

MIT License
