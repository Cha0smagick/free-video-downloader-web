# Video Downloader (yt-dlp)

Web minimalista para descargar videos de **YouTube** y de **miles de sitios web** (todo lo soportado por [yt-dlp](https://github.com/yt-dlp/yt-dlp)). Gratis, sin registro y sin límites de plataforma.

- **Frontend**: HTML/CSS/JS vanilla, sin build → se despliega en **GitHub Pages** (con GitHub Actions).
- **Backend**: FastAPI + yt-dlp + ffmpeg en Docker → se despliega gratis en **Render** (Free tier).

---

## Estructura

```
frontend/                  → GitHub Pages
  index.html               → UI: pegar URL → progreso → descargar
  style.css                → tema dark minimalista
  app.js                   → polling de progreso, sin frameworks
backend/                   → Render Free (Docker)
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

### 1. Backend en Render (Free tier, recomendado)

> **Nota (2026-10-08)**: Hugging Face Spaces ahora exige plan pago (PRO) para crear Spaces con Docker o Gradio — solo los Static son gratis. Render sigue ofreciendo **web services gratis** (verificado en docs oficiales de Render).

1. Sube este repositorio a GitHub (rama `main`).
2. Crea cuenta gratis en [render.com](https://render.com) — **sin tarjeta**: corre sin método de pago (si agotas el ancho de banda mensual sin tarjeta, tus servicios gratuitos se pausan hasta el mes siguiente).
3. Dashboard → **New → Web Service** → conecta el repo de GitHub → configura:
   - **Root Directory**: `backend`
   - **Runtime**: Docker (detecta el Dockerfile automáticamente)
   - **Instance Type**: Free
4. Render construye la imagen (el Dockerfile instala ffmpeg) y expone **HTTPS automático** en:
   `https://TU-SERVICIO.onrender.com`
5. Comprueba `https://TU-SERVICIO.onrender.com/api/health` → `{"status":"ok"}`.

**Limitaciones del Free tier** (de docs oficiales de Render):
- El servicio **duerme tras 15 min sin tráfico**; la primera petición tarda ~1 min en despertarlo.
- RAM 512 MB / 0.1 CPU: perfecto para clips y videos cortos; videos muy largos (2+ h, 1080p) pueden agotar el disco efímero.
- Sin disco persistente: los archivos se pierden al redeploy (el backend ya los borra a la 1 hora por su cuenta).
- Sin shell SSH. El ancho de banda de salida cuenta contra el límite mensual gratis.

### 2. Frontend en GitHub Pages

1. Sube este repositorio a GitHub (rama `main`).
2. En el repo: **Settings → Pages → Source: GitHub Actions**.
3. El workflow `.github/workflows/pages.yml` ya está incluido: en cada push a `main` despliega `frontend/` automáticamente.
4. Tu página quedará en `https://TU-USUARIO.github.io/REPO/`.

### 3. Conectar el frontend con el backend

Abre tu página en GitHub Pages → **⚙ Configuración del backend** → pega la URL del backend:
```
https://TU-SERVICIO.onrender.com
```
Se guarda en `localStorage` (solo hay que hacerlo una vez por navegador).

> ⚠️ **Importante**: si la página está en HTTPS (GitHub Pages), el backend **debe** estar en HTTPS. Un backend en `http://` será bloqueado por el navegador (mixed content). Render da HTTPS automático.

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
   - Sin dominio propio, usa Render Free (HTTPS automático) — más simple.
6. Nota: las instancias Arm a veces no tienen capacidad disponible en tu región; las instancias idle pueden ser reclamadas si no hay uso.

---

## Seguridad y límites

- El backend no requiere API keys; CORS está abierto (`*`) para que GitHub Pages pueda llamarlo.
- Los jobs y archivos viven en memoria/disco temporal del servidor y se limpian a la 1 hora (no hay almacenamiento persistente — es una herramienta de descarga, no un hosting).
- yt-dlp se actualiza con frecuencia (YouTube cambia su API): en Render haz **Manual Deploy → Clear build cache** o usa `pip install -U yt-dlp` en local si una descarga falla.
