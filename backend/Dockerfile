# 1. Base Image dan Setup Lingkungan
FROM python:3.10-slim

# Variabel ini memastikan output Python segera dicetak (penting untuk logging)
ENV PYTHONUNBUFFERED 1
# Atur direktori kerja utama
WORKDIR /app

# 2. Instalasi Dependensi Sistem
# build-essential diperlukan untuk mengkompilasi dependensi native (Numpy/Faiss)
# libpq-dev diperlukan untuk mengkompilasi psycopg2 (driver PostgreSQL)
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# 3. Instalasi Dependensi Python
# Salin requirements.txt dan instal semua paket
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Variabel Lingkungan Non-Sensitif
# Variabel ini akan tersedia di dalam container
ENV GOOGLE_CLIENT_ID="257608911345-h2bn2frj29lfnnm8mp0sqlk6pjn16nla.apps.googleusercontent.com"
ENV GOOGLE_CLOUD_PROJECT="chatbot-unand-462320"
ENV GOOGLE_CLOUD_LOCATION="asia-southeast2"
ENV BACKEND_URL="http://0.0.0.0:8001"

# --- Masalah Potensial: GEMINI_API_KEY (Jika lupa -e) ---
# Kami tidak menetapkan nilai di sini untuk rahasia, tetapi
# jika aplikasi bergantung pada nilai default ini di main.py, 
# Anda harus memastikan ia disuntikkan saat runtime.
# Contoh setting default non-rahasia:
# ENV GEMINI_API_KEY_DEFAULT="placeholder" 
# Gunakan -e GEMINI_API_KEY="..." saat docker run

# 5. File Kredensial Lokal
# Salin file JSON yang ditunjukkan oleh GOOGLE_APPLICATION_CREDENTIALS
COPY client_secret_257608911345-h2bn2frj29lfnnm8mp0sqlk6pjn16nla.apps.googleusercontent.com.json /app/gcp-credentials.json

# Setel izin baca ke file ini untuk memitigasi masalah permission
RUN chmod 644 /app/gcp-credentials.json

ENV GOOGLE_APPLICATION_CREDENTIALS="/app/gcp-credentials.json"

# 6. Salin Kode Aplikasi dan Index FAISS
# Salin semua file dari direktori build (backend)
COPY . .
# Salin index FAISS yang sudah dibuat
COPY vector_db/ ./vector_db/

# 7. Runtime Configuration
EXPOSE 8001

# Perintah utama saat container dijalankan
# Host 0.0.0.0 agar dapat diakses dari luar container
# Variabel sensitif (DB_URL, API_KEY, SECRET_KEY) diatur via docker run -e
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
