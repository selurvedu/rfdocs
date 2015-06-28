// At this time UIAPP should be already defined in scope of module.js!!!
// The line below was added to calm down js(lint)hint.
var UIAPP = UIAPP || {};

UIAPP.namespace('UIAPP.ToolBar');
UIAPP.ToolBar = (function (logger, evmanager) {
    "use strict";
    function ToolBar() {
        // the cached instance
        var instance;

        // rewrite the constructor
        ToolBar = function ToolBar() {
            return instance;
        };

        // carry over the prototype properties
        ToolBar.prototype = this;

        // the instance
        instance = new ToolBar();

        // reset the constructor pointer
        instance.constructor = ToolBar;

        // All the functionality.
        // Private vars and methods
        var _dataset = {
                is_locked: function() {
                    return instance.dataset.edit_ico.hasClass(instance.config.dataset.icons.locked);
                },
                lockUnlock: function(is_locked) {
                    var locked = instance.config.dataset.icons.locked,
                        unlocked = instance.config.dataset.icons.unlocked;
                    if (is_locked) {
                        instance.dataset.edit_ico
                            .text(' Save')
                            .addClass(unlocked)
                            .removeClass(locked);
                    }
                    else {
                        instance.dataset.edit_ico
                            .text(' Edit')
                            .addClass(locked)
                            .removeClass(unlocked);
                    }

                }
            },
            _badge = {
                will_add: function(locator){
                    locator.addClass(instance.config.badge.success);
                    locator.removeClass(instance.config.badge.important);
                },
                will_remove: function(locator){
                    locator.addClass(instance.config.badge.important);
                    locator.removeClass(instance.config.badge.success);
                }
            };

        // Public vars and methods
        ToolBar.prototype.config =  {
            stack: {
                menu: "#toolbar-stack-menu",
                show: '#toolbar-stack-show',
                copy: '#toolbar-stack-copy',
                save: '#toolbar-stack-save',
                restore: '#toolbar-stack-restore',
                clear: '#toolbar-stack-clear',
                counter: '#toolbar-stack-counter'
            },
            badge: {
                success:'badge-success',
                important: 'badge-important'
            },
            dataset : {
                menu: '#toolbar-dataset-menu',
                edit: '#toolbar-dataset-edit',
                icons: {
                    locked: 'icon-lock',
                    unlocked: 'icon-unlock'
                }
            },
            reload_location: '#toolbar-reload-location'
        };

        ToolBar.prototype.init = function(options) {
            if (options) {
                instance.config = $.extend({}, instance.config, options);
            }
            logger.info(instance, 'init :: config ::', instance.config);
            instance.tstack = {
                menu: $(instance.config.stack.menu),
                show: $(instance.config.stack.show),
                copy: $(instance.config.stack.copy),
                save: $(instance.config.stack.save),
                restore: $(instance.config.stack.restore),
                clear: $(instance.config.stack.clear),
                counter: $(instance.config.stack.counter)
            };

            instance.dataset = {
                menu: $(instance.config.dataset.menu),
                edit: $(instance.config.dataset.edit),
                edit_ico: $(instance.config.dataset.edit).find('i')
            };
            instance.data_container = $(UIAPP.LocatorManager.data_container);
            instance.page_reload = $(instance.config.reload_location);

            instance.page_reload.on("click", function(event) {
                logger.debug(instance, 'instance.page_reload.on click');
                event.preventDefault();
                location.reload();
            });

            instance.dataset.edit.on('click', function(event) {
                logger.debug(instance, 'instance.dataset.edit click');
                var state = _dataset.is_locked();
                instance.dataset.menu.toggleClass('action-required-green', state);
                _dataset.lockUnlock(state);
                $.publish(evmanager.toolbar.dataset_edit, [state]);
                event.preventDefault();
            });

            instance.tstack.menu.on('click', function(event) {
                logger.debug(instance, 'instance.tstack.menu click');
                $.publish(evmanager.stack.cando, [this]);
            });

            instance.tstack.clear.on('click', function(event) {
                logger.debug(instance, 'instance.tstack.clear click');
                $.publish(evmanager.stack.clear, [this]);
                event.preventDefault();
            });

            instance.tstack.copy.on('click', function(event) {
                logger.debug(instance, 'instance.tstack.copy click');
                $.publish(evmanager.stack.copy, [this]);
                event.preventDefault();
            });

            instance.tstack.save.on('click', function(event) {
                logger.debug(instance, 'instance.tstack.save click');
                $.publish(evmanager.stack.save, [this]);
                event.preventDefault();
            });

            instance.tstack.restore.on('click', function(event) {
                logger.debug(instance, 'instance.tstack.restore click');
                $.publish(evmanager.stack.restore, [this]);
                event.preventDefault();
            });

            instance.tstack.counter
                .on('mouseenter', function(event) {
                    logger.debug(instance, 'instance.tstack.counter mouseenter');
                    $.publish(evmanager.toolbar.counter_hover,
                        [instance.tstack.counter, _badge.will_remove, _badge.will_add]);
                })
                .on('mouseleave', function(event) {
                    logger.debug(instance, 'instance.tstack.counter mouseleave');
                    $(this).removeClass(instance.config.badge.success+" "+instance.config.badge.important);
                }).
                on('click', function(event) {
                    logger.debug(instance, 'instance.tstack.counter click');
                    $.publish(evmanager.toolbar.counter_click, [this]);
                    $(this).toggleClass(instance.config.badge.success+" "+instance.config.badge.important);
                    event.preventDefault();
                    event.stopPropagation();
                });
        };

        ToolBar.prototype.enableMenuItems = function(clear, copy, save, restore) {
            logger.log(instance, 'enableMenuItems :: clear, copy, save, restore', clear, copy, save, restore);
            instance.tstack.clear.attr("disabled",!clear);
            instance.tstack.copy.attr("disabled",!copy);
            instance.tstack.save.attr("disabled",!save);
            instance.tstack.restore.attr("disabled",!restore);
        };

        ToolBar.prototype.updateCounter = function(val) {
            logger.log(instance, 'updateCounter :: val ::', val);
            instance.tstack.counter.text(val);
        };

        ToolBar.prototype.askReload = function() {
            logger.log(instance, 'askReload');
            instance.page_reload.parent('li').removeClass('hidden');
        };
        return instance;
    }
    return new ToolBar();
}(UIAPP.Logger, EventsManager));