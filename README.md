# UNAND Chatbot System

Sistem chatbot komprehensif untuk Universitas Andalas dengan 3 platform terintegrasi yang menggunakan teknologi RAG (Retrieval-Augmented Generation) dan Google Gemini AI.

## 🌟 Platform yang Tersedia

1. **Website Chatbot** - Interface web responsif dengan autentikasi Google OAuth dan admin panel
2. **Telegram Bot** - Bot Telegram (@junwar_bot) dengan session management
3. **Backend API** - Sistem RAG dengan FAISS vector database dan Google Gemini AI
4. **Admin Panel** - Interface admin untuk manajemen file knowledge base dan monitoring user

## 🎯 Fitur Utama

### 🤖 Sistem AI & RAG

- **RAG System**: Retrieval-Augmented Generation dengan FAISS vector database
- **Google Gemini AI**: Model generatif untuk respons yang akurat dan kontekstual
- **Document Processing**: Otomatis memproses 20+ dokumen resmi UNAND (.docx)
- **Smart Retrieval**: Pencarian semantik dengan threshold scoring yang dapat dikonfigurasi

### 🔐 Autentikasi & Session Management

- **Google OAuth**: Login dengan akun Gmail untuk website
- **Session Management**: Riwayat percakapan per user dengan PostgreSQL
- **Multi-Platform Sessions**: Session terpisah untuk website dan Telegram
- **User Profiles**: Manajemen profil pengguna dengan foto dan informasi

### 🎨 User Interface & Experience

- **Responsive Design**: Interface yang responsif untuk desktop dan mobile
- **Dark/Light Mode**: Toggle tema dengan preferensi tersimpan
- **UNAND Branding**: Tema hijau-coklat dengan logo dan tagline resmi
- **Structured Responses**: Format jawaban dengan kesimpulan, referensi, dan saran
- **Accordion UI**: Referensi yang dapat diperluas dengan shadcn/ui components
- **Admin Panel**: Interface admin untuk upload/delete file dan monitoring user
- **Timezone Support**: Waktu Indonesia (WIB/UTC+7) di seluruh sistem

### 📱 Multi-Platform Support

- **Website**: React.js dengan Tailwind CSS dan shadcn/ui
- **Telegram Bot**: Python-telegram-bot dengan async support
- **Unified Backend**: FastAPI backend yang melayani kedua platform
- **Document Upload**: Upload dokumen baru melalui admin interface
- **Auto Knowledge Base Rebuild**: Otomatis rebuild FAISS index saat upload/delete file

## 🚀 Quick Start

### Prasyarat

- Python 3.8+
- Node.js 16+
- PostgreSQL 12+
- Google Gemini API Key
- Telegram Bot Token (opsional)

### Menjalankan Sistem

Jalankan setiap komponen secara manual di terminal terpisah:

```bash
# Terminal 1 - Backend FastAPI
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend React
cd frontend
npm start

# Terminal 3 - Telegram Bot (opsional)
cd telegram-bot
python run_telegram_bot.py
```

## 🌐 Akses Aplikasi

Setelah menjalankan semua service:

- **Website**: http://localhost:3002
- **Admin Panel**: http://localhost:3002/admin/dashboard
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Telegram Bot**: @junwar_bot

### 🔐 Admin Credentials

- **Email**: admunand@gmail.com
- **Password**: untukkedjajaanbangsa1948

## 🏗️ Arsitektur Sistem

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Web     │    │  Telegram Bot   │    │   Mobile App    │
│   (Port 3001)   │    │  (@junwar_bot)  │    │   (Future)      │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────▼───────────────┐
                    │     FastAPI Backend        │
                    │      (Port 8000)           │
                    │  ┌─────────────────────┐   │
                    │  │   Google OAuth      │   │
                    │  │   JWT Auth          │   │
                    │  └─────────────────────┘   │
                    │  ┌─────────────────────┐   │
                    │  │   RAG System        │   │
                    │  │   FAISS Vector DB   │   │
                    │  │   Google Gemini AI  │   │
                    │  └─────────────────────┘   │
                    └─────────────┬───────────────┘
                                  │
                    ┌─────────────▼───────────────┐
                    │    PostgreSQL Database     │
                    │   (Railway/Local)          │
                    │  ┌─────────────────────┐   │
                    │  │ Users & Sessions    │   │
                    │  │ Chat History        │   │
                    │  │ User Profiles       │   │
                    │  └─────────────────────┘   │
                    └─────────────────────────────┘
