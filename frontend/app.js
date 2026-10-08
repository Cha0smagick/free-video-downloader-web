/* Video Downloader — lógica: POST /api/download → poll /api/progress → GET /api/file */
(function () {
  "use strict";

  var BACKEND_KEY = "ytdlp_backend_url";
  var DEFAULT_BACKEND = "https://free-video-downloader-web.onrender.com";
  var POLL_MS = 1500;

  var form = document.getElementById("download-form");
  var urlInput = document.getElementById("url");
  var btnDownload = document.getElementById("btn-download");
  var statusEl = document.getElementById("status");
  var progressWrap = document.getElementById("progress-wrap");
  var progressTitle = document.getElementById("progress-title");
  var progressPct = document.getElementById("progress-pct");
  var progressBar = document.getElementById("progress-bar");
  var progressInfo = document.getElementById("progress-info");
  var resultEl = document.getElementById("result");
  var downloadLink = document.getElementById("download-link");
  var resultInfo = document.getElementById("result-info");
  var errorEl = document.getElementById("error");
  var backendInput = document.getElementById("backend-url");
  var btnSaveBackend = document.getElementById("btn-save-backend");

  var pollTimer = null;

  function getBackend() {
    var v = localStorage.getItem(BACKEND_KEY);
    if (v) {
      v = v.replace(/\/+$/, "");
      // Migración: valores localhost guardados antes del default Render se descartan (cero configuración)
      if (/localhost|127\.0\.0\.1/.test(v)) {
        localStorage.removeItem(BACKEND_KEY);
        v = "";
      }
    }
    return v || DEFAULT_BACKEND;
  }

  function showError(msg) {
    errorEl.textContent = msg;
    errorEl.classList.remove("hidden");
  }

  function hideAll() {
    statusEl.classList.add("hidden");
    progressWrap.classList.add("hidden");
    resultEl.classList.add("hidden");
    errorEl.classList.add("hidden");
  }

  function fmtSpeed(bytesPerSec) {
    if (!bytesPerSec) return "";
    var mb = bytesPerSec / (1024 * 1024);
    return mb >= 1 ? mb.toFixed(1) + " MB/s" : (bytesPerSec / 1024).toFixed(0) + " KB/s";
  }

  function fmtEta(seconds) {
    if (!seconds || seconds <= 0) return "";
    var m = Math.floor(seconds / 60);
    var s = Math.round(seconds % 60);
    return " · falta " + (m > 0 ? m + " min " + s + " s" : s + " s");
  }

  function fmtSize(bytes) {
    if (!bytes) return "";
    var mb = bytes / (1024 * 1024);
    return mb >= 1 ? " · " + mb.toFixed(1) + " MB" : " · " + (bytes / 1024).toFixed(0) + " KB";
  }

  function warnProtocol() {
    if (location.protocol === "https:" && getBackend().indexOf("http://") === 0) {
      showError("La página está en HTTPS pero el backend en HTTP: el navegador bloqueará las peticiones. Configura un backend con HTTPS (p. ej. Render, que da HTTPS automático).");
    }
  }

  function api(path, options) {
    return fetch(getBackend() + path, options);
  }

  function poll(jobId) {
    pollTimer = setInterval(function () {
      api("/api/progress/" + jobId)
        .then(function (r) { return r.json(); })
        .then(function (j) {
          if (j.title) progressTitle.textContent = j.title;
          progressPct.textContent = Math.round(j.progress || 0) + "%";
          progressBar.style.width = (j.progress || 0) + "%";
          progressInfo.textContent =
            fmtSpeed(j.speed) + fmtEta(j.eta) + fmtSize(j.filesize);

          if (j.status === "done" && j.file_ready) {
            clearInterval(pollTimer);
            progressPct.textContent = "100%";
            progressBar.style.width = "100%";
            progressInfo.textContent = "Descarga completada";
            downloadLink.href = getBackend() + "/api/file/" + jobId;
            if (j.title) downloadLink.setAttribute("download", j.title + ".mp4");
            resultInfo.textContent = fmtSize(j.filesize);
            resultEl.classList.remove("hidden");
            btnDownload.disabled = false;
          } else if (j.status === "error") {
            clearInterval(pollTimer);
            showError("Error en la descarga: " + (j.error || "desconocido"));
            btnDownload.disabled = false;
          }
        })
        .catch(function () { /* red intermitente: reintenta en el próximo tick */ });
    }, POLL_MS);
  }

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    var url = urlInput.value.trim();
    if (!/^https?:\/\//i.test(url)) {
      showError("La URL debe empezar por http:// o https://");
      return;
    }
    warnProtocol();
    hideAll();
    statusEl.textContent = "Enviando al backend…";
    statusEl.classList.remove("hidden");
    btnDownload.disabled = true;

    api("/api/download", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: url })
    })
      .then(function (r) {
        if (!r.ok) return r.json().then(function (j) { throw new Error(j.detail || ("HTTP " + r.status)); });
        return r.json();
      })
      .then(function (j) {
        if (!j.job_id) throw new Error("Respuesta inválida del backend");
        statusEl.classList.add("hidden");
        progressTitle.textContent = "Preparando…";
        progressPct.textContent = "0%";
        progressBar.style.width = "0%";
        progressInfo.textContent = "";
        progressWrap.classList.remove("hidden");
        poll(j.job_id);
      })
      .catch(function (err) {
        showError("No se pudo iniciar: " + err.message + ". ¿Está el backend encendido? (⚙ Configuración)");
        btnDownload.disabled = false;
      });
  });

  btnSaveBackend.addEventListener("click", function () {
    var v = backendInput.value.trim().replace(/\/+$/, "");
    if (v && !/^https?:\/\//i.test(v)) {
      showError("La URL del backend debe empezar por http:// o https://");
      return;
    }
    if (v) {
      localStorage.setItem(BACKEND_KEY, v);
    } else {
      localStorage.removeItem(BACKEND_KEY);
    }
    errorEl.classList.add("hidden");
    warnProtocol();
    statusEl.textContent = "Backend guardado: " + getBackend();
    statusEl.classList.remove("hidden");
  });

  // Estado inicial: mostrar el backend configurado en el input
  backendInput.value = getBackend();
})();
