import $ from 'jquery';
import {get_album_mode} from "./utils.js";


/**
 * Initialize the record functionality
 */
export function initRecord() {
    $(document).ready(function () {
        new Record();
    });
}

const record_tabs = {
    'DETAILS': 'details',
    'COMMENTS': 'comments'
}

/**
 * Class to handle record functionality
 */
class Record {

    /**
     * Initializes the record class
     */
    constructor() {
        // init record tabs functionality
        this.commentsButton = $('#btn-detail-comments');
        this.detailButton = $('#btn-detail-record');
        this.setActiveTab();
        this.addSwitchTabEventListeners();
        // init delete tags functionality
        this.deleteTagMode = false;
        this.tagContainer = $("#tag-container");
        this.deleteTagButton = $("#remove-user-icon");
        this.profilePics = $('.tag-profile-photo');
        this.deleteTags = $('.delete-tag');
        this.addDeleteTagEventListeners();
    }

    /**
     * Add event listeners to switch between record tabs
     */
    addSwitchTabEventListeners() {
        let record = this;
        record.detailButton.click(function () {
            localStorage.setItem('record-tab', record_tabs['DETAILS']);
            record.highlight_detail_button();
        });
        record.commentsButton.click(function () {
            localStorage.setItem('record-tab', record_tabs['COMMENTS']);
            record.highlight_comment_button();
        });
    }

    /**
     * Add event listeners to allow the user to delete tags
     */
    addDeleteTagEventListeners() {
        // toggle delete tag mode when delete tag button is clicked
        if (this.deleteTagButton) {
            this.deleteTagButton.on("click", () => {
                this.toggleDeleteTagMode();
            });
        }

        // delete tag when delete tag button is clicked
        this.deleteTags.on("click", (event) => {
            let tagId = $(event.target).attr('data-tag-id');
            this.sendDeleteTagRequest(tagId);
        });

        // toggle delete tag mode when clicking outside the container
        document.addEventListener("click", (event) => {
            if (this.deleteTagMode === true && !this.tagContainer.is(event.target)) {
                this.toggleDeleteTagMode();
            }
        });

        // Event listener for clicks inside the container (to prevent toggling mode when clicking inside)
        this.tagContainer.on("click", (event) => {
            event.stopPropagation();
        });
    }

    /**
     * Toggle the delete tag mode
     * and show/hide the delete tags/profile photos respectively
     */
    toggleDeleteTagMode() {
        this.deleteTagMode = this.deleteTagMode === false;
        this.profilePics.css('display', this.deleteTagMode ? 'none' : 'block')
        this.deleteTags.css('display', this.deleteTagMode ? 'block' : 'none');
    }

    /**
     * Send ajax request to delete tag
     * @param tagId
     */
    sendDeleteTagRequest(tagId) {
        $.ajax({
            type: 'POST',
            url: '/tag/' + tagId + '/delete',
            data: {
                'csrfmiddlewaretoken': $('input[name=csrfmiddlewaretoken]').val()
            },
            success: function () {
                location.reload();
            },
            error: function () {
                console.log('Error deleting tag');
            }
        });
    }

    /**
     * Highlight the detail button and show the detail container
     */
    highlight_detail_button() {
        $('#btn-detail-record').removeClass('text-secondary');
        $('#btn-detail-record').addClass('text-primary');
        $('#btn-detail-comments').removeClass('text-primary');
        $('#btn-detail-comments').addClass('text-secondary');
        $('#detail-record-container').removeClass('d-none');
        $('#detail-comments-container').addClass('d-none');
    }

    /**
     * Highlight the comment button and show the comment container
     */
    highlight_comment_button() {
        this.commentsButton.removeClass('text-secondary');
        this.commentsButton.addClass('text-primary');
        this.detailButton.removeClass('text-primary');
        this.detailButton.addClass('text-secondary');
        $('#detail-comments-container').removeClass('d-none');
        $('#detail-record-container').addClass('d-none');
    }

    /**
     * Set the active tab based on the album mode and the record tab stored in local storage
     */
    setActiveTab() {
        let album_mode = get_album_mode();
        let record_tab = localStorage.getItem('record-tab');

        if (record_tab === record_tabs['COMMENTS']) {
            this.highlight_comment_button();
        } else if (record_tab === record_tabs['DETAILS']) {
            this.highlight_detail_button();
        } else {
            if (album_mode === true) {
                this.highlight_detail_button();
            } else {
                this.highlight_comment_button();
            }
        }
    }

}
