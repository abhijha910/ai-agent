# 🛠️ Complete Setup Guide

## Prerequisites

- Python 3.10+
- Node.js 18+
- At least ONE API key (Google, OpenAI, or Anthropic)

## Step 1: Get API Key

### Option 1: Google Gemini (FREE, Recommended)

1. Visit: https://makersuite.google.com/app/apikey
2. Sign in with Google
3. Click "Create API Key"
4. Copy the key (looks like: `AIzaSy...`)

### Option 2: OpenAI

1. Visit: https://platform.openai.com/api-keys
2. Sign up/Login
3. Create new secret key
4. Copy the key (starts with `sk-`)

### Option 3: Anthropic Claude

1. Visit: https://console.anthropic.com/
2. Sign up/Login
3. Create API key
4. Copy the key (starts with `sk-ant-`)

## Step 2: Configure Environment

```bash
# Create .env file
copy env.example .env
```

Edit `.env` file and add your API key:

```env
# Add at least ONE of these:
GOOGLE_API_KEY=AIzaSy-your-key-here
# OPENAI_API_KEY=sk-your-key-here
# ANTHROPIC_API_KEY=sk-ant-your-key-here

# Database (default is fine)
DATABASE_URL=sqlite:///./ai_agent.db

# Server (default is fine)
PORT=8000
FRONTEND_URL=http://localhost:3000
```

## Step 3: Install Dependencies

### Backend

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate

# Install packages
pip install -r requirements-working.txt
```

### Frontend

```bash
cd frontend
npm install
cd ..
```

## Step 4: Initialize Database

```bash
venv\Scripts\activate
python -c "from app.database import init_db; init_db()"
```

## Step 5: Start Servers

### Backend (Terminal 1)

```bash
venv\Scripts\activate
python -m uvicorn app.main:app --reload
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
✅ Server ready!
```

### Frontend (Terminal 2 - NEW TERMINAL)

```bash
cd frontend
npm run dev
```

You should see:
```
✓ Ready on http://localhost:3000
```

## Step 6: Test It!

1. Open: http://localhost:3000
2. Type: "Hello!"
3. See AI respond! 🎉

## Troubleshooting

### "Module not found"
```bash
venv\Scripts\activate
pip install -r requirements-working.txt
```

### "Port already in use"
- Close other applications using port 8000
- Or change `PORT=8001` in `.env`

### "API key invalid"
- Check key is correct (no extra spaces)
- Verify key is active in provider dashboard

### "WebSocket not connected"
- Make sure backend is running on port 8000
- Check browser console (F12) for errors

## Verify Setup

```bash
# Test API keys
python test_api_keys.py

# Check backend
curl http://localhost:8000/health
```

## Next Steps

- See **FEATURES.md** for all available features
- Check API docs: http://localhost:8000/docs
- Customize the UI in `frontend/src/components/`

---

**Need help?** Check the error messages and verify all steps above.

