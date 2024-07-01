// // preserve button state (buttons on the sidebar) on page reload (using local storage)
// // Read and set initial state for each button on page load
// window.onload = function () {
//     var buttons = document.querySelectorAll('.keep-state-button');
//     buttons.forEach(function (button) {
//         var buttonId = button.getAttribute("id");
//         var buttonState = localStorage.getItem("button-state-" + buttonId);
//         if (buttonState === "open") {
//             button.setAttribute("aria-expanded", "true");
//             var target = button.dataset.bsTarget;
//             var toggle = new bootstrap.Collapse(document.querySelector(target), {
//                 toggle: false
//             });
//             toggle.show();
//         } else if (buttonState === "closed") {
//             button.setAttribute("aria-expanded", "false");
//             var target = button.dataset.bsTarget;
//             var toggle = new bootstrap.Collapse(document.querySelector(target), {
//                 toggle: false
//             });
//             toggle.hide();
//         } else {
//             // If no state is stored in localStorage, use the default state specified in the data-button-state attribute
//             var defaultButtonState = button.dataset.buttonState;
//             if (defaultButtonState === "open") {
//                 button.setAttribute("aria-expanded", "true");
//             } else if (defaultButtonState === "closed") {
//                 button.setAttribute("aria-expanded", "false");
//             }
//         }
//     });
// }
//
//
// // Function to toggle and store button state
// function toggleButtonState(buttonID) {
//     var button = document.getElementById(buttonID);
//     var currentState = button.getAttribute("aria-expanded");
//     // if the button is open, close it and store the state
//     if (currentState === "true") {
//
//         localStorage.setItem("button-state-" + buttonID, "open");
//         // if the button is closed, open it and store the state
//     } else {
//
//         localStorage.setItem("button-state-" + buttonID, "closed");
//     }
// }
import $ from 'jquery';

export function initSidebar() {
    $(document).ready(function () {
        toggleSidebarState();
        toggleTabState();
    });
}

// function to preserve sidebar state (on page reload) using local storage
// export function toggleSidebarState() {
function toggleSidebarState() {

    $("#button-sidebar-open").on("click", function () {
        localStorage.setItem("sidebar-id", "true");
    });
    $("#button-sidebar-close").on("click", function () {
        localStorage.setItem("sidebar-id", "false");
    });
    var sidebarState = localStorage.getItem("sidebar-id");
    if (sidebarState === "true") {
        // add class show
        $("#sidebar-id").addClass('show')
        $("#sidebar-collapsed-id").removeClass("show");
    } else if (sidebarState === "false") {
        $("#sidebar-id").removeClass("show");
        $("#sidebar-collapsed-id").addClass("show");
    }
};

// Function to toggle and preserve tabs state (on the sidebar)
function toggleTabState() {

    $(".nav-tabs .nav-link").on("click", function () {
        localStorage.setItem("activeTab", $(this).attr("href"));
    });
    var activeTab = localStorage.getItem("activeTab");
    if (activeTab) {
        // set the active tab
        $(".nav-tabs .nav-link").removeClass("active");
        $(".nav-tabs .nav-link[href='" + activeTab + "']").addClass("active");
        $(".tab-pane").removeClass("active");
        $(activeTab).addClass('active');
    }
};
