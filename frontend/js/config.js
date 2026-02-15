// TuneVault — API Configuration
// Uses current hostname to detect environment
const API_BASE =
  window.location.hostname === '127.0.0.1' ||
  window.location.hostname === 'localhost'
    ? 'http://127.0.0.1:8000'
    : 'https://YOUR-BACKEND-URL.railway.app'