```

## 📁 Struktur Proyek

```
chatbot-unand/
├── README.md                    # Dokumentasi utama (UPDATED)
├── .env                         # Environment variables
│
├── backend/                     # 🐍 Backend FastAPI
│   ├── main.py                  # Entry point FastAPI dengan RAG system
│   ├── database.py              # Models SQLAlchemy & database config
│   ├── auth_service.py          # Google OAuth & JWT authentication
│   ├── requirements.txt         # Dependencies Python
│   ├── client_secret_*.json     # Google OAuth credentials
│   ├── data/                    # 📄 Dokumen knowledge base (20+ files)
│   │   ├── permendikbud*.docx   # Peraturan Mendikbud
│   │   ├── Peraturan_Rektor*.docx # Peraturan Rektor UNAND
│   │   ├── PP95-2021*.docx      # Peraturan Pemerintah
│   │   └── ...                  # Dokumen lainnya
│   └── vector_db/               # 🔍 FAISS vector database
│       ├── faiss_index.bin      # FAISS index file
│       └── doc_chunks.json      # Document chunks metadata
│
├── frontend/                    # ⚛️ Frontend React
│   ├── public/
│   │   ├── index.html
│   │   └── lambang-unand.jpg    # Logo UNAND
│   ├── src/
│   │   ├── App.jsx              # Main app component
│   │   ├── ChatWindow.jsx       # Chat interface
│   │   ├── ChatInput.jsx        # Input component
│   │   ├── ChatSidebar.jsx      # Sidebar dengan chat history
│   │   ├── Message.jsx          # Message component dengan accordion
│   │   ├── TelegramButton.jsx   # Floating Telegram button
│   │   ├── api.js               # API client functions
│   │   ├── index.js             # React entry point
│   │   ├── index.css            # Tailwind CSS styles
│   │   ├── components/          # 🧩 Reusable components
│   │   │   ├── Login.jsx        # Google OAuth login
│   │   │   ├── ThemeToggle.jsx  # Dark/light mode toggle
│   │   │   ├── UserProfile.jsx  # User profile component
│   │   │   ├── SessionGuard.jsx # Session protection component
│   │   │   ├── AdminLogin.jsx   # Admin login component
│   │   │   ├── AdminLayout.jsx  # Admin layout component
│   │   │   ├── AdminDashboard.jsx # Admin dashboard
│   │   │   ├── AdminUpload.jsx  # Admin file upload
│   │   │   └── ui/              # shadcn/ui components
│   │   │       ├── accordion.jsx
│   │   │       └── switch.jsx
│   │   └── contexts/            # React contexts
│   │       ├── AuthContext.jsx  # Authentication context
│   │       └── ThemeContext.jsx # Theme context
│   ├── package.json             # Dependencies Node.js
│   ├── tailwind.config.js       # Tailwind configuration
│   ├── postcss.config.js        # PostCSS configuration
│   ├── components.json          # shadcn/ui configuration
│   └── jsconfig.json            # JavaScript configuration
│
└── telegram-bot/                # 🤖 Telegram Bot
    ├── telegram_bot.py          # Main bot implementation
    ├── telegram_bot_simple.py   # Simple bot version
    ├── run_telegram_bot.py      # Bot runner script
    └── README.md                # Telegram bot documentation
```

## ⚙️ Setup & Installation

### 1. Clone Repository

```bash
git clone <repository-url>
cd chatbot-unand
```

### 2. Environment Variables ⭐ UPDATED

**File `.env` sekarang disatukan di root folder untuk semua services (backend & frontend)!**

📚 **Dokumentasi Lengkap:**
- **Quick Start:** `QUICK_REFERENCE.md` ⚡
- **Setup Guide:** `README_ENV_SETUP.md` 📖
- **Full Documentation:** `ENV_CONFIGURATION.md` 📚
- **Testing:** `python test_env.py` 🧪

File `.env` sudah ada di root folder dengan konfigurasi lengkap:

```env
# ===================================
# BACKEND ENVIRONMENT VARIABLES
# ===================================

# 🤖 AI Configuration
GEMINI_API_KEY=your_api_key_here

# 🗄️ Database Configuration
DATABASE_URL=postgresql://user:password@host:port/database

