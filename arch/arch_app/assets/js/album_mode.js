import $ from 'jquery';

/**
 * Add the album_mode query parameter to the URL
 * If album_mode is False redirect to SearchView otherwise redirect to AlbumView
 */
$(document).ready(function () {
    // Define the query string parameters you want to include
    var mode = document.getElementById('album_mode_parameter')
    if (mode) {
        var queryParameter = mode.getAttribute('data-mode')
        // Update the URL in the browser's address bar
        window.history.replaceState({}, document.title, '?' + 'album_mode=' + queryParameter + window.location.hash);
    }
});
