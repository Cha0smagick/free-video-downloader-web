---
title: Video Downloader API
emoji: 📥
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# Video Downloader API (backend)

Backend FastAPI + yt-dlp para la web de descarga de videos. Despliegue en Hugging Face Spaces (Docker).

## Subir a Hugging Face Spaces

1. Crea una cuenta gratis en huggingface.co.
2. **New Space** → nombre p. ej. `video-downloader-api` → SDK: **Docker** → Hardware: **CPU basic (free)** → público o privado.
3. Sube los archivos de esta carpeta (`main.py`, `requirements.txt`, `Dockerfile`) y este `README.md` a la raíz del Space (con la web de HF o con git: `git remote add space https://huggingface.co/spaces/TU_USUARIO/video-downloader-api`).
4. El Space construye la imagen (instala ffmpeg) y expone `https://TU_USUARIO-video-downloader-api.hf.space` con HTTPS automático.

## Endpoints

- `GET /api/health` → `{"status": "ok"}`
- `POST /api/download` body `{"url": "https://..."}` → `{"job_id": "..."}`
- `GET /api/progress/{job_id}` → estado, %, velocidad, ETA
- `GET /api/file/{job_id}` → archivo MP4

## Notas

- Los archivos se eliminan 1 hora después de crearse (almacenamiento efímero).
- yt-dlp soporta miles de sitios (YouTube, TikTok, Twitter/X, Instagram, Vimeo, etc.).
- Documentación interactiva: `https://TU_USUARIO-video-downloader-api.hf.space/docs`
