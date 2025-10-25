# UNAND Chatbot System - Deployment Guide

Panduan lengkap untuk deploy dan menjalankan sistem chatbot UNAND dengan 3 platform.

## 🚨 **PENTING: Setup untuk Device Baru (Setelah Extract ZIP)**

Jika Anda mendapatkan project ini dari file ZIP dan mengalami error SQLAlchemy, ikuti langkah-langkah berikut:

### **Quick Fix untuk Error SQLAlchemy:**

1. **Buat Virtual Environment Baru:**

```bash
# Masuk ke folder project
cd chatbot-unand

# Buat virtual environment
python -m venv venv

# Aktifkan virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

2. **Install Dependencies:**

```bash
# Install backend dependencies
cd backend
pip install -r requirements.txt
cd ..
```

3. **Buat File .env:**

```bash
# Buat file .env di root folder (chatbot-unand/.env)
# Copy isi dari template di bawah
```

4. **Konfigurasi Database:**

```env
# File .env (buat di root folder chatbot-unand)
DATABASE_URL=postgresql://postgres:gMkQnFOVtkhEOHlxsKmuxjRYUyoLHOcQ@turntable.proxy.rlwy.net:31554/railway
GEMINI_API_KEY=AIzaSyAM0cEUZ-4tZapGhUA3oJi5ea-FduA8yo0
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
BACKEND_URL=http://localhost:8000
```

5. **Test Backend:**

```bash
cd backend
python -m uvicorn main:app --reload --port 8000
```

Jika masih error, lanjut ke panduan lengkap di bawah.

## 🚨 **SOLUSI UNTUK ERROR KETIKA PROJECT DI-ZIP DAN EXTRACT KE DEVICE LAIN**

### **Error yang Sering Terjadi:**

```
AssertionError: Class <class 'sqlalchemy.sql.elements.SQLCoreOperations'> directly inherits TypingOnly but has additional attributes
```

### **Penyebab:**

1. Virtual environment tidak terbawa dalam zip
2. Dependencies tidak terinstall di device baru
3. File .env tidak ada atau tidak terkonfigurasi
4. Versi Python/SQLAlchemy tidak kompatibel

### **Solusi Cepat:**

```bash
# 1. Buat virtual environment baru
python -m venv venv

# 2. Aktivasi virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 3. Install dependencies
cd backend
pip install -r requirements.txt

# 4. Buat file .env (lihat template di bawah)
# 5. Test connection
python test_backend_connection.py
```

## 📋 Checklist Pre-Deployment

### ✅ Software Requirements

- [ ] Python 3.8+ terinstall
- [ ] Node.js 16+ terinstall
- [ ] PostgreSQL 12+ terinstall dan berjalan
- [ ] Git terinstall (untuk clone repository)

### ✅ API Keys & Tokens

- [ ] Google Gemini API Key (dari Google AI Studio)
- [ ] Telegram Bot Token (dari @BotFather)
- [ ] Database credentials PostgreSQL

### ✅ Network & Ports

- [ ] Port 8000 tersedia (Backend FastAPI)
- [ ] Port 3001 tersedia (Frontend React)
- [ ] Port 5432 tersedia (PostgreSQL)
- [ ] Internet connection untuk API calls

## 🚀 Step-by-Step Deployment

### Step 1: Clone & Setup Project

```bash
# Clone repository
git clone <repository-url>
cd chatbot-unand

# Atau jika sudah ada, pastikan di direktori yang benar
cd chatbot-unand
```

### Step 2: Database Setup

```sql
-- Login ke PostgreSQL sebagai superuser
psql -U postgres

-- Buat database
CREATE DATABASE chatbot_unand_db;

-- Buat user (opsional)
CREATE USER chatbot_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE chatbot_unand_db TO chatbot_user;

-- Exit
\q
```

### Step 3: Environment Configuration

```bash
# Buat file .env di root project
cp .env.example .env  # Jika ada template
# Atau buat manual:
```

File `.env`:

```env
# AI Configuration
GEMINI_API_KEY=your_actual_gemini_api_key_here

# Database Configuration
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/chatbot_unand_db

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_actual_telegram_bot_token_here

# Backend URL
BACKEND_URL=http://localhost:8000
```

### Step 4: Install Dependencies

```bash
# Install Python dependencies
cd backend
pip install -r requirements.txt
cd ..

# Install Node.js dependencies
cd frontend
npm install
cd ..
```

### Step 5: Prepare Documents

```bash
# Pastikan folder data ada
mkdir -p backend/data

# Copy dokumen .docx ke folder backend/data/
# Contoh:
# cp /path/to/your/documents/*.docx backend/data/
```

### Step 6: Test Individual Components

#### Test Database Connection

```bash
python -c "
import psycopg2
from dotenv import load_dotenv
import os
load_dotenv()
try:
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    print('✅ Database connection OK')
    conn.close()
