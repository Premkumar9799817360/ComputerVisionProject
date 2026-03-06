#!/usr/bin/env python3
"""
SightFlow startup script.
Run: python run.py
"""
import uvicorn
from backend.config import APP_HOST, APP_PORT

if __name__ == "__main__":
    print("=" * 55)
    print("  👁  SightFlow - AI Proctoring System")
    print("=" * 55)
    print(f"  Starting on http://{APP_HOST}:{APP_PORT}")
    print(f"  Open browser: http://localhost:{APP_PORT}")
    print("=" * 55)
    uvicorn.run("main:app", host=APP_HOST, port=APP_PORT, reload=True)
