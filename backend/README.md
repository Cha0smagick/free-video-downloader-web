# Video Downloader API (backend)

Backend FastAPI + yt-dlp para la web de descarga de videos. Despliegue gratis en **Render** (Free tier, Docker).

> **Nota (2026-10-08)**: Hugging Face Spaces ahora exige plan pago (PRO) para Spaces con Docker o Gradio — solo los Static son gratis. Render sigue ofreciendo web services gratis (verificado en docs oficiales).

## Subir a Render (Free tier)

1. Sube el repositorio a GitHub (rama `main`).
2. Crea cuenta gratis en [render.com](https://render.com) — corre sin tarjeta (si agotas el ancho de banda mensual sin tarjeta, tus servicios gratuitos se pausan hasta el mes siguiente).
3. Dashboard → **New → Web Service** → conecta el repo → configura:
   - **Root Directory**: `backend`
   - **Runtime**: Docker (detecta el Dockerfile automáticamente)
   - **Instance Type**: Free
4. Render construye la imagen (el Dockerfile instala ffmpeg) y expone HTTPS automático en:
   `https://TU-SERVICIO.onrender.com`
5. Comprueba `https://TU-SERVICIO.onrender.com/api/health` → `{"status":"ok"}`.

## Limitaciones del Free tier (docs oficiales de Render)

- El servicio duerme tras 15 min sin tráfico; la primera petición tarda ~1 min en despertarlo.
- RAM 512 MB / 0.1 CPU: clips y videos cortos OK; videos muy largos (2+ h, 1080p) pueden agotar el disco efímero.
- Sin disco persistente: los archivos se pierden al redeploy (el backend ya los borra a la 1 hora).
- Sin shell SSH. Ancho de banda de salida contra el límite mensual gratis.

## Cookies para YouTube

YouTube bloquea descargas desde IPs de datacenter (Render) con `Sign in to confirm you're not a bot`
sin sesión autenticada. Otras plataformas normalmente no requieren cookies.

Exporta las cookies del navegador (sesión de YouTube iniciada) con la extensión
**[Get cookies.txt](https://chromewebstore.google.com/detail/get-cookiestxt/bgaddhkoddajcdgocldbbfleckgcbcid)** y:

1. Guárdalas como `cookies.txt` junto a `main.py` en un **repositorio privado** (tokens de sesión —
   si se filtran, cierra sesión en YouTube para revocarlas), **o**
2. Añádelas como **Secret File** en Render: Environment → Secret Files → `/etc/secrets/cookies.txt`
   (disponibilidad en free tier sin verificar), **o**
3. Define la variable de entorno `YTDLP_COOKIES_FILE` con la ruta absoluta al archivo.

El backend las detecta en ese orden y las usa automáticamente. La portada `/` muestra
**`Cookies: activos ✓`** cuando están configuradas.

## Ejecutar en local

```bash
pip install -r requirements.txt   # requiere ffmpeg instalado en el sistema
python main.py                    # http://localhost:7860
```

## Endpoints

- `GET /api/health` → `{"status": "ok"}`
- `POST /api/download` body `{"url": "https://..."}` → `{"job_id": "..."}`
- `GET /api/progress/{job_id}` → estado, %, velocidad, ETA
- `GET /api/file/{job_id}` → archivo MP4

## Notas

- Los archivos se eliminan 1 hora después de crearse (almacenamiento efímero).
- yt-dlp soporta miles de sitios (YouTube, TikTok, Twitter/X, Instagram, Vimeo, etc.).
- yt-dlp se actualiza con frecuencia: en Render haz **Manual Deploy → Clear build cache** si una descarga falla.
- Documentación interactiva: `https://TU-SERVICIO.onrender.com/docs`
