import $ from 'jquery';

export function drawTagBox() {

    $(document).ready(function () {

        // this script is to create a tag box on the image
        var canvas = document.getElementById('imageCanvas');
        var context = canvas.getContext('2d');
        var drawButton = document.getElementById('drawButton');
        var drawing = false;
        var startX, startY, currentX, currentY;
        var id = canvas.dataset.record;
        var image = document.getElementById('gallery-image-' + id);

        // add event listener to the draw button
        drawButton.addEventListener('click', function (event) {
            // canvasStyleFlag = true;  // flag to indicate if the canvas is highlighted,
            // Set canvas size to match the image size
            canvas.width = image.width;
            canvas.height = image.height;
            // highlight the canvas
            canvas.style.border = "1px solid gray";
            canvas.style.cursor = "crosshair";
            canvas.style.boxShadow = "0px 0px 10px 0px rgba(0,0,0,0.75)";

            // when mouse down, start drawing and set the start position
            canvas.addEventListener('mousedown', function (event) {
                drawing = true;
                startX = event.clientX - canvas.getBoundingClientRect().left;
                startY = event.clientY - canvas.getBoundingClientRect().top;
            });

            // when mouse move, draw the rectangle
            canvas.addEventListener('mousemove', function (event) {
                if (!drawing) return;  // if not drawing, do nothing
                // get the current mouse position
                currentX = event.clientX - canvas.getBoundingClientRect().left;
                currentY = event.clientY - canvas.getBoundingClientRect().top;
                // clear the canvas
                context.clearRect(0, 0, canvas.width, canvas.height);
                // draw the rectangle
                context.strokeStyle = 'red';
                context.lineWidth = 1;
                context.strokeRect(startX, startY, currentX - startX, currentY - startY);
            });

            // when mouse up, send the data to the server
            canvas.addEventListener('mouseup', function (event) {
                drawing = false;
                // remove highlights from the canvas
                canvas.style.border = "none";
                canvas.style.cursor = "default";
                canvas.style.boxShadow = "none";

                var data = {
                    'x1': startX < currentX ? startX : currentX,  // minimal value of x
                    'y1': startY < currentY ? startY : currentY,  // minimal value of y
                    'x2': startX < currentX ? currentX : startX,  // maximal value of x
                    'y2': startY < currentY ? currentY : startY,  // maximal value of y
                    'width': canvas.width,  // width of the image
                    'height': canvas.height,  // height of the image
                    'csrfmiddlewaretoken': $('input[name=csrfmiddlewaretoken]').val()
                };

                $.ajax({
                    type: 'POST',
                    url: '/record/' + id + '/create_tag_box',
                    data: data,
                    dataType: 'json',
                    success: function (response) {
                        location.reload();  // reload current page
                    },
                    error: function (xhr, status, error) {
                        console.log('Error: ' + error);
                    }
                });

            });
        });
    });
};
