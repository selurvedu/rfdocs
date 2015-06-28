// At this time UIAPP should be already defined in scope of module.js!!!
// The line below was added to calm down js(lint)hint.
var UIAPP = UIAPP || {};

UIAPP.namespace('UIAPP.Item');
UIAPP.Item = (function (logger, evmanager) {
    "use strict";
    function Item() {
        // the cached instance
        var instance;

        // rewrite the constructor
        Item = function Item() {
            return instance;
        };

        // carry over the prototype properties
        Item.prototype = this;

        // the instance
        instance = new Item();

        // reset the constructor pointer
        instance.constructor = Item;

        // private vars and methods
        var selectElementContents = function(el) {
                var range;
                if (window.getSelection && document.createRange) {
                    range = document.createRange();
                    var sel = window.getSelection();
                    range.selectNodeContents(el);
                    sel.removeAllRanges();
                    sel.addRange(range);
                } else if (document.body && document.body.createTextRange) {
                    range = document.body.createTextRange();
                    range.moveToElementText(el);
                    range.select();
                }
            },

            _activateInstack = function(activate, issuccess) {
                var container = $(instance.config.instack.container),
                    success = $(instance.config.instack.success),
                    fail = $(instance.config.instack.fail);
                container.attr("data-is-instack",activate);
                if (activate) {
                    if (issuccess) {
                        container
                            .addClass("highlight-green")
                            .removeClass("highlight-red");
                        success.removeClass("hidden");
                        fail.addClass("hidden");
                    }
                    else {
                        container
                            .addClass("highlight-red")
                            .removeClass("highlight-green");

                        success.addClass("hidden");
                        fail.removeClass("hidden");
                    }
                }
            };

        // all the functionality
        Item.prototype.config =  {
            container: UIAPP.LocatorManager.data_container,
            article: 'article',
            item_name: '.item-name',
            item_subheading: '.item-subheading',
            instack: {
                container: '#instack-active-container',
                success: "#instack-success",
                fail: "#instack-fail"
            },
            filter_icon: '#filter-active-container',
            filter_tags: '.filter-tags'
        };

        Item.prototype.init = function(options) {
            if (options) {
                instance.config = $.extend({}, instance.config, options);
            }
            logger.info(instance, 'init :: config ::', instance.config);
            instance.registerListeners();
        };

        Item.prototype.highlightActive = function(key, issuccess) {
            if (key !== $(instance.config.article).data('nodekey')) {
                logger.log(instance, 'highlightActive :: key ::', key, false);
                return;
            }
            logger.log(instance, 'highlightActive :: key ::', key, true);
            _activateInstack(true, issuccess);
        };

        Item.prototype.getContainer = function() {
            logger.log(instance, 'getContainer');
            return $(instance.config.container);
        };

        Item.prototype.unhighlightActive = function(key) {
            if (key !== $(instance.config.article).data('nodekey')) {
                logger.log(instance, 'unhighlightActive :: key ::', key, false);
                return;
            }
            logger.log(instance, 'unhighlightActive :: key ::', key, true);
            _activateInstack(false, false);
        };

        Item.prototype.getActive = function() {
            logger.log(instance, 'getActive');
            return $(instance.config.article).data('nodekey');
        };

        Item.prototype.highlightBlind = function() {
            // should be used on page load
            logger.log(instance, 'highlightBlind');
            _activateInstack(true, true);
        };

        Item.prototype.unhighlightBlind = function() {
            logger.log(instance, 'unhighlightBlind');
            _activateInstack(false, true);
        };

        Item.prototype.registerListeners = function() {
            // these listeners are intended to be used on item load through AJAX
            // so, must be added into proper django template.
            // Don't want to attach these listeners to `body` - so use as below
            logger.log(instance, 'registerListeners');
            $(document).ready(function() {
                try {
                    $.publish(evmanager.item.highlight, [
                        instance.getActive(),
                        instance.highlightBlind,
                        instance.unhighlightBlind
                    ]);
                }
                catch(err) {
                    logger.warn(err.message);
                }

                var filter_tags = $(instance.config.filter_tags),
                    filter_icon = {
                        ico: $(instance.config.filter_icon),
                        makeVisible: function() {
                            filter_icon.ico.addClass("highlight");
                        },
                        makeInvisible: function() {
                            filter_icon.ico.removeClass("highlight");
                        },
                        makeActive: function() {
                            filter_icon.ico.attr("data-is-active",true);
                        },
                        makeInactive: function() {
                            filter_icon.ico.attr("data-is-active",false);
                        }
                    },
                    mix_class = function() {
                        return Array.prototype.slice.call(arguments).join(" ");
                    };

                $.subscribe(evmanager.filter.clear, function() {
                    // de-activate all filters
                    $('[data-filter-active="true"]').attr("data-filter-active", false);
                    filter_icon.makeInactive();
                });

                // Add events handlers for tags
                filter_tags
                    .on("mouseenter", "a", function(event) {
                        filter_icon.makeVisible();
                    })
                    .on("mouseleave", "a", function(event){
                        filter_icon.makeInvisible();
                    })
                    .on("click", "a", function(event) {
                        $('[data-filter-active="true"]').attr("data-filter-active", false);
                        filter_icon.makeActive();
                        var $this = $(this),
                            text = $this.text().trim()+":";
                        $this.attr("data-filter-active", true);

                        // stop default anchor tag events
                        event.preventDefault();
                        event.stopPropagation();

                        // publish event
                        $.publish(evmanager.filter.search, [ text ]);
                    });

                // Add event handlers for item
                $(instance.config.item_subheading).on("click", function() {
//                    selectElementContents($(this).next('p').get(0));
                    selectElementContents($(this).parent('section').get(0));
                });

//                $(instance.config.item_subheading).next('.doc, .robotdoc').on("mouseenter", function() {
//                    logger.log('Table clicked');
//                });

                $(instance.config.item_name)
                    .on("mouseenter", "a", function(event) {
                        filter_icon.makeVisible();
                    })
                    .on("mouseleave", "a", function(event){
                        filter_icon.makeInvisible();
                    })
                    .on("click", "a", function(event) {
                        $('[data-filter-active="true"]').attr("data-filter-active", false);
                        filter_icon.makeActive();
                        var $this = $(this);
                        var text =  $(instance.config.article).attr('data-type') === 'keyword' ?
                            $this.text().trim() : $this.text().trim() + ":";
                        $this.attr("data-filter-active", true);
                        event.preventDefault();
                        event.stopPropagation();

                        // publish event
                        $.publish(evmanager.filter.search, [ text ]);
                    });
            });
        };

        return instance;
    }
    return new Item();
}(UIAPP.Logger, EventsManager));