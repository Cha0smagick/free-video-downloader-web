"""Backend de descarga de videos — FastAPI + yt-dlp.

Endpoints:
- POST /api/download {url}  -> {job_id}
- GET  /api/progress/{id}   -> estado y progreso del job
- GET  /api/file/{id}       -> stream del archivo descargado
- GET  /api/health          -> {"status": "ok"}

Los jobs viven en memoria (dict). Los archivos se guardan en DOWNLOAD_DIR y un
janitor los elimina 1 hora después de su creación (idóneo para almacenamiento
efímero de Hugging Face Spaces / Render).
"""
import threading
import time
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from yt_dlp import YoutubeDL

DOWNLOAD_DIR = Path(__file__).parent / "downloads"
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

FILE_TTL_SECONDS = 60 * 60  # 1 hora de vida para cada archivo
JANITOR_INTERVAL_SECONDS = 600  # 10 minutos

app = FastAPI(title="Video Downloader API", docs_url="/docs")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

_jobs: dict[str, dict] = {}
_lock = threading.Lock()


class DownloadRequest(BaseModel):
    url: str


def _set_job(job_id: str, **fields: object) -> None:
    with _lock:
        _jobs[job_id].update(fields)


def _make_hooks(job_id: str):
    """Hooks de yt-dlp cerrados sobre el job_id correspondiente."""

    def progress_hook(d: dict) -> None:
        if d.get("status") == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            downloaded = d.get("downloaded_bytes") or 0
            pct = round(downloaded / total * 100, 1) if total else None
            _set_job(
                job_id,
                status="downloading",
                progress=pct,
                speed=d.get("speed"),
                eta=d.get("eta"),
            )
        elif d.get("status") == "finished":
            _set_job(job_id, status="processing", progress=100.0)

    def postproc_hook(d: dict) -> None:
        if d.get("status") == "started":
            _set_job(job_id, status="processing")

    return progress_hook, postproc_hook


def _find_final_file(info: dict) -> Path | None:
    """Localiza el archivo final: el merge puede cambiar la extensión."""
    vid = str(info.get("id") or "")
    if not vid:
        return None
    candidates = [p for p in DOWNLOAD_DIR.iterdir() if p.is_file() and vid in p.name]
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def _worker(job_id: str, url: str) -> None:
    progress_hook, postproc_hook = _make_hooks(job_id)
    ydl_opts = {
        # bestvideo+bestaudio con ffmpeg; sin filtro de dominio: yt-dlp soporta
        # miles de sitios por defecto ("cualquier plataforma").
        "format": "bestvideo*+bestaudio/best",
        "outtmpl": str(DOWNLOAD_DIR / "%(title).150B-%(id)s.%(ext)s"),
        "merge_output_format": "mp4",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "socket_timeout": 30,
        "retries": 3,
        "progress_hooks": [progress_hook],
        "postprocessor_hooks": [postproc_hook],
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
        # Guardas: playlist inesperada o id ausente
        if "entries" in info and isinstance(info.get("entries"), list) and info["entries"]:
            info = info["entries"][0]
        filepath = _find_final_file(info)
        if filepath is None:
            raise RuntimeError("No se encontró el archivo descargado")
        _set_job(
            job_id,
            status="done",
            progress=100.0,
            filepath=str(filepath),
            filename=filepath.name,
            title=info.get("title") or filepath.stem,
            filesize=filepath.stat().st_size,
        )
    except Exception as exc:  # noqa: BLE001 — el error viaja al cliente vía /api/progress
        _set_job(job_id, status="error", error=str(exc)[:500])


def _janitor() -> None:
    """Elimina jobs y archivos con más de FILE_TTL_SECONDS de antigüedad."""
    while True:
        time.sleep(JANITOR_INTERVAL_SECONDS)
        cutoff = time.time() - FILE_TTL_SECONDS
        with _lock:
            expired = [jid for jid, j in _jobs.items() if j.get("created_at", 0) < cutoff]
            for jid in expired:
                _jobs.pop(jid, None)
        for p in DOWNLOAD_DIR.iterdir():
            try:
                if p.is_file() and p.stat().st_mtime < cutoff:
                    p.unlink()
            except OSError:
                pass  # archivo bloqueado por otra descarga; se limpia en el siguiente ciclo


threading.Thread(target=_janitor, daemon=True).start()


@app.post("/api/download")
def start_download(req: DownloadRequest) -> dict:
    url = req.url.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        raise HTTPException(status_code=400, detail="URL inválida: debe empezar por http:// o https://")
    job_id = uuid.uuid4().hex[:12]
    with _lock:
        _jobs[job_id] = {"status": "queued", "progress": 0.0, "created_at": time.time()}
    threading.Thread(target=_worker, args=(job_id, url), daemon=True).start()
    return {"job_id": job_id}


@app.get("/api/progress/{job_id}")
def get_progress(job_id: str) -> dict:
    job = _jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job no encontrado o expirado")
    return {
        "status": job.get("status"),
        "progress": job.get("progress"),
        "speed": job.get("speed"),
        "eta": job.get("eta"),
        "title": job.get("title"),
        "filesize": job.get("filesize"),
        "error": job.get("error"),
        "file_ready": job.get("status") == "done",
    }


@app.get("/api/file/{job_id}")
def get_file(job_id: str) -> FileResponse:
    job = _jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job no encontrado o expirado")
    if job.get("status") != "done":
        raise HTTPException(status_code=409, detail="El archivo aún no está listo")
    fp = job.get("filepath")
    if not fp or not Path(fp).is_file():
        raise HTTPException(status_code=410, detail="El archivo expiró; vuelve a solicitar la descarga")
    return FileResponse(
        fp,
        filename=job.get("filename") or "video.mp4",
        media_type="application/octet-stream",
    )


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=7860)
