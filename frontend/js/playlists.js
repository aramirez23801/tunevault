// ============================================================
// TuneVault — Playlists
// ============================================================

// Track currently being added to a playlist
let pendingTrackId = null
let pendingTrackName = ''

// Currently viewed playlist ID
let currentPlaylistId = null

// ============================================================
// Load Playlists Page
// ============================================================

async function loadPlaylists() {
  const container = document.getElementById('playlists-grid')
  container.innerHTML = '<div class="loading">Loading playlists...</div>'

  const response = await apiRequest('/playlists')
  if (!response) return
  const data = await response.json()

  container.innerHTML = ''

  if (data.playlists.length === 0) {
    container.innerHTML =
      '<div class="empty-state">' +
      '<div class="empty-state-text">No playlists yet</div>' +
      '<div class="empty-state-sub">Create your first playlist to get started</div>' +
      '</div>'
    return
  }

  data.playlists.forEach((playlist) => {
    const card = document.createElement('div')
    card.className = 'playlist-card'
    card.onclick = () => openPlaylistDetail(playlist.playlist_id)

    const coverContent = playlist.cover_image_url
      ? '<img src="' + playlist.cover_image_url + '" alt="Cover" />'
      : '<span>&#9835;</span>'

    card.innerHTML =
      '<div class="playlist-card-cover">' +
      coverContent +
      '</div>' +
      '<div class="playlist-card-info">' +
      '<div class="playlist-card-name">' +
      playlist.name +
      '</div>' +
      '<div class="playlist-card-count">' +
      playlist.track_count +
      ' tracks</div>' +
      '</div>'

    container.appendChild(card)
  })
}

// ============================================================
// Playlist Detail
// ============================================================

async function openPlaylistDetail(playlistId) {
  currentPlaylistId = playlistId

  // Switch to playlist detail page
  const pages = document.querySelectorAll('.page')
  pages.forEach((p) => p.classList.remove('active'))
  document.getElementById('page-playlist-detail').classList.add('active')

  // Update sidebar — remove active from all, keep My Playlists highlighted
  const items = document.querySelectorAll('.sidebar-item[data-page]')
  items.forEach((item) => {
    item.classList.remove('active')
    if (item.dataset.page === 'playlists') item.classList.add('active')
  })

  // Load playlist data
  const response = await apiRequest('/playlists/' + playlistId + '/tracks')
  if (!response) return
  const data = await response.json()

  // Update header
  document.getElementById('playlist-detail-name').textContent = data.name
  document.getElementById('playlist-detail-count').textContent =
    data.track_count + ' tracks'

  // Update cover
  const coverEl = document.getElementById('playlist-cover')
  if (data.cover_image_url) {
    coverEl.style.backgroundImage = 'url(' + data.cover_image_url + ')'
    coverEl.style.backgroundSize = 'cover'
    coverEl.style.backgroundPosition = 'center'
    coverEl.innerHTML = ''
  } else {
    coverEl.style.backgroundImage = 'none'
    coverEl.innerHTML =
      '<span style="font-size: 48px; color: var(--text-muted);">&#9835;</span>'
    coverEl.style.display = 'flex'
    coverEl.style.alignItems = 'center'
    coverEl.style.justifyContent = 'center'
  }

  // Set up delete button
  document.getElementById('delete-playlist-btn').onclick = () =>
    deletePlaylist(playlistId)

  // Render tracks
  const container = document.getElementById('playlist-tracks')
  container.innerHTML = ''

  if (data.tracks.length === 0) {
    container.innerHTML =
      '<div class="empty-state">' +
      '<div class="empty-state-text">This playlist is empty</div>' +
      '<div class="empty-state-sub">Go to Explore to add tracks</div>' +
      '</div>'
    return
  }

  data.tracks.forEach((track, index) => {
    const item = document.createElement('div')
    item.className = 'track-item'
    item.innerHTML =
      '<span class="track-number">' +
      (index + 1) +
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
      '<button class="track-remove-btn" onclick="removeTrackFromPlaylist(' +
      playlistId +
      ', ' +
      track.track_id +
      ')">&#10005;</button>'
    container.appendChild(item)
  })
}

