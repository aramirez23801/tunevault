// TuneVault — Authentication

// Toggle between login and register tabs
function showAuthTab(tab) {
  const loginForm = document.getElementById('login-form')
  const registerForm = document.getElementById('register-form')
  const tabs = document.querySelectorAll('.auth-tab')

  tabs.forEach((t) => t.classList.remove('active'))

  if (tab === 'login') {
    loginForm.style.display = 'flex'
    registerForm.style.display = 'none'
    tabs[0].classList.add('active')
  } else {
    loginForm.style.display = 'none'
    registerForm.style.display = 'flex'
    tabs[1].classList.add('active')
  }
}

// Handle login form submission
async function handleLogin() {
  const email = document.getElementById('login-email').value
  const password = document.getElementById('login-password').value
  const errorEl = document.getElementById('login-error')
  errorEl.textContent = ''

  if (!email || !password) {
    errorEl.textContent = 'Please fill in all fields'
    return
  }

  try {
    const response = await fetch(API_BASE + '/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    })

    const data = await response.json()

    if (!response.ok) {
      errorEl.textContent = data.detail || 'Login failed'
      return
    }

    // Store credentials and redirect to dashboard
    sessionStorage.setItem('api_key', data.api_key)
    sessionStorage.setItem('username', data.username)
    window.location.href = 'dashboard.html'
  } catch (error) {
    errorEl.textContent = 'Could not connect to server'
  }
}

// Handle register form submission
async function handleRegister() {
  const username = document.getElementById('register-username').value
  const email = document.getElementById('register-email').value
  const password = document.getElementById('register-password').value
  const errorEl = document.getElementById('register-error')
  errorEl.textContent = ''

  if (!username || !email || !password) {
    errorEl.textContent = 'Please fill in all fields'
    return
  }

  try {
    const response = await fetch(API_BASE + '/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, email, password })
    })

    const data = await response.json()

    if (!response.ok) {
      errorEl.textContent = data.detail || 'Registration failed'
      return
    }

    // Store credentials and redirect to dashboard
    sessionStorage.setItem('api_key', data.api_key)
    sessionStorage.setItem('username', username)
    window.location.href = 'dashboard.html'
  } catch (error) {
    errorEl.textContent = 'Could not connect to server'
  }
}

// Handle logout
function handleLogout() {
  sessionStorage.clear()
  window.location.href = 'index.html'
}

// Allow pressing Enter to submit forms
function handleAuthKeypress(event, action) {
  if (event.key === 'Enter') {
    if (action === 'login') handleLogin()
    if (action === 'register') handleRegister()
  }
}
