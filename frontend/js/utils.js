// TuneVault — Utility Functions

// Show a toast notification at the bottom-right of the screen
function showToast(message, type = 'success') {
  const toast = document.createElement('div')
  toast.className = 'toast ' + type
  toast.textContent = message
  document.body.appendChild(toast)
  setTimeout(() => toast.remove(), 3000)
}

// Format milliseconds to mm:ss
function formatDuration(ms) {
  const minutes = Math.floor(ms / 60000)
  const seconds = Math.floor((ms % 60000) / 1000)
  return minutes + ':' + (seconds < 10 ? '0' : '') + seconds
}

// Make an authenticated API request
async function apiRequest(endpoint, options = {}) {
  const apiKey = sessionStorage.getItem('api_key')
  const separator = endpoint.includes('?') ? '&' : '?'
  const url =
    API_BASE + endpoint + (apiKey ? separator + 'api_key=' + apiKey : '')

  const response = await fetch(url, options)

  if (response.status === 401) {
    sessionStorage.clear()
    window.location.href = 'index.html'
    return null
  }

  return response
}