// ============================================================
// Delete Playlist
// ============================================================

async function deletePlaylist(playlistId) {
  if (!confirm('Are you sure you want to delete this playlist?')) return

  const response = await apiRequest('/playlists/' + playlistId, {
    method: 'DELETE'
  })

  if (!response) return

  if (response.ok) {
    showToast('Playlist deleted')
    navigateTo('playlists')
  } else {
    showToast('Failed to delete playlist', 'error')
  }
}

// ============================================================
// Remove Track from Playlist
// ============================================================

async function removeTrackFromPlaylist(playlistId, trackId) {
  const response = await apiRequest(
    '/playlists/' + playlistId + '/tracks/' + trackId,
    {
      method: 'DELETE'
    }
  )

  if (!response) return

  if (response.ok) {
    showToast('Track removed')
    openPlaylistDetail(playlistId)
  } else {
    showToast('Failed to remove track', 'error')
  }
}

// ============================================================
// Add to Playlist Modal (triggered from + button on tracks)
// ============================================================

async function showAddToPlaylistModal(trackId, trackName) {
  pendingTrackId = trackId
  pendingTrackName = trackName

  document.getElementById('adding-track-name').textContent =
    'Adding: "' + trackName + '"'
  document.getElementById('new-playlist-name').value = ''
  document.getElementById('add-to-playlist-modal').style.display = 'flex'

  // Load user's playlists
  const container = document.getElementById('playlist-options')
  container.innerHTML = '<div class="loading">Loading...</div>'

  const response = await apiRequest('/playlists')
  if (!response) return
  const data = await response.json()

  container.innerHTML = ''

  if (data.playlists.length === 0) {
    container.innerHTML =
      '<div class="empty-state-sub">No playlists yet — create one below</div>'
    return
  }

  data.playlists.forEach((playlist) => {
    const option = document.createElement('button')
    option.className = 'playlist-option'
    option.onclick = () =>
      addTrackToExistingPlaylist(playlist.playlist_id, playlist.name)
    option.innerHTML =
      '<span class="playlist-option-icon">&#9835;</span>' +
      '<span>' +
      playlist.name +
      '</span>'
    container.appendChild(option)
  })
}

function closeAddToPlaylistModal() {
  document.getElementById('add-to-playlist-modal').style.display = 'none'
  pendingTrackId = null
  pendingTrackName = ''
}

async function addTrackToExistingPlaylist(playlistId, playlistName) {
  const response = await apiRequest('/playlists/' + playlistId + '/tracks', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ track_id: pendingTrackId })
  })

  if (!response) return

  if (response.ok) {
    showToast('Added to "' + playlistName + '"')
    closeAddToPlaylistModal()
  } else {
    const data = await response.json()
    showToast(data.detail || 'Failed to add track', 'error')
  }
}

async function createPlaylistAndAdd() {
  const name = document.getElementById('new-playlist-name').value.trim()
  if (!name) {
    showToast('Enter a playlist name', 'error')
    return
  }

  // Create the playlist
  const createResponse = await apiRequest('/playlists', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: name })
  })

  if (!createResponse) return
  const createData = await createResponse.json()

  if (!createResponse.ok) {
    showToast('Failed to create playlist', 'error')
    return
  }

  // Add the track to the new playlist
  const addResponse = await apiRequest(
    '/playlists/' + createData.playlist_id + '/tracks',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ track_id: pendingTrackId })
    }
  )

  if (addResponse && addResponse.ok) {
    showToast('Created "' + name + '" and added track')
    closeAddToPlaylistModal()
  } else {
    showToast('Playlist created but failed to add track', 'error')
  }
}

// ============================================================
// Create Playlist Modal (from My Playlists page)
// ============================================================

function showCreatePlaylistModal() {
  document.getElementById('create-playlist-name').value = ''
  document.getElementById('create-playlist-modal').style.display = 'flex'
}

