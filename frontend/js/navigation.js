// TuneVault — Navigation & Page Switching

// Check if user is authenticated, redirect to login if not
function checkAuth() {
  const apiKey = sessionStorage.getItem('api_key')
  if (!apiKey) {
    window.location.href = 'index.html'
  }
}

// Initialize the dashboard on page load
function initDashboard() {
  checkAuth()
  const username = sessionStorage.getItem('username')
  document.getElementById('sidebar-username').textContent = username
  document.getElementById('home-username').textContent = username
}

// Switch between pages (home, explore, playlists, playlist-detail)
function navigateTo(page) {
  // Hide all pages
  const pages = document.querySelectorAll('.page')
  pages.forEach((p) => p.classList.remove('active'))

  // Show the selected page
  const target = document.getElementById('page-' + page)
  if (target) {
    target.classList.add('active')
  }

  // Update sidebar active state
  const items = document.querySelectorAll('.sidebar-item[data-page]')
  items.forEach((item) => {
    item.classList.remove('active')
    if (item.dataset.page === page) {
      item.classList.add('active')
    }
  })

  // Load data for the page
  if (page === 'explore') {
    loadExplorePage()
  } else if (page === 'playlists') {
    loadPlaylists()
  }
}

// Toggle sidebar collapse
function toggleSidebar() {
  document.getElementById('sidebar').classList.toggle('collapsed')
}

// Run on page load
initDashboard()