except Exception as e:
    print(f'❌ Database connection failed: {e}')
"
```

#### Test Backend

```bash
cd backend
python -m uvicorn main:app --reload --port 8000
# Buka browser: http://localhost:8000/health
# Harus return: {"status": "OK", ...}
```

#### Test Frontend

```bash
cd frontend
npm start
# Buka browser: http://localhost:3001
# Harus tampil interface chatbot
```

### Step 7: Deploy All Services

```bash
# Manual deployment (3 terminal)
# Terminal 1: cd backend && python -m uvicorn main:app --reload
# Terminal 2: cd frontend && npm start
# Terminal 3: python run_telegram_bot.py
```

## 🔧 Troubleshooting

### Backend Issues

#### Error: "GEMINI_API_KEY not found"

```bash
# Cek file .env
cat .env | grep GEMINI_API_KEY

# Pastikan tidak ada spasi atau quotes berlebih
GEMINI_API_KEY=AIzaSy...  # ✅ Benar
GEMINI_API_KEY = "AIzaSy..."  # ❌ Salah
```

#### Error: Database connection failed

```bash
# Cek PostgreSQL berjalan
sudo systemctl status postgresql  # Linux
brew services list | grep postgres  # Mac
# Windows: Services.msc -> PostgreSQL

# Test manual connection
psql -U postgres -d chatbot_unand_db -h localhost -p 5432
```

#### Error: Port already in use

```bash
# Cek port yang digunakan
netstat -tulpn | grep :8000  # Linux/Mac
netstat -ano | findstr :8000  # Windows

# Kill process jika perlu
# Windows: taskkill /F /PID <process_id>
# Linux/Mac: kill -9 <process_id>
```

### Frontend Issues

#### Error: "npm command not found"

```bash
# Install Node.js dari https://nodejs.org
node --version  # Harus return versi
npm --version   # Harus return versi
```

#### Error: "Module not found"

```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Telegram Bot Issues

#### Error: "Bot token invalid"

```bash
# Cek token di .env
# Dapatkan token baru dari @BotFather jika perlu
# Format: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz
```

#### Error: "Backend not available"

```bash
# Pastikan backend berjalan di port 8000
curl http://localhost:8000/health

# Cek BACKEND_URL di .env
echo $BACKEND_URL  # Harus: http://localhost:8000
```

## 📊 Monitoring & Maintenance

### Health Checks

```bash
# Cek backend
curl http://localhost:8000/health

# Cek frontend
curl http://localhost:3001

# Cek telegram bot
python test_backend_connection.py
```

### Log Monitoring

```bash
# Backend logs
tail -f backend/logs/app.log  # Jika ada

# Frontend logs
# Lihat di terminal yang menjalankan npm start

# Telegram bot logs
# Lihat di terminal yang menjalankan bot
```

### Performance Monitoring

```bash
# Cek resource usage
htop  # Linux/Mac
# Task Manager -> Performance  # Windows

# Cek database size
psql -U postgres -d chatbot_unand_db -c "
SELECT pg_size_pretty(pg_database_size('chatbot_unand_db'));
"
```

## 🔄 Updates & Maintenance

### Update Dependencies

```bash
# Python dependencies
cd backend
pip install -r requirements.txt --upgrade

# Node.js dependencies
cd frontend
npm update
```

### Backup Database

```bash
# Backup
pg_dump -U postgres chatbot_unand_db > backup_$(date +%Y%m%d).sql

# Restore
psql -U postgres chatbot_unand_db < backup_20241201.sql
```

### Update Documents

```bash
# Tambah dokumen baru
cp new_document.docx backend/data/

# Restart backend untuk reindex
# Stop backend (Ctrl+C di terminal backend)
# Start backend: cd backend && python -m uvicorn main:app --reload
```

## 🚨 Emergency Procedures

### Complete System Reset

```bash
# Stop all services (Ctrl+C di setiap terminal)

# Clear vector database (akan rebuild otomatis)
rm -rf backend/vector_db/*

# Restart manually:
# Terminal 1: cd backend && python -m uvicorn main:app --reload
# Terminal 2: cd frontend && npm start
# Terminal 3: python run_telegram_bot.py
```

### Database Reset

```sql
-- Drop dan recreate database
DROP DATABASE chatbot_unand_db;
CREATE DATABASE chatbot_unand_db;
```

### Service Recovery

```bash
# Jika satu service crash, restart individual:
# Backend only:
cd backend && python -m uvicorn main:app --reload

# Frontend only:
cd frontend && npm start

# Telegram bot only:
python run_telegram_bot.py
```

## 📞 Support Contacts

- **Technical Issues**: Check logs dan error messages
- **API Issues**: Cek Google AI Studio dan Telegram Bot settings
- **Database Issues**: Cek PostgreSQL logs dan connection
- **Network Issues**: Cek firewall dan port availability
