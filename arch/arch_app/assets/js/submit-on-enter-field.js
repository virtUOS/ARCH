import $ from 'jquery';

// attaches event listener to all input fields with the class submit-on-enter.
// when the enter key is pressed (and shift is not pressed), the form is submitted.
$(document).ready(function () {
    $('.submit-on-enter').on('keyup', function (e) {
        let keyCode = e.keyCode || e.which;
        if (keyCode === 13 && !e.shiftKey) {
            e.preventDefault();
            $(this).closest('form').submit();
        }
    });
});