# 🔐 Google OAuth Configuration
GOOGLE_CLIENT_ID=257608911345-h2bn2frj29lfnnm8mp0sqlk6pjn16nla.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_google_client_secret
APP_SECRET_KEY=your_jwt_secret_key

# ☁️ Google Cloud Configuration
GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
GOOGLE_CLOUD_PROJECT=chatbot-unand-462320
GOOGLE_CLOUD_LOCATION=asia-southeast2

# ===================================
# FRONTEND ENVIRONMENT VARIABLES
# ===================================

# 🌐 Frontend Configuration
REACT_APP_BACKEND_URL=https://api-chatbot.difunand.cloud
REACT_APP_GOOGLE_CLIENT_ID=257608911345-h2bn2frj29lfnnm8mp0sqlk6pjn16nla.apps.googleusercontent.com
REACT_APP_ADMIN_DOMAIN=admin.difunand.cloud

# ===================================
# OPTIONAL: TELEGRAM BOT
# ===================================

# 📱 Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
BACKEND_URL=http://localhost:8001
```

**✅ Test Environment Variables:**
```bash
# Python script
python test_env.py

# PowerShell script
.\test_env.ps1

# Expected output:
# ✅ All required environment variables are set!
```

**📁 Struktur File Environment:**
```
chatbot-unand/
  ├── .env                         ← ⭐ MAIN CONFIG (all env vars)
  ├── .gitignore                   ← Protects .env from Git
  ├── docker-compose.yml           ← Docker deployment config
  ├── QUICK_REFERENCE.md          ← Quick reference guide
  ├── README_ENV_SETUP.md         ← Setup & troubleshooting
  ├── ENV_CONFIGURATION.md        ← Full documentation
  ├── test_env.py                 ← Testing script
  └── test_env.ps1                ← Testing script (Windows)
```

### 3. Install Dependencies

```bash
# 🐍 Python dependencies (Backend)
cd backend
pip install -r requirements.txt

# ⚛️ Node.js dependencies (Frontend)
cd ../frontend
npm install
```

### 4. Database Setup

Database sudah dikonfigurasi menggunakan Railway PostgreSQL. Tabel akan dibuat otomatis saat backend pertama kali dijalankan.

Untuk setup database lokal:

```sql
-- Buat database lokal (opsional)
CREATE DATABASE chatbot_unand_db;

-- Update DATABASE_URL di .env untuk database lokal
DATABASE_URL=postgresql://postgres:password@localhost:5432/chatbot_unand_db
```

### 5. Google OAuth Setup

1. Buka [Google Cloud Console](https://console.cloud.google.com/)
2. Pilih project `chatbot-unand`
3. Enable Google+ API dan Google OAuth2 API
4. Buat OAuth 2.0 credentials
5. Tambahkan authorized redirect URIs:
   - `http://localhost:3002/api/auth/callback/google`
   - `http://localhost:3002`
6. Download credentials JSON dan simpan sebagai `client_secret_*.json` di folder `backend/`

## 🛠️ Testing & Debugging

### Test Backend Connection

```bash
# Test koneksi backend
curl http://localhost:8000/health

# Test API endpoints
curl http://localhost:8000/docs

# Check database connection
# Database tables akan dibuat otomatis saat backend start
```

### Test Frontend

```bash
cd frontend
npm test
```

### Test Telegram Bot

1. Cari `@junwar_bot` di Telegram
2. Kirim `/start` untuk memulai
3. Test dengan pertanyaan: "Apa itu UNAND?"

## 📱 Platform Details

### 1. 🌐 Website Chatbot

**URL**: http://localhost:3002

**Fitur Utama**:

- ✅ Google OAuth login dengan Gmail
- ✅ Dark/Light mode toggle
- ✅ Responsive design untuk mobile & desktop
- ✅ Chat history dengan sidebar
- ✅ Structured responses dengan accordion
- ✅ UNAND branding (hijau-coklat) dengan tagline
- ✅ User profile management
- ✅ Session management per user
- ✅ Floating Telegram button (draggable)
- ✅ Timezone Indonesia (WIB/UTC+7)

**Teknologi**:

- React 18.3.1 dengan JSX
- Tailwind CSS untuk styling
- shadcn/ui components (accordion, switch)
- Google OAuth & JWT authentication
- Context API untuk state management

