// Import CSS
import 'bootstrap/dist/css/bootstrap.min.css';
import 'bootstrap-icons/font/bootstrap-icons.css';
import 'select2/dist/css/select2.min.css';
import 'jquery-ui/themes/base/all.css';

// Import custom CSS
import '../styles/solar_light.css';
import '../styles/style.css';

// Import JS
import $ from 'jquery';
import 'jquery-ui';
import 'select2'
import 'bootstrap';

// Import custom JS
import {addQueryParamsToLink} from "./utils.js";
import "./album_mode.js";
import {showSpinner} from "./spinner.js";
import {dashboard} from "./dashboard.js";
import "./drag_drop.js";
import {drawTagBox} from "./draw_tag_box.js";
import {initRecord} from "./record.js";
import {initSidebar} from "./preserve_toggle_state.js";
import {initSearch, clean_filter} from "./search_utils";
import "./submit-on-enter-field.js";

export {$, dashboard, showSpinner, addQueryParamsToLink, drawTagBox,
    initRecord, initSearch, clean_filter, initSidebar};

window.arch = {
    $,
    dashboard,
    showSpinner,
    addQueryParamsToLink,
    drawTagBox,
    initRecord,
    initSearch,
    clean_filter,
    initSidebar
};
