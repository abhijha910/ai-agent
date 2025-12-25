#!/bin/bash
echo "Starting AI Agent Backend..."
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -c "from app.database import init_db; init_db()"
python -m uvicorn app.main:app --reload

