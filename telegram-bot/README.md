# Tanyo Unand - Telegram Bot untuk UNAND

Bot Telegram yang menggunakan backend chatbot UNAND yang sudah ada untuk memberikan informasi tentang peraturan dan kebijakan Universitas Andalas.

Handle bot baru: `@ChatbotUnand_bot` (Tanyo Unand)

## 🎯 Fitur

- **Integrasi dengan Backend Existing**: Menggunakan API backend FastAPI yang sudah ada
- **Session Management**: Setiap user Telegram memiliki session terpisah
- **RAG System**: Memanfaatkan sistem Retrieval-Augmented Generation yang sudah ada
- **Document Search**: Pencarian dalam dokumen peraturan UNAND
- **Response Formatting**: Format response yang sesuai untuk Telegram

## 📋 Persyaratan

1. **Backend FastAPI** harus sudah berjalan (disarankan `https://api-chatbot.difunand.cloud`)
2. **Database PostgreSQL** harus sudah dikonfigurasi
3. **Environment Variables** yang diperlukan:
   - `TELEGRAM_BOT_TOKEN`: Token dari BotFather (Tanyo Unand)
   - `GEMINI_API_KEY`: API Key Google Gemini
   - `DATABASE_URL`: URL database PostgreSQL (untuk backend)

## 🚀 Cara Menjalankan

### 1. Persiapan Environment

Pastikan file `.env` di root project berisi:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
GEMINI_API_KEY=your_gemini_api_key_here
DATABASE_URL=
BACKEND_URL=https://api-chatbot.difunand.cloud
```

### 2. Install Dependencies

```bash
cd ../backend
pip install -r requirements.txt
```

### 3. Jalankan Backend (Terminal 1)

```bash
cd ../backend
python -m uvicorn main:app --reload --port 8000
```

### 4. Jalankan Telegram Bot (Terminal 2)

```bash
cd telegram-bot
python run_telegram_bot.py
```

## 🤖 Perintah Bot

- `/start` - Memulai percakapan dengan bot
- `/help` - Menampilkan bantuan penggunaan
- `/reset` - Reset session percakapan

## 📱 Cara Menggunakan

1. Cari bot `@junwar_bot` di Telegram
2. Kirim `/start` untuk memulai
3. Ajukan pertanyaan tentang peraturan UNAND
4. Bot akan mencari informasi dari dokumen resmi dan memberikan jawaban

## 🔧 Arsitektur

```
Telegram User
     ↓
Telegram Bot (telegram_bot.py)
     ↓ HTTP Request
Backend FastAPI (main.py)
     ↓
Database + RAG System + Gemini AI
     ↓
Response ke Telegram User
```

## 📊 Flow Data

1. **User mengirim pesan** ke Telegram Bot
2. **Bot membuat/menggunakan session** untuk user tersebut
3. **Bot mengirim HTTP request** ke backend FastAPI (`/chat` endpoint)
4. **Backend memproses** dengan RAG system dan Gemini AI
5. **Backend mengembalikan response** dalam format JSON
6. **Bot memformat response** dan mengirim ke user Telegram

## 🛠️ Troubleshooting

### Bot tidak merespon

- Pastikan backend FastAPI berjalan di port 8000
- Cek log backend untuk error
- Pastikan database PostgreSQL berjalan

### Error "Backend not available"

- Pastikan backend sudah running: `python -m uvicorn main:app --reload`
- Cek URL backend di environment variable `BACKEND_URL`

### Error database

- Pastikan PostgreSQL berjalan
- Cek connection string di `DATABASE_URL`
- Pastikan database `chatbot_unand_db` sudah dibuat

### Bot token error

- Pastikan `TELEGRAM_BOT_TOKEN` benar
- Dapatkan token baru dari @BotFather jika perlu

## 📝 Log dan Monitoring

Bot akan menampilkan log untuk:

- Koneksi ke backend
- Pesan yang diterima dari user
- Response yang dikirim
- Error yang terjadi

## 🔄 Session Management

- Setiap user Telegram memiliki session terpisah
- Session dibuat otomatis saat user pertama kali berinteraksi
- Session dapat direset dengan command `/reset`
- Session tersimpan di database backend

## 📚 Contoh Pertanyaan

- "Bagaimana prosedur pendaftaran mahasiswa baru?"
- "Apa saja persyaratan kelulusan?"
- "Bagaimana sistem penilaian di UNAND?"
- "Apa itu kurikulum OBE?"

## 🎨 Customization

Untuk mengubah perilaku bot, edit file `telegram_bot.py`:

- `format_response()`: Mengubah format response
- `welcome_message`: Mengubah pesan sambutan
- Handler functions: Menambah command baru

## 📞 Support

Jika ada masalah:

1. Cek log di terminal
2. Pastikan semua service berjalan
3. Cek environment variables
4. Restart backend dan bot jika perlu
