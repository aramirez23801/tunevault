// TuneVault — Explore Page

// Load the explore page content (genres + artists)
async function loadExplorePage() {
  loadGenres()
  loadArtists()
}

// ============================================================
// Genres
// ============================================================

async function loadGenres() {
  const container = document.getElementById('genre-cards')
  container.innerHTML = '<div class="loading">Loading genres...</div>'

  const response = await apiRequest('/genres')
  if (!response) return
  const data = await response.json()

  container.innerHTML = ''
  data.genres.forEach((genre) => {
    const card = document.createElement('div')
    card.className = 'card'
    card.onclick = () => openGenreDetail(genre.genre_id, genre.name)
    card.innerHTML =
      '<div class="card-cover">&#9835;</div>' +
      '<div class="card-title">' +
      genre.name +
      '</div>' +
      '<div class="card-subtitle">' +
      genre.track_count +
      ' tracks</div>'
    container.appendChild(card)
  })
}

async function openGenreDetail(genreId, genreName) {
  // Hide browse sections, show genre detail
  document.getElementById('genre-section').style.display = 'none'
  document.getElementById('artist-section').style.display = 'none'
  document.getElementById('search-results').style.display = 'none'
  document.getElementById('artist-detail').style.display = 'none'
  document.getElementById('genre-detail').style.display = 'block'

  document.getElementById('genre-detail-name').textContent = genreName

  const container = document.getElementById('genre-artists')
  container.innerHTML = '<div class="loading">Loading artists...</div>'

  // Search tracks by genre, then extract unique artists
  const response = await apiRequest(
    '/tracks/search?genre=' + encodeURIComponent(genreName) + '&limit=500'
  )
  if (!response) return
  const data = await response.json()

  // Get unique artists from the results
  const artistMap = {}
  data.tracks.forEach((track) => {
    if (!artistMap[track.artist]) {
      artistMap[track.artist] = { name: track.artist, count: 0 }
    }
    artistMap[track.artist].count++
  })

  const artists = Object.values(artistMap).sort((a, b) => b.count - a.count)

  container.innerHTML = ''
  artists.forEach((artist) => {
    const card = document.createElement('div')
    card.className = 'card'
    card.onclick = () => openArtistDetail(artist.name)
    card.innerHTML =
      '<div class="card-cover">&#9834;</div>' +
      '<div class="card-title">' +
      artist.name +
      '</div>' +
      '<div class="card-subtitle">' +
      artist.count +
      ' tracks</div>'
    container.appendChild(card)
  })

  if (artists.length === 0) {
    container.innerHTML =
      '<div class="empty-state"><div class="empty-state-text">No artists found</div></div>'
  }
}

function closeGenreDetail() {
  document.getElementById('genre-detail').style.display = 'none'
  document.getElementById('genre-section').style.display = 'block'
  document.getElementById('artist-section').style.display = 'block'
}

// ============================================================
// Artists
// ============================================================

async function loadArtists() {
  const container = document.getElementById('artist-cards')
  container.innerHTML = '<div class="loading">Loading artists...</div>'

  const response = await apiRequest('/artists?limit=50')
  if (!response) return
  const data = await response.json()

  container.innerHTML = ''
  data.artists.forEach((artist) => {
    const card = document.createElement('div')
    card.className = 'card'
    card.onclick = () => openArtistDetail(artist.name)
    card.innerHTML =
      '<div class="card-cover">&#9834;</div>' +
      '<div class="card-title">' +
      artist.name +
      '</div>' +
      '<div class="card-subtitle">' +
      artist.album_count +
      ' albums</div>'
    container.appendChild(card)
  })
}

async function openArtistDetail(artistName) {
  // Hide browse sections, show artist detail
  document.getElementById('genre-section').style.display = 'none'
  document.getElementById('artist-section').style.display = 'none'
  document.getElementById('search-results').style.display = 'none'
  document.getElementById('genre-detail').style.display = 'none'
  document.getElementById('artist-detail').style.display = 'block'

  document.getElementById('artist-detail-name').textContent = artistName

  const container = document.getElementById('artist-tracks')
  container.innerHTML = '<div class="loading">Loading tracks...</div>'

  const response = await apiRequest(
    '/tracks/search?artist=' + encodeURIComponent(artistName) + '&limit=100'
  )
  if (!response) return
  const data = await response.json()

  container.innerHTML = ''
  data.tracks.forEach((track, index) => {
    container.appendChild(createTrackItem(track, index + 1))
  })

  if (data.tracks.length === 0) {
    container.innerHTML =
      '<div class="empty-state"><div class="empty-state-text">No tracks found</div></div>'
  }
}

function closeArtistDetail() {
  document.getElementById('artist-detail').style.display = 'none'
  document.getElementById('genre-section').style.display = 'block'
  document.getElementById('artist-section').style.display = 'block'
}

// ============================================================
// Search
// ============================================================

let searchTimeout = null

function handleSearch(event) {
  const query = event.target.value.trim()

  // Debounce: wait 400ms after user stops typing
  clearTimeout(searchTimeout)

  if (query.length === 0) {
    clearSearch()
    return
  }

  searchTimeout = setTimeout(() => {
    performSearch(query)
  }, 400)
}

async function performSearch(query) {
  // Hide browse sections, show search results
  document.getElementById('genre-section').style.display = 'none'
  document.getElementById('artist-section').style.display = 'none'
  document.getElementById('genre-detail').style.display = 'none'
  document.getElementById('artist-detail').style.display = 'none'
  document.getElementById('search-results').style.display = 'block'

  const container = document.getElementById('search-results-list')
  container.innerHTML = '<div class="loading">Searching...</div>'

  const response = await apiRequest(
    '/tracks/search?q=' + encodeURIComponent(query) + '&limit=30'
  )
  if (!response) return
  const data = await response.json()

  container.innerHTML = ''
  data.tracks.forEach((track, index) => {
    container.appendChild(createTrackItem(track, index + 1))
  })

  if (data.tracks.length === 0) {
    container.innerHTML =
      '<div class="empty-state"><div class="empty-state-text">No results for "' +
      query +
      '"</div></div>'
  }
}

function clearSearch() {
  document.getElementById('search-input').value = ''
  document.getElementById('search-results').style.display = 'none'
  document.getElementById('genre-section').style.display = 'block'
  document.getElementById('artist-section').style.display = 'block'
}

// ============================================================
// Track Item (reusable component)
// ============================================================

function createTrackItem(track, number) {
  const item = document.createElement('div')
  item.className = 'track-item'
  item.innerHTML =
    '<span class="track-number">' +
    number +
    '</span>' +
    '<div class="track-info">' +
    '<div class="track-name">' +
    track.name +
    '</div>' +
    '<div class="track-artist">' +
    track.artist +
    '</div>' +
    '</div>' +
    '<div class="track-album">' +
    track.album +
    '</div>' +
    '<div class="track-duration">' +
    formatDuration(track.milliseconds) +
    '</div>' +
    '<button class="track-add-btn" onclick="showAddToPlaylistModal(' +
    track.track_id +
    ", '" +
    track.name.replace(/'/g, "\\'") +
    '\')">+</button>'
  return item
}