function closeCreatePlaylistModal() {
  document.getElementById('create-playlist-modal').style.display = 'none'
}

async function createPlaylist() {
  const name = document.getElementById('create-playlist-name').value.trim()
  if (!name) {
    showToast('Enter a playlist name', 'error')
    return
  }

  const response = await apiRequest('/playlists', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: name })
  })

  if (!response) return

  if (response.ok) {
    showToast('Playlist "' + name + '" created')
    closeCreatePlaylistModal()
    loadPlaylists()
  } else {
    showToast('Failed to create playlist', 'error')
  }
}

// ============================================================
// Cover Overlay (hover on playlist cover)
// ============================================================

function showCoverOverlay() {
  document.getElementById('cover-overlay').style.display = 'flex'
}

function hideCoverOverlay() {
  document.getElementById('cover-overlay').style.display = 'none'
}

function showGenerateCoverModal() {
  document.getElementById('cover-upload').value = ''
  document.getElementById('cover-preview').innerHTML = ''
  document.getElementById('cover-result').style.display = 'none'
  document.getElementById('generate-cover-modal').style.display = 'flex'
}

function closeGenerateCoverModal() {
  document.getElementById('generate-cover-modal').style.display = 'none'
}

// ============================================================
// AI Cover Generation
// ============================================================

let generatedCoverUrl = null

async function generateCover() {
  const fileInput = document.getElementById('cover-upload')
  if (!fileInput.files || fileInput.files.length === 0) {
    showToast('Please upload a photo first', 'error')
    return
  }

  // Show loading state
  const generateBtn = document.querySelector(
    '#generate-cover-modal .btn-primary'
  )
  const originalText = generateBtn.textContent
  generateBtn.textContent = 'Generating... (15-30s)'
  generateBtn.disabled = true
  document.getElementById('cover-result').style.display = 'none'

  // Build form data with the image
  const formData = new FormData()
  formData.append('image', fileInput.files[0])

  try {
    const apiKey = sessionStorage.getItem('api_key')
    const response = await fetch(
      API_BASE +
        '/playlists/' +
        currentPlaylistId +
        '/generate-cover?api_key=' +
        apiKey,
      {
        method: 'POST',
        body: formData
      }
    )

    const data = await response.json()

    if (!response.ok) {
      showToast(data.detail || 'Generation failed', 'error')
      return
    }

    // Show the generated image
    generatedCoverUrl = data.image_url
    document.getElementById('generated-cover').src = generatedCoverUrl
    document.getElementById('cover-result').style.display = 'block'
    showToast('Cover generated!')
    console.log('DALL-E prompt used:', data.prompt_used) // DELETE LATER!!!
    console.log('Playlist analysis:', data.playlist_analysis) // DELETE LATER!!!
  } catch (error) {
    showToast('Failed to generate cover', 'error')
  } finally {
    generateBtn.textContent = originalText
    generateBtn.disabled = false
  }
}

async function saveCover() {
  if (!generatedCoverUrl) {
    showToast('No cover to save', 'error')
    return
  }

  const response = await apiRequest(
    '/playlists/' +
      currentPlaylistId +
      '/cover?image_url=' +
      encodeURIComponent(generatedCoverUrl),
    { method: 'PUT' }
  )

  if (!response) return

  if (response.ok) {
    showToast('Cover saved!')
    closeGenerateCoverModal()
    openPlaylistDetail(currentPlaylistId)
  } else {
    showToast('Failed to save cover', 'error')
  }
}
// Preview uploaded image in the modal
document.addEventListener('DOMContentLoaded', function () {
  const uploadInput = document.getElementById('cover-upload')
  if (uploadInput) {
    uploadInput.addEventListener('change', function () {
      const preview = document.getElementById('cover-preview')
      if (this.files && this.files[0]) {
        const reader = new FileReader()
        reader.onload = function (e) {
          preview.innerHTML = '<img src="' + e.target.result + '" />'
        }
        reader.readAsDataURL(this.files[0])
      }
    })
  }
})
