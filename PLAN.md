# PLAN DE DESARROLLO — Web de Descarga de Videos (yt-dlp)

> Plan atómico, paso a paso. Marcar cada paso `[x]` al completarlo. No pasar al siguiente sin verificar el actual.

## Objetivo
Web minimalista + backend yt-dlp que descarga videos de YouTube y de cualquier plataforma soportada por yt-dlp (miles de sitios). 100% gratuito:
- **Frontend** estático → GitHub Pages (con GitHub Actions CI/CD).
- **Backend** Python (FastAPI + yt-dlp) → Hugging Face Spaces (gratis, HTTPS automático).

## Arquitectura (locked con el usuario)
```
frontend/                  → GitHub Pages (Actions en push a main)
  index.html               → UI minimalista: pegar URL → progreso → descargar
  style.css                → estilos minimalistas, dark
  app.js                   → polling de progreso, sin frameworks
backend/                   → Hugging Face Spaces (Docker)
  main.py                  → FastAPI + yt-dlp, jobs en memoria + progress hooks
  requirements.txt         → fastapi, uvicorn, yt-dlp
  Dockerfile               → imagen con ffmpeg instalado (merge bestvideo+audio)
.github/workflows/
  pages.yml                → deploy frontend a GitHub Pages
```
Endpoints: `POST /api/download {url}` → job_id · `GET /api/progress/{job_id}` → estado/% · `GET /api/file/{job_id}` → stream del archivo · `GET /api/health`. CORS habilitado para el origen de GitHub Pages.

## Entorno verificado (2026-10-08)
- Python 3.12.3, pip 26.2.1
- ffmpeg: `C:\Users\USER\AppData\Local\Microsoft\WinGet\Links\ffmpeg.EXE` ✓
- yt-dlp 2026.08.19 ✓ · fastapi 0.141.1 ✓ (sin installs locales)
- Nota: shell local es PowerShell 5.1 — usar sintaxis PS o Python para comandos compuestos.

## Pasos

### Paso 1 — Scaffold
- [ ] Crear `frontend/`, `backend/`, `.github/workflows/`
- [ ] Crear `.gitignore` (venv, __pycache__, descargas temporales)
- [ ] Inspeccionar y limpiar la entrada basura `undefined` del directorio raíz

### Paso 2 — Backend (FastAPI + yt-dlp)
- [x] `backend/main.py`: jobs en memoria (dict job_id → estado), progress hook de yt-dlp, descarga en hilo de fondo, endpoints completos + CORS
- [x] `backend/requirements.txt`: fastapi, uvicorn, yt-dlp
- [x] `backend/Dockerfile`: base python:3.12-slim, `apt-get install -y ffmpeg`, puerto 7860 (HF Spaces requiere 7860)
- [x] Verificar: arrancar servidor, `GET /api/health` responde ✓ ({"status":"ok"})

### Paso 3 — Frontend minimalista
- [x] `frontend/index.html`: input de URL + botón + barra de progreso + área de descarga
- [x] `frontend/style.css`: dark minimalista, sin dependencias
- [x] `frontend/app.js`: POST /api/download → poll /api/progress → enlace a /api/file; URL del backend configurable (localStorage, con valor por defecto)
- [x] Verificar: abrir index.html en navegador, flujo completo contra backend local ✓ (Chromium headless, enlace generado)

### Paso 4 — GitHub Actions (Pages)
- [x] `.github/workflows/pages.yml`: deploy de `frontend/` a GitHub Pages en push a main
- [x] Verificar sintaxis del workflow (revisión manual: acciones oficiales v4/v5/v3, permisos y concurrency correctos)

### Paso 5 — Verificación local de punta a punta
- [x] Arrancar backend con uvicorn
- [x] Descarga real de un video corto de YouTube vía API ✓ ("Me at the zoo", 100%, 475989 bytes servidos)
- [x] Progreso reportado correctamente (poll)
- [x] Archivo servido con Content-Disposition correcto
- [x] Frontend en navegador completa el flujo ✓ (Chromium headless + Playwright: fill → click → progreso → enlace de descarga, 465 KB)