### 2. 🤖 Telegram Bot (@junwar_bot)

**Commands**:

- `/start` - Memulai percakapan dengan bot
- `/help` - Menampilkan bantuan penggunaan
- `/reset` - Reset session percakapan

**Fitur**:

- ✅ Session management per Telegram user
- ✅ Async message handling
- ✅ Markdown formatting support
- ✅ Error handling & retry logic
- ✅ Health check backend integration
- ✅ Message length optimization untuk Telegram

**Teknologi**:

- python-telegram-bot 20.7
- aiohttp untuk async HTTP calls
- Integrasi dengan FastAPI backend

### 3. 👨‍💼 Admin Panel

**URL**: http://localhost:3002/admin/dashboard
**Login**: admunand@gmail.com / untukkedjajaanbangsa1948

**Fitur Admin**:

- ✅ Dashboard dengan statistik user dan aktivitas
- ✅ Upload file knowledge base (.docx)
- ✅ Delete file dengan auto-rebuild FAISS index
- ✅ Monitor aktivitas user terbaru
- ✅ Manajemen file knowledge base
- ✅ Timezone Indonesia (WIB/UTC+7)
- ✅ User numbering sequential (1,2,3...)
- ✅ Responsive admin interface

**Teknologi**:

- React.js dengan admin routing
- Tailwind CSS untuk styling
- Separate authentication system
- File upload dengan progress tracking
- Real-time knowledge base management

### 4. 🔧 Backend API

**URL**: http://localhost:8000
**Documentation**: http://localhost:8000/docs

**Endpoints**:

**User Endpoints:**

- `POST /auth/google` - Google OAuth authentication
- `GET /auth/me` - Get current user info
- `POST /auth/logout` - Logout user
- `POST /chat` - Send message to chatbot
- `POST /sessions` - Create new chat session
- `GET /sessions` - Get user's chat sessions
- `GET /sessions/{session_id}/messages` - Get session messages
- `GET /health` - Health check

**Admin Endpoints:**

- `POST /admin/login` - Admin authentication
- `GET /admin/dashboard` - Admin dashboard data
- `GET /admin/users` - Get all users
- `GET /admin/files` - Get knowledge base files
- `POST /admin/files/upload` - Upload document
- `DELETE /admin/files/{file_id}` - Delete document

**Teknologi**:

- FastAPI 0.111.0 dengan async support
- SQLAlchemy 2.0.23 untuk ORM
- PostgreSQL dengan psycopg2-binary
- FAISS untuk vector database
- Google Gemini AI untuk text generation
- Google OAuth untuk authentication
- JWT untuk session management

## �️ Database Schema

```sql
-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    google_id VARCHAR UNIQUE,
    email VARCHAR UNIQUE,
    name VARCHAR,
    picture VARCHAR,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- Chat sessions table
CREATE TABLE chat_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR UNIQUE,
    user_id INTEGER REFERENCES users(id),
    title VARCHAR DEFAULT 'New Chat',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- Chat messages table
CREATE TABLE chat_messages (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR,
    message_type VARCHAR, -- 'user' or 'bot'
    content TEXT,
    timestamp TIMESTAMP DEFAULT NOW(),
    sources TEXT, -- JSON string
    summary TEXT,
    suggestions TEXT
);

-- User activities table
CREATE TABLE user_activities (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    activity_type VARCHAR, -- 'login', 'logout', 'chat_start', 'chat_end'
    session_id VARCHAR,
    ip_address VARCHAR,
    user_agent VARCHAR,
    timestamp TIMESTAMP DEFAULT NOW(),
    details TEXT -- JSON string
);

-- Knowledge files table
CREATE TABLE knowledge_files (
    id SERIAL PRIMARY KEY,
    filename VARCHAR UNIQUE,
    original_filename VARCHAR,
    file_path VARCHAR,
    file_size INTEGER,
    file_type VARCHAR,
    upload_date TIMESTAMP DEFAULT NOW(),
    uploaded_by VARCHAR DEFAULT 'admin',
    is_active BOOLEAN DEFAULT TRUE,
    processed_chunks INTEGER DEFAULT 0,
    last_processed TIMESTAMP
);
```

## 📋 System Requirements

