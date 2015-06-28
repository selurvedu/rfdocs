// At this time UIAPP should be already defined in scope of module.js!!!
// The line below was added to calm down js(lint)hint.
var UIAPP = UIAPP || {};

UIAPP.namespace('UIAPP.Stack');
UIAPP.Stack = (function (logger, evmanager) {
    "use strict";
    function Stack() {
        // the cached instance
        var instance;

        // rewrite the constructor
        Stack = function Stack() {
            return instance;
        };

        // carry over the prototype properties
        Stack.prototype = this;

        // the instance
        instance = new Stack();

        // reset the constructor pointer
        instance.constructor = Stack;

        Stack.prototype.config =  {
            modal_window: '#modal-stack',
            modal_clear: '#modal-stack-clear',
            modal_copy: '#modal-stack-copy',
            modal_save: '#modal-stack-save',
            modal_restore: '#modal-stack-restore',
            modal_buffer: '#modal-stack-buffer',
            modal_counter: '#modal-stack-counter',
            modal_max_items: $.storage.read($.storage.stack.max) || 50
        };

        // Private vars and methods
        var _copyText = " Copy",
            _richText = " Rich Text",
            _readStackFormStorage = function() {
                return $.storage.readJSON($.storage.stack);
            },
            _countItems = function() {
                return instance.mbody.find('p.kw-item').length;
            },
            _callHandler = function(handler) {
                instance.mwindow.modal("show");
                instance.mwindow.on('shown', function() {
                    handler.trigger("click");
                });
            },

            _setEnabledState = function(flag) {
                if (flag) {
                    instance.mcopy.removeAttr("disabled");
                    instance.mclear.removeAttr("disabled");
                    instance.msave.removeAttr("disabled");
                }
                else {
                    instance.mcopy.attr("disabled", true);
                    instance.mclear.attr("disabled", true);
                    instance.msave.attr("disabled", true);
                }
            },

            _replaceTextAndIcon = function(target, txt, add_icon, remove_icon) {
                target.find('i')
                    .text(txt)
                    .addClass(add_icon)
                    .removeClass(remove_icon);
            },

            _clearBuffer = function() {
                instance.mbuffer.text("");
            },

            _selectBuffer = function() {
                instance.mbuffer.select();
            },

            _showBuffer = function(flag) {
                if (flag) {
                    instance.mbuffer_div.removeClass('hidden');
                    instance.mbody.addClass('hidden');
                }
                else {
                    instance.mbody.removeClass('hidden');
                    instance.mbuffer_div.addClass('hidden');
                }
            },
            _get_keyword_with_signature = function(keyword_name, keyword_arguments) {
                if (keyword_arguments === null || keyword_arguments === undefined) {
                    return keyword_name + '\n';
                }
                var keyword_arguments_arr = keyword_arguments.split(',');
                if (keyword_arguments_arr.length === 1) {
                    return keyword_name + '  ' + keyword_arguments_arr[0] + '\n';
                }
                return keyword_name + '\n' + $.map(keyword_arguments_arr, function(value, index) {
                    return '...  ' + value.trim()
                }).join('\n')+'\n';
            },
            _prependItem = function(key, data) {
                var p = $('<p></p>', {
                        text: data['arguments'],
                        class: 'kw-item',
                        'data-nodekey': key
                    }),
                    h = $('<h4></h4>', {
                        text: data.name,
                        class: 'kw-name'
                    }),
                    small = $('<small></small>', {
                        text: "   " + data.library,
                        class: 'kw-args'
                    }),
                    span = $('<span></span>', {
                        text: "#" + data.library + "\n" + _get_keyword_with_signature(data.name, data['arguments']),
                        class: 'kw-signature hidden'
                    }),
                    sep = $('<hr />');
                small.appendTo(h);
                span.appendTo(h);
                h.prependTo(p);
                sep.appendTo(p);
                p.prependTo(instance.mbody);
            },

            _prependItemErrored = function(key, data) {
                // It would be more readable with .html() or .append() html text.
                // But need to pass in several params, thus the method below seems more suitable.
                var p = $('<p></p>', {
                        text: "Failed to retrieve data. Error: "+ data.status + " " + data.detail,
                        'data-nodekey': key
                    }),
                    h = $('<h4></h4>', {
                        text: data.name,
                        class: 'text-error'
                    }),
                    a = $('<a></a>', {
                        text: 'x',
                        class: "close",
                        'data-dismiss': "alert",
                        href: "#"
                    }),
                    d = $('<div></div>', {
                        class: 'alert alert-danger'
                    });

                a.appendTo(d);
                h.prependTo(p);
                p.appendTo(d);
                d.prependTo(instance.mbody);
            },

            _setCounter = function() {
                instance.counter = _countItems();
                instance.mcounter.text(instance.counter);
            };

        // Public methods
        // instance.init = ...
        // or
        Stack.prototype.init = function(options) {
            if (options) {
                instance.config = $.extend({}, instance.config, options);
            }
            logger.info(instance, 'inti :: config ::', instance.config);
            instance.mwindow = $(instance.config.modal_window);
            instance.mbody = instance.mwindow.find('div.modal-body');
            instance.mbuffer_div = $(instance.config.modal_buffer);
            instance.mbuffer = instance.mbuffer_div.find('textarea');
            instance.mcopy = $(instance.config.modal_copy);
            instance.msave = $(instance.config.modal_save);
            instance.mrestore = $(instance.config.modal_restore);
            instance.mclear = $(instance.config.modal_clear);
            instance.mcounter = $(instance.config.modal_counter);
            instance.counter = 0;

            // --- Start event listeners
            instance.mwindow.on('hide', function(event) {
                logger.log(instance, 'Modal Window :: hide');
                instance.mbody.removeClass('hidden');
                instance.mbuffer_div.addClass('hidden');
            });

            instance.mwindow.on('show', function(event) {
                logger.log(instance, 'Modal Window :: show');
                var cando = instance.canDo();
                if (cando.clear) {
                    _setEnabledState(true);
                }
                else {
                    _setEnabledState(false);
                }
                // either `null` or `[]`
                if (cando.restore) {
                    instance.mrestore.attr("disabled",false);
                }
                else {
                    instance.mrestore.attr("disabled",true);
                }
                if (instance.mbody.hasClass("hidden")) {
                    _replaceTextAndIcon(instance.mcopy, _richText, 'icon-refresh', 'icon-copy');
                }
                else {
                    _replaceTextAndIcon(instance.mcopy, _copyText, 'icon-copy', 'icon-refresh');
                }
            });

            $("label[for"+instance.mbuffer.attr('id')+"]").on("click", function() {
                _selectBuffer();
            });

            instance.mclear.on('click', function(event) {
                logger.log(instance, 'Modal Window :: clear');
                if ($(this).attr("disabled")) {
                    return false;
                }
                $.publish(evmanager.stack.clear, [this]);
                _setEnabledState(false);
                event.preventDefault();
                return true;
            });

            instance.msave.on('click', function(event) {
                logger.log(instance, 'Modal Window :: save');
                var $this = $(this);
                if ($this.attr("disabled")) {
                    return false;
                }
                $.publish(evmanager.stack.save, [this]);
                event.preventDefault();
                return true;
            });

            instance.mrestore.on('click', function(event) {
                logger.log(instance, 'Modal Window :: restore');
                var $this = $(this);
                if ($this.attr("disabled")) {
                    return false;
                }
                _setEnabledState(true);
                $.publish(evmanager.stack.restore, [this]);
                event.preventDefault();
                return true;
            });

            instance.mcopy.on('click', function(event) {
                logger.log(instance, 'Modal Window :: copy');
                var $this = $(this);
                if ($this.attr("disabled")) {
                    return false;
                }
                if ($this.text().toLowerCase().indexOf(_copyText.toLocaleLowerCase()) >= 0) {
                    instance.toPlainText();
                    _showBuffer(true);
                    _selectBuffer();
                    _replaceTextAndIcon(instance.mcopy, _richText, 'icon-refresh', 'icon-copy');
                    $.publish(evmanager.stack.copy, [this]);
                }
                else {
                    _showBuffer(false);
                    _replaceTextAndIcon(instance.mcopy, _copyText, 'icon-copy', 'icon-refresh');
                }
                event.preventDefault();
                return true;
            });
        }; // --- End event listeners

        Stack.prototype.addItem = function(key, data, issuccess) {
            logger.log(instance, 'Stack :: addItem :: key, data, issuccess', key, data, issuccess);
            if (!instance.isItemPresent(key)) {
                if (issuccess) {
                    _prependItem(key, data);
                }
                else {
                    _prependItemErrored(key, data);
                }
                _setCounter();
            }
        };

        Stack.prototype.popItem = function(key) {
            logger.log(instance, 'Stack :: popItem :: key', key);
            if (instance.counter > 0) {
                instance.mbody.find("p[data-nodekey='"+ key +"']").remove();
                _setCounter();
            }
        };

        Stack.prototype.popLastItem = function() {
            logger.log(instance, 'Stack :: popLastItem');
            if (instance.counter > instance.config.modal_max_items) {
                var _last = instance.mbody.find('p.kw-item').last(),
                    _last_data_key = _last.data('nodekey');
                _last.remove();
                _setCounter();
                logger.log(instance, 'Modal Window :: popLastItem', _last_data_key);
                return _last_data_key;
            }
            logger.log(instance, 'Modal Window :: popLastItem', false);
            return null;
        };

        Stack.prototype.getCounter = function() {
            return instance.counter;
        };

        Stack.prototype.isItemPresent = function(key) {
            return instance.mbody.find("p[data-nodekey='"+ key +"']").length > 0;
        };

        Stack.prototype.clear = function() {
            logger.log(instance, 'Stack :: clear');
            instance.mbody.find('p.kw-item').remove();
            _clearBuffer();
            _setCounter();
            $.storage.writeJSON($.storage.stack, []);
        };

        Stack.prototype.restore = function() {
            logger.log(instance, 'Stack :: restore');
            return _readStackFormStorage();
        };

        Stack.prototype.toPlainText = function() {
            logger.log(instance, 'Stack :: toPlainText');
            _clearBuffer();
            var items = instance.mbody.find('.kw-signature');
            $.each(items, function(index, value) {
                instance.mbuffer.append($(value).text()+"\n");
            });
        };

        Stack.prototype.save = function() {
            logger.log(instance, 'Stack :: save');
            var keys = [];
            var items = instance.mbody.find('p.kw-item');
            $.each(items, function(index, value) {
                keys.push($(value).attr('data-nodekey'));
            });
            $.storage.writeJSON($.storage.stack, keys);
        };

        Stack.prototype.copy = function() {
            logger.log(instance, 'Stack :: copy');
            _callHandler(instance.mcopy);
        };

        Stack.prototype.canDo = function() {
            var st = _readStackFormStorage(),
                clear = instance.counter !== 0,
                restore = !(st === null || st.length === 0);
            logger.log(instance, 'Stack :: canDo', {'restore': restore,'clear': clear,'save': clear,'copy': clear});
            return {
                'restore': restore,
                'clear': clear,
                'save': clear,
                'copy': clear
            };
        };

        return instance;
    }
    return new Stack();
}(UIAPP.Logger, EventsManager));