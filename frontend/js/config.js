// TuneVault — API Configuration
const API_BASE =
  window.location.hostname === '127.0.0.1' ||
  window.location.hostname === 'localhost'
    ? 'http://127.0.0.1:8000'
    : 'https://tunevault-production-83a3.up.railway.app'
