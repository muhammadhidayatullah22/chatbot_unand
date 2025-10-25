# ===============================================
# STAGE 1: Build Image (Mengompilasi Aplikasi React)
# ===============================================

# Menggunakan Node versi stabil sebagai base image untuk build
FROM node:20-alpine AS builder

# Tentukan argumen build yang akan diterima saat menjalankan 'docker build'
ARG NODE_ENV=production
ARG REACT_APP_GOOGLE_CLIENT_ID # <--- INI PENTING! Menerima Client ID sebagai argumen

# Tetapkan Environment Variable (ENV) menggunakan nilai dari ARG.
# Ini memastikan bahwa 'npm run build' dapat melihat dan menyematkan Client ID.
ENV REACT_APP_GOOGLE_CLIENT_ID=$REACT_APP_GOOGLE_CLIENT_ID
ENV NODE_ENV=$NODE_ENV

# Tentukan direktori kerja di dalam container
WORKDIR /app

# Salin file package.json dan package-lock.json untuk caching instalasi
COPY package.json package-lock.json ./

# Instal semua dependensi
RUN npm install

# Salin seluruh kode sumber frontend
COPY . .

# Jalankan proses build Create React App
# Output build akan berada di folder /app/build
RUN npm run build

# ===============================================
# STAGE 2: Runner Image (Server Statis Minimalis)
# ===============================================

# Menggunakan image node minimalis untuk menjalankan server file statis
FROM node:20-alpine AS runner

# Tentukan environment runner
ENV NODE_ENV production
ENV PORT 3000

WORKDIR /app

# Salin HANYA hasil build (folder 'build') dari stage 'builder'
# Ini adalah praktik terbaik (multi-stage build) untuk ukuran image yang kecil
COPY --from=builder /app/build ./build

# Instal 'serve' untuk melayani file statis dari hasil build
RUN npm install -g serve

# Ekspos port
EXPOSE 3000

# Perintah yang dijalankan saat container dimulai: 
# Melayani output build dari folder /app/build pada Port 3000
CMD ["serve", "-s", "build", "-l", "3000"]