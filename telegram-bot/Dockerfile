# syntax=docker/dockerfile:1

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps (optional)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl && rm -rf /var/lib/apt/lists/*

# Install python deps (only bot requirements)
RUN pip install --no-cache-dir \
    python-telegram-bot==21.6 \
    aiohttp==3.9.5 \
    requests==2.32.3 \
    python-dotenv==1.0.1

# Copy bot sources
COPY . /app

# Runtime env (override in compose/portainer)
ENV BACKEND_URL=https://api-chatbot.difunand.cloud \
    TELEGRAM_BOT_TOKEN=7977126581:AAGuPriDsRyInaNjR34_duG5DWWNbfu6V4E \
    GEMINI_API_KEY=AIzaSyAM0cEUZ-4tZapGhUA3oJi5ea-FduA8yo0

# Run
CMD ["python", "run_telegram_bot.py"]


