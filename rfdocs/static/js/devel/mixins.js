/**
 This file should be added right after jquery*.js files and before any other js files,
 that may use current file.
 */

String.prototype.strip = function (str) {
    "use strict";
    var re = new RegExp(str,"g");
    return this.replace(re, '');
};

String.prototype.rstrip = function (str) {
    "use strict";
    return this.strip(str+"$");
};

String.prototype.lstrip = function (str) {
    "use strict";
    return this.strip("^"+str);
};

// Global functions
// Don't make it as nested func of `hiJax`, allow to use it separately.
function sameOrigin(a_tag) {
    "use strict";
    // check if the target link has the same origin as current resource (same location)
    var loc = window.location;
    return a_tag.prop('hostname') === loc.hostname &&
        a_tag.prop('port') === loc.port &&
        a_tag.prop('protocol') === loc.protocol;
}

function hiJax(locator, target_handler) {
    "use strict";
    // hijax only links with same origin
    $(locator).on('click', 'a', function(e) {
        var $this = $(this);
        if (sameOrigin($this)) {
            // Pass in the Event and the Target objects.
            // Let the handler func to work with them.
            target_handler(e, $this);
        }
    });
}

function addBootstrapTooltipls(tooltips) {
    // See http://getbootstrap.com/2.3.2/javascript.html#tooltips for more details
    if (tooltips.length) {
        $.each(tooltips, function(index, value) {
            var $value = $(value);
            $value.tooltip(
                {
                    animation: $value.attr('data-tooltip-animation') || true,
                    html: $value.attr('data-tooltip-html') || false,
                    placement: $value.attr('data-tooltip-placement') || 'top',
                    selector: $value.attr('data-tooltip-selector') || false,
                    title: $value.attr('data-tooltip-title') || '',
                    trigger: $value.attr('data-tooltip-trigger') || 'hover focus',
                    delay: $value.attr('data-tooltip-delay') || 0,
                    container: $value.attr('data-tooltip-container') || false
                }
            );
        })
    }
}

(function($) {
    'use strict';
    // Source: http://stackoverflow.com/questions/3390930/any-way-to-make-jquery-inarray-case-insensitive
    $.extend({
        // Case insensative inArray
        inArrayIgnoreCase: function(elem, arr, i){
            // not looking for a string anyways, use default method
            if (typeof elem !== 'string'){
                return $.inArray.apply(this, arguments);
            }
            // confirm array is populated
            if (arr){
                var len = arr.length;
                i = i ? (i < 0 ? Math.max(0, len + i) : i) : 0;
                elem = elem.toLowerCase();
                for (; i < len; i++){
                    if (i in arr && arr[i].toLowerCase() === elem){
                        return i;
                    }
                }
            }
            // stick with inArray/indexOf and return -1 on no match
            return -1;
        }
    });
})(jQuery);
