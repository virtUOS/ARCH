import $ from 'jquery';
import autocomplete from 'jquery-ui/ui/widgets/autocomplete';
import 'select2';

export function initSearch() {
    $(document).ready(function () {
// search bar dropdown
        $(function () {
            $(".input-group-btn .dropdown-menu li a").click(function () {
                var selText = $(this).html();
                $(this).parents(".input-group-btn").find(".btn-search").html(selText);
            });
        });

// autocomplete user
        $(function () {
            $("#search_depicted_users").autocomplete({
                source: '/autocomplete/' + '?autocomplete=search_depicted_users',
                appendTo: "#autocomplete-container",
            });
        });

// autocomplete location
        $(function () {
            $("#search_location").autocomplete({
                source: '/autocomplete/' + '?autocomplete=search_location',
                appendTo: "#autocomplete-container",
            });
        });

        $(function () {
            $("#search_input").autocomplete({
                source: '/autocomplete/' + '?autocomplete=search_input',
            });
        });
    });
}

// clean filters
export function clean_filter(field) {
    if (field === 'date') {
        // clean date fields (SearchForm) and submit form
        document.getElementById('search_start_date').value = '';
        document.getElementById('search_end_date').value = '';
        document.getElementById('search_form_nav').submit();
    } else if (field === 'location') {
        // clean location field (SearchForm) and submit form
        document.getElementById('search_location').value = '';
        document.getElementById('search_form_nav').submit();
    } else if (field === 'media_type') {
        // clean media_type field (SearchForm) and submit form
        document.getElementById('search_media_type').value = 'All';
        document.getElementById('search_form_nav').submit();
    } else if (field === 'depicted_users') {
        // clean depicted_users field (SearchForm) and submit form
        document.getElementById('search_depicted_users').value = '';
        document.getElementById('search_form_nav').submit();
    }
}