- **Python 3.8+** dengan pip
- **Node.js 16+** dengan npm
- **PostgreSQL 12+** (Railway atau local)
- **Google Gemini API Key** (dari Google AI Studio)
- **Google OAuth Credentials** (dari Google Cloud Console)
- **Telegram Bot Token** (dari @BotFather) - opsional

## 📚 Knowledge Base

Sistem ini memiliki 20+ dokumen resmi UNAND yang telah diproses dan dapat dikelola melalui admin panel:

### Peraturan Pemerintah

- PP 95 Tahun 2021 - Perguruan Tinggi Negeri Badan Hukum UNAND
- Permendikbud No. 3 Tahun 2020
- Permendikbud No. 35 Tahun 2020
- Permendikbudristek No. 38 Tahun 2021
- Permendikbudristek No. 53 Tahun 2023 - Penjaminan Mutu PT

### Peraturan Rektor UNAND

- Peraturan Rektor No. 7 Tahun 2022 - Penyelenggaraan Pendidikan
- Peraturan Rektor No. 8 Tahun 2024
- Peraturan Rektor No. 9 Tahun 2022
- Peraturan Rektor No. 10 Tahun 2021 - BKD UNAND

### Panduan & Kebijakan

- Panduan Kurikulum OBE
- Peta Jalan Penelitian UNAND 2021-2024
- SK Panduan Disabilitas
- SK Bentuk Pembelajaran dalam Program Studi
- SK Rekognisi Kegiatan dan Mata Kuliah

## ✨ Fitur Terbaru (Latest Updates)

### 🚀 Admin Panel Features

- **📤 File Upload System**: Upload file .docx ke knowledge base dengan progress tracking
- **🗑️ File Delete System**: Hapus file dari knowledge base dengan konfirmasi
- **🔄 Auto Knowledge Base Rebuild**: Otomatis rebuild FAISS index saat upload/delete
- **📊 User Activity Monitoring**: Monitor aktivitas user dengan timestamp WIB
- **👥 User Management**: Lihat semua user dengan numbering sequential
- **🕐 Timezone Support**: Semua timestamp menggunakan Waktu Indonesia (WIB/UTC+7)

### 🎨 UI/UX Improvements

- **🎯 Responsive Admin Interface**: Admin panel yang responsive untuk semua device
- **🔐 Separate Admin Authentication**: Sistem autentikasi terpisah untuk admin
- **📱 Mobile-Friendly**: Interface yang optimal untuk mobile dan desktop
- **🎨 UNAND Branding**: Konsisten dengan tema hijau-coklat UNAND

### 🔧 Technical Improvements

- **🧹 Code Cleanup**: Menghapus file dan kode yang tidak digunakan
- **⚡ Performance Optimization**: Optimasi performa dengan pembersihan kode
- **🔒 Security Enhancement**: Peningkatan keamanan dengan session isolation
- **📝 Documentation Update**: Dokumentasi lengkap dan up-to-date

## 🔧 Configuration Details

### RAG System Configuration

```python
# Konfigurasi RAG di backend/main.py
EMBEDDING_MODEL = "models/text-embedding-004"
GENERATIVE_MODEL = "gemini-1.5-flash"
RETRIEVAL_RESULTS = 15  # Jumlah chunks yang diambil
SCORE_THRESHOLD = 0.6   # Threshold similarity score
CONTEXT_CHUNKS = 8      # Chunks untuk context
```

### Frontend Configuration

```javascript
// Konfigurasi di frontend/src/api.js
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

// Tailwind theme configuration
// File: frontend/tailwind.config.js
theme: {
  extend: {
    colors: {
      'unand-green': '#22c55e',
      'unand-brown': '#a3a3a3'
    }
  }
}
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Backend tidak bisa start

```bash
# Cek Python version
python --version  # Harus 3.8+

# Cek dependencies
pip install -r backend/requirements.txt

# Cek environment variables
cat .env | grep GEMINI_API_KEY
```

#### 2. Frontend tidak bisa start

```bash
# Cek Node.js version
node --version  # Harus 16+

# Clear cache dan reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
```

#### 3. Database connection error

```bash
# Test database connection
python view_database.py

# Cek DATABASE_URL di .env
echo $DATABASE_URL
```

#### 4. Google OAuth error

- Pastikan Google Client ID dan Secret benar
- Cek authorized redirect URIs di Google Cloud Console
- Pastikan file `client_secret_*.json` ada di folder `backend/`

#### 5. Telegram Bot tidak respond

```bash
# Cek bot token
echo $TELEGRAM_BOT_TOKEN

