#!/usr/bin/env python3
"""
Script untuk menjalankan (Telegram Bot untuk UNAND)
Pastikan backend FastAPI sudah berjalan sebelum menjalankan bot ini.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Tambahkan path backend ke sys.path jika diperlukan
backend_path = Path(__file__).parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

# Import bot (gunakan versi simple jika ada masalah dengan async)
try:
    from telegram_bot import main
except Exception as e:
    print(f"⚠️  Using simple version due to: {e}")
    from telegram_bot_simple import main

def check_environment():
    """Cek environment variables yang diperlukan"""
    required_vars = {
        "TELEGRAM_BOT_TOKEN": "Token bot Telegram dari BotFather (Tanyo Unand)",
        "BACKEND_URL": "URL backend FastAPI (mis. http://localhost:8001)",
    }
    
    missing_vars = []
    for var, description in required_vars.items():
        if not os.getenv(var):
            missing_vars.append(f"  - {var}: {description}")
    
    if missing_vars:
        print("❌ Environment variables berikut belum diset:")
        print("\n".join(missing_vars))
        print("\nSilakan set environment variables tersebut atau buat file .env")
        return False
    
    return True

def print_startup_info():
    """Print informasi startup"""
    print("🤖 Tanyo Unand - Chatbot Telegram")
    print("=" * 50)
    print(f"Backend URL: {os.getenv('BACKEND_URL', 'http://localhost:8001')}")
    print(f"Bot Token: {os.getenv('TELEGRAM_BOT_TOKEN', 'Not set')[:20]}...")
    print("=" * 50)
    print("📋 Pastikan:")
    print("  1. Backend FastAPI sudah berjalan (python -m uvicorn main:app --reload)")
    print("  2. Database PostgreSQL sudah berjalan")
    print("  3. File .env sudah dikonfigurasi dengan benar")
    print("=" * 50)

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print_startup_info()
    
    # Cek environment
    if not check_environment():
        sys.exit(1)
    
    try:
        print("🚀 Starting Chatbot UNAND...")
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Bot stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)
