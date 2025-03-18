document.addEventListener("DOMContentLoaded", function () {
  let searchForm = document.querySelector(".navbar-middle form");
  let searchInput = document.querySelector(".search-bar");
  let searchButton = document.querySelector(".search-button");
  let suggestionsContainer = document.querySelector(".main-content");
  const audioPlayer = document.getElementById("audio-player");
  const playPauseBtn = document.querySelector(
    ".control-button[aria-label='Play']"
  );
  const nextBtn = document.querySelector(".control-button[aria-label='Next']");
  const prevBtn = document.querySelector(
    ".control-button[aria-label='Previous']"
  );
  const progressBar = document.querySelector(".progress-bar .progress");

  let playlistQueue = [];
  let currentSongIndex = 0;

  function performSearch() {
    let query = searchInput.value.trim();
    if (!query) return;

    fetch(`/suggestions/?q=${query}`, {
      headers: { "X-Requested-With": "XMLHttpRequest" },
    })
      .then((response) => response.json())
      .then((data) => {
        suggestionsContainer.innerHTML = "";

        if (data.search_result && data.search_result.name) {
          let searchResultBox = `
              <div class="song-box" data-audio-url="${data.search_result.audio_url}">
                  <div class="song-image">
                      <img src="${data.search_result.image_url}" alt="${data.search_result.name}" />
                  </div>
                  <div class="song-name">${data.search_result.name}</div>
                  <div class="song-artist">${data.search_result.artist}</div>
              </div>`;
          suggestionsContainer.innerHTML += searchResultBox;
        }

        if (data.suggestions && data.suggestions.length > 0) {
          data.suggestions.forEach((song) => {
            let songBox = `
                <div class="song-box" data-audio-url="${song.audio_url}">
                    <div class="song-image">
                        <img src="${song.image_url}" alt="${song.name}" />
                    </div>
                    <div class="song-name">${song.name}</div>
                    <div class="song-artist">${song.artist}</div>
                </div>`;
            suggestionsContainer.innerHTML += songBox;
          });
        }

        if (
          !data.search_result &&
          (!data.suggestions || data.suggestions.length === 0)
        ) {
          suggestionsContainer.innerHTML = "<p>No suggestions available.</p>";
        }
      })
      .catch((error) =>
        console.error("❌ Error fetching search results:", error)
      );
  }

  searchForm.addEventListener("submit", function (event) {
    event.preventDefault();
    performSearch();
  });

  searchButton.addEventListener("click", function (event) {
    event.preventDefault();
    performSearch();
  });

  function loadPlaylists() {
    fetch("/get_user_playlists/")
      .then((response) => response.json())
      .then((data) => {
        const playlistContent = document.querySelector(".playlist-content");
        playlistContent.innerHTML = ""; // Clear old playlists

        data.playlists.forEach((playlist) => {
          const playlistItem = document.createElement("div");
          playlistItem.classList.add("playlist-item");
          playlistItem.innerHTML = `
                    <img src="${playlist.image_url}" alt="${playlist.name}" class="playlist-image"/>
                    <span>${playlist.name}</span>
                `;
          playlistItem.addEventListener("click", function (event) {
            event.preventDefault(); // ⛔ Prevent default link action
            event.stopPropagation(); // ⛔ Stop event bubbling

            console.log(
              `📂 Clicked Playlist: ${playlist.name} (ID: ${playlist.id})`
            );

            // ✅ Ensure no redirection happens
            if (window.location.pathname !== "/") {
              window.history.pushState(null, "", "/"); // Adjust URL without reloading
            }

            // ✅ Load playlist songs without redirecting
            loadPlaylistSongs(playlist.id);

            return false; // ⛔ Explicitly prevent navigation
          });

          playlistContent.appendChild(playlistItem);
        });
      })
      .catch((error) => console.error("❌ Error fetching playlists:", error));
  }

  loadPlaylists();

  function loadPlaylistSongs(playlistId) {
    fetch(`/get_playlist_songs/${playlistId}/`)
      .then((response) => response.json())
      .then((data) => {
        suggestionsContainer.innerHTML = ""; // Clear previous suggestions

        if (!data.songs || data.songs.length === 0) {
          suggestionsContainer.innerHTML =
            "<p>No songs found in this playlist.</p>";
          return;
        }

        playlistQueue = data.songs; // Store songs for playback
        currentSongIndex = 0; // Reset index

        data.songs.forEach((song, index) => {
          if (!song.audio_url) return; // Skip if no audio

          let songBox = `
                    <div class="song-box" data-audio-url="${song.audio_url}" data-index="${index}">
                        <div class="song-image">
                            <img src="${song.image_url}" alt="${song.name}" />
                        </div>
                        <div class="song-name">${song.name}</div>
                        <div class="song-artist">${song.artist}</div>
                    </div>`;
          suggestionsContainer.innerHTML += songBox;
        });

        // ✅ Add event listeners to play a song when clicked
        document.querySelectorAll(".song-box").forEach((box) => {
          box.addEventListener("click", function () {
            currentSongIndex = parseInt(box.dataset.index);
            playSong(playlistQueue[currentSongIndex]);
          });
        });

        playSong(playlistQueue[0]); // Auto-play first song
      })
      .catch((error) => console.error("❌ Error fetching songs:", error));
  }

  function playYouTubeAudio(youtubeUrl) {
    fetch(`/player/get_audio_url/?url=${encodeURIComponent(youtubeUrl)}`)
      .then((response) => response.json())
      .then((data) => {
        if (data.audio_url) {
          audioPlayer.src = data.audio_url; // Set the audio player source
          audioPlayer.play();
        } else {
          console.error("❌ Error fetching audio URL:", data.error);
        }
      })
      .catch((error) => console.error("❌ Error:", error));
  }

  function playSong(song) {
    console.log("🎵 Now Playing:", song);

    let audioPlayer = document.getElementById("audio-player");
    let currentTrackName = document.getElementById("current-track-name");
    let currentTrackImage = document.getElementById("current-track-image");

    if (!song.audio_url) {
      console.error("No audio URL available for this song.");
      return;
    }

    audioPlayer.src = song.audio_url;
    audioPlayer.play();

    currentTrackName.textContent = song.name;
    currentTrackImage.src = song.image_url;
  }

  // **✅ Play/Pause Button**
  playPauseBtn.addEventListener("click", function () {
    if (audioPlayer.paused) {
      audioPlayer.play();
      playPauseBtn.innerHTML = `<i class="fas fa-pause"></i>`;
    } else {
      audioPlayer.pause();
      playPauseBtn.innerHTML = `<i class="fas fa-play"></i>`;
    }
  });

  // **✅ Next Song**
  nextBtn.addEventListener("click", function () {
    if (currentSongIndex < playlistQueue.length - 1) {
      playSong(currentSongIndex + 1); // Go to the next song
    } else {
      playSong(0); // Loop back to the first song
    }
  });

  // **✅ Previous Song**
  prevBtn.addEventListener("click", function () {
    if (currentSongIndex > 0) {
      playSong(currentSongIndex - 1);
    }
  });

  // **✅ Update Progress Bar**
  audioPlayer.addEventListener("timeupdate", function () {
    const progress = (audioPlayer.currentTime / audioPlayer.duration) * 100;
    progressBar.style.width = progress + "%";
  });

  // **✅ Autoplay Next Song**
  audioPlayer.addEventListener("ended", function () {
    if (currentSongIndex < playlistQueue.length - 1) {
      playSong(currentSongIndex + 1); // Play next song
    } else {
      playSong(0); // Restart from the first song when the playlist ends
    }
  });

  // **✅ Remove duplicate <audio> elements inside "current-track"**
  document.querySelectorAll(".current-track audio").forEach((el, i) => {
    if (i > 0) el.remove();
  });
});
