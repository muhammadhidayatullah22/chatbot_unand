import os
import logging
import aiohttp
import json
from typing import Dict, Optional
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Konfigurasi ---
# Default token di-set dari bot baru "Tanyo Unand". Disarankan override via env saat deploy.
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8282030014:AAH2IQ9xTH-KBdf2aXZWtf6KPW6Ni8QpfaE")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8001")  # URL backend FastAPI

# Konfigurasi logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Dictionary untuk menyimpan session_id per user Telegram
user_sessions: Dict[int, str] = {}

class BackendClient:
    """Client untuk berkomunikasi dengan backend FastAPI"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def create_session(self, title: str = "Telegram Chat") -> Optional[str]:
        """Membuat session baru di backend"""
        try:
            async with self.session.post(
                f"{self.base_url}/sessions",
                json={"title": title}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data["session_id"]
                else:
                    logger.error(f"Failed to create session: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return None
    
    async def send_message(self, query: str, session_id: Optional[str] = None) -> Dict:
        """Mengirim pesan ke backend dan mendapat response"""
        try:
            payload = {"query": query}
            if session_id:
                payload["session_id"] = session_id
            
            async with self.session.post(
                f"{self.base_url}/chat",
                json=payload
            ) as response:
                if response.status == 200:
                    # Backend bisa mengembalikan JSON atau stream (text/event-stream)
                    content_type = response.headers.get("Content-Type", "").lower()
                    if content_type.startswith("application/json"):
                        return await response.json()
                    # Jika streaming, baca sebagai teks penuh
                    if content_type.startswith("text/event-stream") or content_type.startswith("text/plain"):
                        text_body = await response.text()
                        return {
                            "response": text_body or "",
                            "session_id": session_id or "",
                            "sources": []
                        }
                else:
                    error_text = await response.text()
                    logger.error(f"Backend error {response.status}: {error_text}")
                    return {
                        "response": "Maaf, terjadi kesalahan saat memproses pertanyaan Anda.",
                        "session_id": session_id or "",
                        "sources": []
                    }
        except Exception as e:
            logger.error(f"Error sending message to backend: {e}")
            return {
                "response": "Maaf, tidak dapat terhubung ke server. Silakan coba lagi nanti.",
                "session_id": session_id or "",
                "sources": []
            }
    
    async def check_health(self) -> bool:
        """Mengecek status backend"""
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("status") == "OK"
                return False
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

async def get_or_create_session(user_id: int, username: str = None) -> str:
    """Mendapatkan atau membuat session untuk user Telegram"""
    if user_id in user_sessions:
        return user_sessions[user_id]
    
    # Buat session baru
    title = f"Telegram - {username or f'User {user_id}'}"
    async with BackendClient(BACKEND_URL) as client:
        session_id = await client.create_session(title)
        if session_id:
            user_sessions[user_id] = session_id
            logger.info(f"Created new session {session_id} for user {user_id}")
            return session_id
        else:
            logger.error(f"Failed to create session for user {user_id}")
            return ""

def format_response(response_text: str) -> str:
    """Format response untuk Telegram (menangani markdown dan panjang pesan)"""
    # Telegram memiliki batas 4096 karakter per pesan
    if len(response_text) > 4000:
        # Potong pesan dan tambahkan indikator
        response_text = response_text[:3900] + "\n\n... (pesan dipotong karena terlalu panjang)"
    
    # Escape karakter markdown yang bermasalah untuk Telegram
    # Telegram menggunakan MarkdownV2 yang lebih ketat
    return response_text

# --- Handler Perintah Telegram ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mengirim pesan sambutan saat perintah /start diterima."""
    user = update.effective_user
    
    # Cek koneksi backend
    async with BackendClient(BACKEND_URL) as client:
        is_healthy = await client.check_health()
        
    if not is_healthy:
        await update.message.reply_text(
            "⚠️ Maaf, sistem sedang tidak tersedia. Silakan coba lagi nanti."
        )
        return
    
    # Buat session untuk user
    session_id = await get_or_create_session(user.id, user.username)
    
    welcome_message = (
        f"🎓 Halo {user.first_name}! Selamat datang di **Tanyo Unand**!\n\n"
        "Saya adalah chatbot resmi Universitas Andalas yang dapat membantu Anda dengan:\n"
        "📋 Informasi peraturan dan kebijakan universitas\n"
        "📚 Panduan akademik dan kurikulum\n"
        "🏛️ Informasi umum tentang UNAND\n\n"
        "**UNTUK KEDJAJAAN BANGSA** 🇮🇩\n\n"
        "Silakan ajukan pertanyaan Anda, dan saya akan membantu berdasarkan dokumen resmi universitas!"
    )
    
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Menangani pesan teks dari pengguna dan memberikan jawaban."""
    user = update.effective_user
    user_query = update.message.text
    
    logger.info(f"Received message from {user.full_name} (ID: {user.id}): {user_query}")
    
    # Kirim indikator typing
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    # Dapatkan session untuk user
    session_id = await get_or_create_session(user.id, user.username)
    
    if not session_id:
        await update.message.reply_text(
            "❌ Maaf, terjadi kesalahan sistem. Silakan coba lagi dengan /start"
        )
        return
    
    # Kirim pesan ke backend
    async with BackendClient(BACKEND_URL) as client:
        # Cek kesehatan backend terlebih dahulu
        if not await client.check_health():
            await update.message.reply_text(
                "⚠️ Sistem sedang tidak tersedia. Silakan coba lagi nanti."
            )
            return
        
        # Kirim pertanyaan ke backend
        response_data = await client.send_message(user_query, session_id)
    
    # Format dan kirim response
    bot_response = response_data.get("response", "Maaf, tidak ada response dari sistem.")
    formatted_response = format_response(bot_response)
    
    try:
        await update.message.reply_text(formatted_response, parse_mode='Markdown')
    except Exception as e:
        # Jika markdown gagal, kirim tanpa formatting
        logger.warning(f"Markdown parsing failed: {e}")
        await update.message.reply_text(formatted_response)
    
    logger.info(f"Sent response to {user.full_name}")

async def reset_session(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reset session untuk user (command /reset)"""
    user = update.effective_user
    
    if user.id in user_sessions:
        del user_sessions[user.id]
        await update.message.reply_text(
            "✅ Session Anda telah direset. Percakapan baru akan dimulai."
        )
    else:
        await update.message.reply_text(
            "ℹ️ Anda belum memiliki session aktif."
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Menampilkan bantuan penggunaan bot"""
    help_text = (
        "🤖 **Bantuan Tanyo Unand**\n\n"
        "**Perintah yang tersedia:**\n"
        "/start - Memulai percakapan dengan bot\n"
        "/help - Menampilkan bantuan ini\n"
        "/reset - Reset session percakapan\n\n"
        "**Cara menggunakan:**\n"
        "• Kirim pertanyaan langsung tentang peraturan UNAND\n"
        "• Bot akan mencari informasi dari dokumen resmi\n"
        "• Anda bisa bertanya tentang akademik, peraturan, atau info umum\n\n"
        "**Contoh pertanyaan:**\n"
        "• Bagaimana prosedur pendaftaran mahasiswa baru?\n"
        "• Apa saja persyaratan kelulusan?\n"
        "• Bagaimana sistem penilaian di UNAND?\n\n"
        "**UNTUK KEDJAJAAN BANGSA** 🇮🇩"
    )
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

# --- Fungsi Utama untuk Menjalankan Bot ---

def main() -> None:
    """Menjalankan bot."""
    logger.info("Starting Tanyo Unand Bot...")

    # Inisialisasi aplikasi bot
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Tambahkan handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("reset", reset_session))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Tanyo Unand Bot started and ready to receive messages...")

    # Jalankan bot dengan polling
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.critical(f"Fatal error running bot: {e}")
