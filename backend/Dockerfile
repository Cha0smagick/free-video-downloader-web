FROM python:3.12-slim

# ffmpeg: fusionar bestvideo+bestaudio · node+npm: servidor PO Token (BotGuard emulado) · git: clonar el generador
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg nodejs npm git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt bgutil-ytdlp-pot-provider

# Generador de PO Tokens (bgutil): compilado en build time; corre en 127.0.0.1:4416 dentro del contenedor
RUN git clone --single-branch --depth 1 https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git /app/pot-provider \
    && cd /app/pot-provider/server \
    && npm ci \
    && npx tsc

COPY main.py .

EXPOSE 7860

# El servidor PO Token corre en segundo plano; uvicorn en primer plano
CMD ["sh", "-c", "node /app/pot-provider/server/build/main.js & exec uvicorn main:app --host 0.0.0.0 --port 7860"]
