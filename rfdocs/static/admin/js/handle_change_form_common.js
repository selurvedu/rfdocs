if (!$) {
    $ = django.jQuery;
}

$(document).ready(function () {
    var ul_objects = $('ul.object-tools'),
        a_tag = ul_objects.find('a').filter(function(index) {
            return $(this).text() === 'History';
        });
    if (a_tag.length) {
        $('.alert-danger').removeClass('hide');
    }

    ul_objects.find('a:contains("Invalidate")');

    var main_form = $('#content-main').find('> form'),
        orig_form_obj = main_form.serializeArray();

    main_form.on('change', function() {
        var new_form_obj = $(this).serializeArray();
        var eq = true;
        $.each(new_form_obj, function(idx, val) {
            eq = orig_form_obj[idx].value === val.value;
            if (!eq) {
                return eq;
            }
        });
        if (eq) {
            ul_objects.removeClass('disabled');
        }
        else {
            ul_objects.addClass('disabled');
        }
    });

    ul_objects.on('click', 'a', function(e) {
        if (ul_objects.hasClass('disabled')) {
            return false;
        }
        ul_objects.addClass('disabled');
        var clicked = $(this),
            others = ul_objects.find('a').filter(function() {
                return $(this) !== clicked;
            });
        $.each(others, function(index, value) {
            $(value).on('click', function(e) {
                e.preventDefault();
            });
        });
    })
});