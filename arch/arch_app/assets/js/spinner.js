import $ from 'jquery';
// remove the spinner when the page is loaded

$(window).on('load', function () {
    var spinner = $('.spinner-border'); // Use jQuery to select the spinner element
    spinner.addClass('d-none'); // Hide the spinner
});

function isFormEmpty(form) {
    // Loop through the form elements
    for (var i = 0; i < form.elements.length; i++) {
        var element = form.elements[i];

        // Check if the element is a file input
        if (element.type === 'file') {
            // Check if the user selected at least one file
            if (element.files.length > 0) {
                return false; // At least one file is selected
            }
        }
    }
    return true; // Form is empty
}

export function showSpinner(formId) {
    var spinner = $('.spinner-border');

    var form = document.getElementById(formId); // Get the form element

    // check if the form is empty
    if (isFormEmpty(form)) {
        spinner.addClass('d-none'); // Hide the spinner
           // submit the form
        form.submit();
        return;
    }
    spinner.removeClass('d-none'); // Show the spinner
}

