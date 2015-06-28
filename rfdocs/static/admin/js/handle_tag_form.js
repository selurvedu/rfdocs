if (!$) {
    $ = django.jQuery;
}

$(document).ready(function () {
    "use strict";
    var source_opts = $('#id_source_select'),
        local_file_input = $('#id_source_local_file'),
        local_file_label = $("label[for='id_source_local_file']"),
        external_url_input = $('#id_source_external_url'),
        external_url_label = $("label[for='id_source_external_url']"),
        handle_url_opt = function () {
            external_url_input.attr('placeholder', 'http://robotframework.googlecode.com/hg/doc/libraries/ExampleLibrary.html');
            external_url_input.prop('disabled', false);
            local_file_input.prop('disabled', true);
            external_url_label.addClass('required');
            local_file_label.removeClass('required');
        },
        handle_file_opt = function() {
            local_file_input.prop('disabled', false);
            external_url_input.prop('disabled', true);
            external_url_label.removeClass('required');
            local_file_label.addClass('required');
        },
        selected_val = source_opts.find(':selected').val(),
        handle_opts = function() {
            if (selected_val === 'source_url') {
                handle_url_opt();
            }
            else if (selected_val === 'local_file') {
                handle_file_opt();
            }
        };
    handle_opts();
    source_opts.on("change", function() {
        selected_val = source_opts.find(':selected').val();
        handle_opts();
    });
});
