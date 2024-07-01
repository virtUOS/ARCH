/**
 * Add query parameters to a link
 * @param id
 */
export function addQueryParamsToLink(id) {
    var currentUrl = window.location.href;

    // Check if the URL contains query parameters
    if (currentUrl.includes('?')) {
        // Get the query string from the URL
        var queryString = currentUrl.split('?')[1];
        // delete the old page number
        if (id.includes('paginate')){
            // Split the query string into individual parameters
            const params = queryString.split('&');
            // Filter out the old 'page=' parameter
            const filteredParams = params.filter(param => !param.startsWith('page='));
            // Reconstruct the updated query string
            queryString = filteredParams.join('&');
        }

        var button = document.getElementById(id);
        // Get the current link attached to the button
        var buttonLink = button.getAttribute('href');
        // Check if the button link already has a query string
        if (buttonLink.includes('?')) {
            // Append the query string to the existing query string in the button link
            buttonLink += '&' + queryString;
        } else {
            // Append the query string to the button link
            buttonLink += '?' + queryString;
        }
        // Update the link attached to the button
        button.setAttribute('href', buttonLink);
    }
}


/**
 * Get the value of the album_mode query parameter
 * @param as_string
 * @returns {boolean|string}
 */
export function get_album_mode(as_string=false) {
    var url = new URL(window.location.href);
    var album_mode = url.searchParams.get("album_mode");
    if (as_string){
        return album_mode
    }
    else {
        album_mode = album_mode === null ? "False" : album_mode;
        return album_mode === "True";
    }
}