### Paso 6 — README y deploy
- [x] `README.md`: instrucciones deploy HF Spaces (primario, con Dockerfile) + guía alternativa Oracle Cloud Free Tier (VCN, SSH, systemd, HTTPS con dominio + Let's Encrypt) + GitHub Pages + cómo apuntar el frontend al backend desplegado

### Paso 7 — Cierre
- [~] `git init` + commit inicial — OMITIDO: el usuario no lo pidió explícitamente (ejecutar cuando lo pida)
- [x] Resumen final: qué cambió, dónde, evidencia de verificación

### Paso 11 - PO Tokens: navegador emulado para YouTube en la nube
- [x] Auditoría (README oficial bgutil-ytdlp-pot-provider): plugin `pip install bgutil-ytdlp-pot-provider` + generador Node HTTP en 127.0.0.1:4416 (recomendado); caveat oficial: PO Token NO evade restricciones por IP (datacenter puede seguir pidiendo cookies)
- [x] Dockerfile: node+npm+git; clona generador bgutil, `npm ci` + `npx tsc`; CMD corre servidor PO (127.0.0.1:4416) en background + uvicorn — commit af5352e
- [x] requirements.txt: + bgutil-ytdlp-pot-provider — commit af5352e; backend/README.md: sección PO Tokens — commit 3104b64
- [x] Verificación local: plugin cargado (`PO Token Providers: bgutil:http-2.0.2 (external)`, bgutil:script-node/deno unavailable — esperado sin repo local)
- [~] Pendiente (usuario): Render auto-rebuild (npm ci tarda unos min) → probar descarga de YouTube en https://free-video-downloader-web.onrender.com — si sigue el error "Sign in to confirm...", añadir cookies (sección README, fix más fiable para datacenter IPs)
### Paso 8 — Pivot de hosting: HF Spaces pago → Render Free
- [x] Verificar de docs oficiales: HF Spaces exige plan pago (PRO) para Docker/Gradio; solo Static gratis. Render Free sí ofrece web services gratis (HTTPS gestionado ✓, Docker no excluido ✓, corre sin tarjeta ✓, sleep 15 min + ~1 min wake ✓)
- [x] README.md: Render Free como backend principal ( pasos de deploy + limitaciones del free tier )
- [x] backend/README.md: reescrito con deploy en Render Free + nota de HF pago
- [x] frontend (index.html + app.js): notas actualizadas de HF → Render
- [~] Desplegar en Render real: requiere cuenta GitHub + repo remoto del usuario (pendiente de acción del usuario)

### Paso 9 — Correcciones post-deploy
- [x] Verificado backend desplegado en Render: `GET /api/health` → 200 `{"status":"ok"}` (el servicio SÍ está vivo)
- [x] Diagnóstico: `{"detail":"Not Found"}` en `/` = FastAPI sin ruta raíz (cosmético) · YouTube bloquea IPs de datacenter (Render) sin cookies → error real de descarga
- [x] `main.py`: ruta raíz `/` con página de estado (endpoints + estado de cookies)
- [x] `main.py`: soporte cookies multi-ruta (env `YTDLP_COOKIES_FILE` → `/etc/secrets/cookies.txt` Render Secret Files → `cookies.txt` junto a main.py); fix Ruff PIE810
- [x] README: sección cookies (exportar del navegador, repo privado o Secret Files)
- [x] Verificación local de la ruta raíz y estado de cookies (GET / → 200 "Cookies: activos ✓" con cookies.txt dummy; dummy eliminado tras la prueba)

## Criterios de éxito
- Backend descarga un video real de YouTube localmente y sirve el archivo ✓ verificado
- Frontend pega URL, muestra progreso real y permite descargar ✓ verificado
- Deploy listo: Dockerfile válido para Render Free + workflow de Pages funcional
- "Cualquier plataforma": yt-dlp soporta miles de sitios por defecto (sin filtro de dominio); YouTube desde la nube requiere cookies (implementado)

### Paso 10 - Fix UX: backend por defecto automatico y transparente
- [x] Diagnostico: el default de ytdlp_backend_url seguia siendo `http://localhost:7860` (HTTP) -> en la pagina HTTPS de GitHub Pages el navegador bloquea el fetch (mixed content) + no hay backend local -> advertencia de protocolo y "Failed to fetch"
- [x] `app.js`: `DEFAULT_BACKEND` -> `https://free-video-downloader-web.onrender.com` (funciona sin configurar nada; override local sigue disponible via Configuracion)
- [x] `index.html`: placeholder del input de backend -> URL de Render
- [x] Verificacion: `node --check app.js` OK
- [x] Subir `frontend/app.js` + `frontend/index.html` a GitHub (auto-deploy de Pages) — commit 9779ddc pusheado a origin/main
- [x] Migración automática: `getBackend()` descarta valores `localhost`/`127.0.0.1` guardados en localStorage y usa el default Render — commit 17a8819 (cero configuración: pegar link → progreso → descarga directa)