# Test backend health
curl http://localhost:8000/health
```

## � Deployment ke Device Lain (Compress & Extract)

Jika Anda ingin memindahkan project ini ke device/server lain dengan cara compress dan extract folder:

### 1. Persiapan Sebelum Compress

```bash
# Di device asal, bersihkan file yang tidak perlu
cd chatbot-unand

# Hapus node_modules (akan diinstall ulang)
rm -rf frontend/node_modules
rm -rf frontend/package-lock.json

# Hapus Python cache
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -name "*.pyc" -delete

# Hapus vector database (akan rebuild otomatis)
rm -rf backend/vector_db/*

# Backup file .env (jangan ikut di compress jika ada credential sensitif)
cp .env .env.backup
```

### 2. Compress Project

```bash
# Compress seluruh folder (exclude sensitive files)
tar -czf chatbot-unand.tar.gz chatbot-unand/ --exclude='.env' --exclude='*.log'

# Atau menggunakan zip
zip -r chatbot-unand.zip chatbot-unand/ -x "*.env" "*.log"
```

### 3. Setup di Device Baru

#### Step 1: Extract dan Setup Environment

```bash
# Extract file
tar -xzf chatbot-unand.tar.gz
# atau: unzip chatbot-unand.zip

cd chatbot-unand

# Buat file .env baru dengan konfigurasi yang sesuai
cp .env.backup .env  # jika ada backup
# atau buat manual:
nano .env
```

#### Step 2: Install System Requirements

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip nodejs npm postgresql postgresql-contrib

# CentOS/RHEL
sudo yum install python3 python3-pip nodejs npm postgresql postgresql-server

# macOS (dengan Homebrew)
brew install python3 node postgresql

# Windows
# Download dan install dari website resmi:
# - Python 3.8+ dari python.org
# - Node.js 16+ dari nodejs.org
# - PostgreSQL dari postgresql.org
```

#### Step 3: Setup Database

```bash
# Start PostgreSQL service
sudo systemctl start postgresql  # Linux
brew services start postgresql   # macOS

# Buat database (jika menggunakan database lokal)
sudo -u postgres psql
CREATE DATABASE chatbot_unand_db;
CREATE USER chatbot_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE chatbot_unand_db TO chatbot_user;
\q

# Update DATABASE_URL di .env untuk database lokal
DATABASE_URL=postgresql://chatbot_user:your_password@localhost:5432/chatbot_unand_db
```

#### Step 4: Install Dependencies

```bash
# Install Python dependencies
cd backend
python3 -m pip install --upgrade pip
pip install -r requirements.txt
cd ..

# Install Node.js dependencies
cd frontend
npm install
cd ..
```

#### Step 5: Setup Google OAuth (Jika Diperlukan)

```bash
# Copy Google OAuth credentials file ke backend/
# File: client_secret_257608911345-h2bn2frj29lfnnm8mp0sqlk6pjn16nla.apps.googleusercontent.com.json

# Pastikan file ada di backend/
ls -la backend/client_secret_*.json

# Update .env dengan Google credentials
GOOGLE_CLIENT_ID=257608911345-h2bn2frj29lfnnm8mp0sqlk6pjn16nla.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_google_client_secret
```

#### Step 6: Verify Installation

```bash
# Test Python dependencies
cd backend
python -c "import fastapi, sqlalchemy, google.generativeai, faiss; print('Python dependencies OK')"

# Test Node.js dependencies
cd ../frontend
npm list --depth=0

# Test database connection
cd ..
python view_database.py
```

### 4. First Run Setup

```bash
# Terminal 1: Start Backend (akan auto-create tables dan rebuild index)
cd backend
python -m uvicorn main:app --reload --port 8000

# Terminal 2: Start Frontend
cd frontend
npm start

# Terminal 3: Start Telegram Bot (optional)
cd telegram-bot
python run_telegram_bot.py
```

### 5. Konfigurasi Khusus Device Baru

#### Update Environment Variables

```bash
# Edit .env sesuai environment baru
nano .env

# Contoh perubahan yang mungkin diperlukan:
DATABASE_URL=postgresql://new_user:new_password@new_host:5432/new_db
BACKEND_URL=http://new_ip:8000
GEMINI_API_KEY=your_api_key_here
```

#### Setup Firewall (Jika Diperlukan)

```bash
# Ubuntu/Debian
sudo ufw allow 3001  # Frontend
sudo ufw allow 8000  # Backend

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=3001/tcp
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload
```

#### Setup Reverse Proxy (Production)

```nginx
# /etc/nginx/sites-available/chatbot-unand
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:3001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 6. Troubleshooting Device Baru

#### Permission Issues

```bash
# Fix permission untuk Python packages
sudo chown -R $USER:$USER ~/.local/

# Fix permission untuk Node.js
sudo chown -R $USER:$USER ~/.npm
```

#### Port Conflicts

```bash
# Cek port yang digunakan
netstat -tulpn | grep :8000
netstat -tulpn | grep :3001

# Ganti port jika conflict
# Backend: python -m uvicorn main:app --reload --port 8001
# Frontend: PORT=3002 npm start
```

#### Memory Issues

```bash
# Increase Node.js memory limit
export NODE_OPTIONS="--max-old-space-size=4096"
npm start

# Monitor memory usage
htop
free -h
```

### 7. Checklist Deployment

- [ ] ✅ System requirements terinstall (Python 3.8+, Node.js 16+, PostgreSQL)
- [ ] ✅ Dependencies terinstall (pip install, npm install)
- [ ] ✅ Database setup dan connection berhasil
- [ ] ✅ Environment variables dikonfigurasi (.env)
- [ ] ✅ Google OAuth credentials tersedia
- [ ] ✅ Firewall/ports terbuka jika diperlukan
- [ ] ✅ Backend berjalan di http://localhost:8000
- [ ] ✅ Frontend berjalan di http://localhost:3002
- [ ] ✅ Database tables terbuat otomatis
- [ ] ✅ FAISS index rebuild berhasil
- [ ] ✅ Test login Google OAuth
- [ ] ✅ Test chat functionality
- [ ] ✅ Test admin panel login
- [ ] ✅ Test file upload/delete di admin
- [ ] ✅ Test Telegram bot (jika digunakan)

## 📖 Additional Documentation

- **Telegram Bot**: `telegram-bot/README.md` - Dokumentasi khusus bot
- **Environment Setup**: Lihat bagian "Setup & Installation" di atas
- **API Documentation**: http://localhost:8000/docs - Interactive API docs

## 🤝 Contributing

1. Fork repository
2. Buat feature branch: `git checkout -b feature/new-feature`
3. Commit changes: `git commit -am 'Add new feature'`
4. Push branch: `git push origin feature/new-feature`
5. Submit Pull Request

## 📞 Support

Untuk bantuan teknis atau pertanyaan:

- Buka issue di repository
- Lihat dokumentasi lengkap di README.md ini
- Test API di http://localhost:8000/docs
- Cek health endpoint: http://localhost:8000/health

## 📝 Changelog

### Version 2.0 (Latest) - December 2024

**🚀 Major Features Added:**

- ✅ Admin Panel dengan dashboard lengkap
- ✅ File upload/delete system dengan auto-rebuild FAISS
- ✅ User activity monitoring dengan timezone WIB
- ✅ Separate admin authentication system
- ✅ Sequential user numbering (1,2,3...)

**🔧 Technical Improvements:**

- ✅ Code cleanup - menghapus 7 file tidak digunakan
- ✅ Optimasi performa dengan pembersihan kode
- ✅ Update dokumentasi lengkap
- ✅ Timezone support untuk seluruh sistem
- ✅ Responsive admin interface

**🐛 Bug Fixes:**

- ✅ Fix port configuration (3002 untuk frontend)
- ✅ Fix admin authentication flow
- ✅ Fix knowledge base auto-rebuild
- ✅ Fix timezone display di admin dashboard

### Version 1.0 - November 2024

**🎯 Initial Release:**

- ✅ Website chatbot dengan Google OAuth
- ✅ Telegram bot integration
- ✅ RAG system dengan FAISS + Gemini AI
- ✅ PostgreSQL database dengan Railway
- ✅ Dark/light mode toggle
- ✅ UNAND branding dan responsive design

---

**UNAND Chatbot System** - Dikembangkan untuk Universitas Andalas
_"UNTUK KEDJAJAAN BANGSA"_ 🇮🇩
