import $ from 'jquery';

$(document).ready(function () {

    // Get all albums from the sidebar
    var albums = $('.album');

    // Highlight the album when dragged over
    albums.on('dragenter', function () {
        $(this).addClass('highlight');
    });

    // Remove highlight when no longer dragged over
    albums.on('dragleave', function () {
        $(this).removeClass('highlight');
    });

    albums.on('dragover', function (event) {
        event.preventDefault();
    });

    // Handle the drop event
    albums.on('drop', function (event) {
        event.preventDefault();
        event.stopPropagation();

        // Get the album ID
        var album_id = $(this).data('id');
        // Get the record ID from the dataTransfer object
        var record_id = event.originalEvent.dataTransfer.getData('text/plain');

        // Move the record to the album
        $.ajax(
            {
                url: '/record_update/',
                type: 'POST',
                data: {
                    'album_id': album_id,
                    'record_id': record_id,
                    'csrfmiddlewaretoken': $('input[name=csrfmiddlewaretoken]').val()
                },
                success: function (response) {
                    // reload current page
                    location.reload();
                },
                error: function (xhr, status, error) {
                    console.log('Error: ' + error);
                }
            });
    });

    // Handle the dragstart event for record files
    $('.record-container').on('dragstart', function (event) {
        // Set the dataTransfer object with the record ID
        event.originalEvent.dataTransfer.setData('text/plain', event.target.dataset.record_id);
    });
});
