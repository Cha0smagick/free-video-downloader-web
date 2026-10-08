# Video Downloader (yt-dlp)

Web minimalista para descargar videos de **YouTube** y de **miles de sitios web** (todo lo soportado por [yt-dlp](https://github.com/yt-dlp/yt-dlp)). Gratis, sin registro y sin límites de plataforma.

- **Frontend**: HTML/CSS/JS vanilla, sin build → se despliega en **GitHub Pages** (con GitHub Actions).
- **Backend**: FastAPI + yt-dlp + ffmpeg en Docker → se despliega gratis en **Hugging Face Spaces**.

---

## Estructura

```
frontend/                  → GitHub Pages
  index.html               → UI: pegar URL → progreso → descargar
  style.css                → tema dark minimalista
  app.js                   → polling de progreso, sin frameworks
backend/                   → Hugging Face Spaces (Docker)
  main.py                  → API + yt-dlp (jobs en memoria + progress hooks)
  requirements.txt         → fastapi, uvicorn, yt-dlp
  Dockerfile               → imagen con ffmpeg incluido
.github/workflows/pages.yml→ deploy del frontend a GitHub Pages
PLAN.md                    → plan de desarrollo paso a paso
```

## API del backend

| Endpoint | Método | Descripción |
|---|---|---|
| `/api/download` | POST | `{ "url": "..." }` → `{ "job_id": "..." }` |
| `/api/progress/{job_id}` | GET | `{ status, progress, speed, eta, title, filesize, error, file_ready }` |
| `/api/file/{job_id}` | GET | Descarga del archivo terminado (attachment) |
| `/api/health` | GET | `{ "status": "ok" }` |

---

## Ejecutar en local

### Backend
```bash
cd backend
pip install -r requirements.txt   # requiere ffmpeg instalado en el sistema
python main.py                    # http://localhost:7860
```

### Frontend
Abrir `frontend/index.html` directamente en el navegador (el backend por defecto es `http://localhost:7860`), o servirlo:
```bash
cd frontend
python -m http.server 8080        # http://localhost:8080
```

---

## Despliegue (100% gratis)

### 1. Backend en Hugging Face Spaces (recomendado)

1. Crea una cuenta gratis en [huggingface.co](https://huggingface.co) → **New Space**.
2. Configura: **SDK = Docker**, nombre p. ej. `video-downloader`.
3. Sube los 3 archivos de `backend/` (`main.py`, `requirements.txt`, `Dockerfile`) al Space (arrastrar y soltar en la web o con git).
4. El Space construye la imagen (instala ffmpeg solo) y queda en:
   `https://TU-USUARIO-video-downloader.hf.space`
5. Comprueba `https://TU-USUARIO-video-downloader.hf.space/api/health` → `{"status":"ok"}`.

**Notas**: el Space gratuito duerme tras ~48 h de inactividad (arranque en frío ~1-2 min). Los archivos descargados se borran automáticamente a la 1 hora.

### 2. Frontend en GitHub Pages

1. Sube este repositorio a GitHub (rama `main`).
2. En el repo: **Settings → Pages → Source: GitHub Actions**.
3. El workflow `.github/workflows/pages.yml` ya está incluido: en cada push a `main` despliega `frontend/` automáticamente.
4. Tu página quedará en `https://TU-USUARIO.github.io/REPO/`.

### 3. Conectar el frontend con el backend

Abre tu página en GitHub Pages → **⚙ Configuración del backend** → pega la URL del Space:
```
https://TU-USUARIO-video-downloader.hf.space
```
Se guarda en `localStorage` (solo hay que hacerlo una vez por navegador).

> ⚠️ **Importante**: si la página está en HTTPS (GitHub Pages), el backend **debe** estar en HTTPS. Un backend en `http://` será bloqueado por el navegador (mixed content). Hugging Face Spaces da HTTPS automático.

---

## Alternativa: Oracle Cloud Free Tier

Si prefieres más potencia y siempre encendido (sin cold start), el Always Free de Oracle Cloud ofrece hasta 4 OCPU Arm + 24 GB RAM:

1. Crea cuenta (requiere tarjeta de crédito para verificación; los rechazos al registrarse son comunes).
2. Crea una instancia **VM Standard A1.Flex** (Ubuntu) dentro de una VCN con puerto 7860 abierto (Security List / ingress rule TCP 7860, origen 0.0.0.0/0).
3. Conéctate por SSH e instala:
   ```bash
   sudo apt update && sudo apt install -y ffmpeg python3-pip
   pip3 install fastapi uvicorn yt-dlp
   ```
4. Copia `backend/main.py` y crea el servicio systemd:
   ```ini
   # /etc/systemd/system/ytdlp-web.service
   [Unit]
   Description=Video Downloader API
   After=network.target

   [Service]
   User=ubuntu
   WorkingDirectory=/home/ubuntu/ytdlp-web
   ExecStart=/usr/local/bin/uvicorn main:app --host 0.0.0.0 --port 7860
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```
   ```bash
   sudo systemctl enable --now ytdlp-web
   ```
5. **HTTPS obligatorio**: el frontend de GitHub Pages exige HTTPS en el backend. Opciones:
   - Tu propio dominio apuntando a la IP pública (registro A) + [Caddy](https://caddyserver.com) o nginx + certbot (Let's Encrypt) como reverse proxy en el puerto 443.
   - Sin dominio propio, usa Hugging Face Spaces (HTTPS automático) — más simple.
6. Nota: las instancias Arm a veces no tienen capacidad disponible en tu región; las instancias idle pueden ser reclamadas si no hay uso.

---

## Seguridad y límites

- El backend no requiere API keys; CORS está abierto (`*`) para que GitHub Pages pueda llamarlo.
- Los jobs y archivos viven en memoria/disco temporal del servidor y se limpian a la 1 hora (no hay almacenamiento persistente — es una herramienta de descarga, no un hosting).
- yt-dlp se actualiza con frecuencia (YouTube cambia su API): en HF Spaces reconstruye el Space o usa `pip install -U yt-dlp` en local si una descarga falla.
