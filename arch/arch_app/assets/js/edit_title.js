import $ from 'jquery';
// handles title editing functionality

//toggle record details and comments
$(document).ready(function () {
        document.querySelectorAll('.editable-title').forEach((element) => {
            element.addEventListener('click', () => {
                element.classList.add('editing');
                element.addEventListener('blur', () => {
                    element.classList.remove('editing');
                });
            });
        });
    }
);
