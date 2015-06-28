// At this time UIAPP should be already defined in scope of module.js!!!
// The line below was added to calm down js(lint)hint.
var UIAPP = UIAPP || {};

UIAPP.namespace('UIAPP.Filter');
UIAPP.Filter = (function (logger, evmanager) {
    "use strict";
    function Filter() {
        // the cached instance
        var instance;

        // rewrite the constructor
        Filter = function Filter() {
            return instance;
        };

        // carry over the prototype properties
        Filter.prototype = this;

        // the instance
        instance = new Filter();

        // reset the constructor pointer
        instance.constructor = Filter;

        // Private vars and methods
        var _isHandledByStatusCode = function(status, codes) {
                return $.inArray(status, $.map(codes, function (n, i) {return parseInt(n);} )) !== -1;
            },
            _show = function(callback) {
                instance.container.show('slide', {direction: 'left'}, 500, callback);
                instance.search_form.fadeIn(500);
            },
            _hide = function(callback) {
                instance.container.hide('slide', {direction: 'left'}, 700, callback);
                instance.search_form.fadeOut(700);
            },

            _setFilterParams = function(params) {
                $.each(params, function(key, value) {
                    if (value === "") {
                        value = instance.config.all;
                    }
                    var atag = $("#id_"+key).find('a').filter(function(index) {
                        return $(this).text() === value;
                    });
                    if (!atag.hasClass(instance.config.aselected)) {
                        atag.click();
                    }
                });
            },
            _getFilterParams = function(item) {
                var url_params = {},
                    aselected = "a."+instance.config.aselected;
                $.each(instance.ul_ids, function(index, value) {
                    url_params[value.lstrip("id_")] = $("#"+value)
                        .find(aselected)
                        .get(0).text.replace(instance.config.all,"");
                });
                var _cloned_url_params = $.extend({}, url_params);
                // exclude current item from associative array
                delete url_params[$(item).closest('ul').attr('id').lstrip("id_")];
                return {
                    url: item.href + "&" + $.param(url_params),
                    params: _cloned_url_params
                };
            },
            _makeActive = function(item) {
                item.addClass(instance.config.aselected);
            },
            _makeSiblingsInActive = function(item) {
                item.closest('ul').find('a').removeClass(instance.config.aselected);
            },
            _filterList = function(list, text) {
                var $list = $(list);
                $list.find("a:not(:Contains(" + text + "))").parent().slideUp();
                var res = $list.find("a:Contains(" + text + ")");
                res.parent().slideDown();
                return res.length;
            },
            _updateSearchBoxClass = function(container, passed) {
                if (passed) {
                    container.addClass('passed');
                    container.removeClass('failed');
                }
                else {
                    container.addClass('failed');
                    container.removeClass('passed');
                }
            },
            _updateIcons = function(ico_search, ico_clear, ico_count, empty) {
                if (empty) {
                    ico_search.removeClass('hidden');
                    ico_clear.addClass('hidden');
                    ico_count.addClass('hidden');
                }
                else {
                    ico_search.addClass('hidden');
                    ico_clear.removeClass('hidden');
                    ico_count.removeClass('hidden');
                }
            };

        // Public vars and methods
        Filter.prototype.config =  {
            search_form: "#search-form",
            filter_form : ".filter-form",
            aselected: "selected",
            all: "All"
        };

        Filter.prototype.init = function(locator, options) {
            instance.container = $(locator || "#filter");
            if (options) {
                instance.config = $.extend({}, instance.config, options);
            }
            instance.data_container = $(UIAPP.LocatorManager.data_container);
            instance.search_form = $(instance.config.search_form);
            instance.filter_form = $(instance.config.filter_form);
            instance.ul_ids = [];
            instance.lists = instance.filter_form.find('ul');
            $.each(instance.lists, function(index, value) {
                instance.ul_ids.push($(value).attr('id'));
            });

            // --- Start event listeners
            instance.filter_form.on("click", "a", function(event) {
                instance.onActivate(this);
                event.preventDefault();
            });
            instance.search_form.submit(function(event) {
                event.preventDefault();
            });
        }; // --- End event listeners

        // Snippet that allows case-insensitive search with `:contains` selector
        // http://css-tricks.com/snippets/jquery/make-jquery-contains-case-insensitive/
        // http://stackoverflow.com/questions/2196641/how-do-i-make-jquery-contains-case-insensitive-including-jquery-1-8
        $.expr[":"].Contains = $.expr.createPseudo(function(arg) {
            return function( elem ) {
                return $(elem).text().toUpperCase().indexOf(arg.toUpperCase()) >= 0;
            };
        });

        // Prototypes
        Filter.prototype.registerListeners = function() {
            $(window).on("popstate", function(event) {
                var event_state = event.originalEvent.state;
                if (event_state === null) {
                    return;
                }
                if (event_state.isMine && event_state.filterURL) {
                    _setFilterParams(event_state.filterParams);
                }
            });
        };

        Filter.prototype.show = function(callback) {
            _show(callback);
        };

        Filter.prototype.hide = function(callback) {
            _hide(callback);
        };

        Filter.prototype.showHide = function(callback) {
            if (instance.container.is(":visible")) {
                _hide(callback);
            }
            else {
                _show(callback);
            }
        };

        Filter.prototype.onActivate = function(item) {
            var $item = $(item),
                $body = $('body');
            _makeSiblingsInActive($item);
            _makeActive($item);
            var filter_params = _getFilterParams(item),
                filter_url = filter_params.url,
                filter_vals = filter_params.params;
            if (item.href) {
                // #TODO define correct reactions on codes like 3.xx, 4.xx, 5.xx
                $.ajax({
                    url: filter_url,
                    type: "GET",
                    timeout: 5000, // 5 seconds. Is it too much?
                    beforeSend: function() {
                        logger.log('GET', filter_url);
                        $body.addClass("loading");
                    },
                    statusCode: {
                        // #TODO Forbidden - provide template to require auth, etc.
                        403: function(xhr) {
                            instance.data_container.html(xhr.responseText);
                        },
                        404: function(xhr) {
                            instance.data_container.html(xhr.responseText);
                        },
                        500: function(xhr) {
                            instance.data_container.html(xhr.responseText);
                        }
                    }
                })
                    .done(function(data, textStatus, jqXHR) {
                        instance.data_container.html(data);
                    })
                    .fail(function(jqXHR, textStatus, errorThrown) {
                        // don't duplicate errors handling of statusCode
                        if (!_isHandledByStatusCode(jqXHR.status, Object.keys(this.statusCode))) {
                            instance.data_container.html(jqXHR.responseText);
                        }
                        logger.log(".fail",jqXHR, textStatus, errorThrown);
                    })
                    .always(function(data, event) {
                        $body.removeClass("loading");
                    });
                // FF browser does not work with global `event` object.
                // Have to use workaround - instead of simple
                // if (event.type !== 'popstate') {
                // use line below
                if (history.state === null || history.state.filterURL !== filter_url) {
                    logger.log("onActivate history.pushState: url", filter_url,"params",filter_params);
                    history.pushState({
                        isMine:true,
                        filterURL: filter_url,
                        filterParams: filter_vals
                    }, item.text, filter_url);
                }
            }
            else {
                logger.log("onActivate not filterURL");
            }
        };

        // Visually it looks like filter(search) in this case works in
        // the same way as filtering in tree does.
        // But here search is done against text inside lists elements (<li> tags).
        // Filtering in tree uses custom `data` attributes (like `title`, `status`).
        Filter.prototype.addSearchCapability = function(search_box,
                                                        search_box_search_icon,
                                                        search_box_count_badge,
                                                        search_box_clear_icon) {
            var sb = $(search_box),
                sb_icon_clear = $(search_box_clear_icon),
                sb_icon_search = $(search_box_search_icon),
                sb_icon_count_res = $(search_box_count_badge),
                thread = null,
                delay = 300;

            sb_icon_clear.on("click", function() {
                $.publish(evmanager.filter.clear, [ this ]);
                sb
                    .val('')
                    .trigger('keyup', 30);
            });
            // `propertychange` is for IE
            sb.on('keyup input propertychange', function(event, wait_time) {
                clearTimeout(thread);
                var $this = $(this);
                thread = setTimeout(function() {
                    var text = $this.val();
                    var res_count = 0;
                    if (text) {
                        $.each(instance.lists, function(index, value) {
                            res_count += _filterList(value, text);
                        });
                    }
                    else {
                        $.each(instance.lists, function(index, value) {
                            $(value).find("li").slideDown();
                        });
                    }
                    sb_icon_count_res.text(res_count);
                    if (res_count < 1 && sb.val().length >= 1) {
                        _updateSearchBoxClass(sb, false);
                    }
                    else {
                        _updateSearchBoxClass(sb, true);
                    }

                }, wait_time || delay);
                if (sb.val().length < 1) {
                    _updateIcons(sb_icon_search, sb_icon_clear, sb_icon_count_res, true);
                    $.publish(evmanager.filter.clear, [ this ]);
                }
                else {
                    _updateIcons(sb_icon_search, sb_icon_clear, sb_icon_count_res, false);
                }
            });
            $.subscribe(evmanager.filter.search,  function(e, val) {
                sb
                    .val(val)
                    .trigger('focus')
                    .trigger('input', 30);
            });
        };

        return instance;
    }
    return new Filter();
}(UIAPP.Logger, EventsManager));
