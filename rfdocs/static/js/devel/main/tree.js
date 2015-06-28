// At this time UIAPP should be already defined in scope of module.js!!!
// The line below was added to calm down js(lint)hint.
var UIAPP = UIAPP || {};


UIAPP.namespace('UIAPP.Tree');
UIAPP.Tree = (function (logger, evmanager) {
    "use strict";
    function Tree() {
        var instance;

        // rewrite the constructor
        Tree = function Tree() {
            return instance;
        };

        // carry over the prototype properties
        Tree.prototype = this;

        // the instance
        instance = new Tree();

        // reset the constructor pointer
        instance.constructor = Tree;

        Tree.prototype.config =  {
            search_form: "#search-form",
            fx: { height: "toggle", duration: 200 },
            persist: true,
            generateIds:true,
            classNames: {
                noConnector:true
            },

            initAjax: {
                type: "GET",
                url: "/dataset/load",
                traditional: true,
                data: {
                    "version": $.storage.readJSON($.storage.dataset) || []
                }
            },

            ajaxDefaults: {
                cache: true,
                dataType: "json"
            },

            iconClasses: {
                versionIconClass: {
                    closed: 'icon-folder-close',
                    opened: 'icon-folder-open'
                },
                libraryIconClass: {
                    closed: 'icon-folder-close-alt',
                    opened: 'icon-folder-open-alt'
                },
                keywordIconClass: {
                    // Instead of adding/removing classes with .addClass/.removeClass
                    // will use .attr('class',class) to replace class property.
                    // So, if there are multiple classes to use, just pass them as one string.
                    default: 'icon-key',
                    success: 'icon-key action-success',
                    loading: 'icon-spinner icon-spin',
                    fail: 'icon-warning-sign action-fail'
                }
            },

//            onSelect: function(flag, node) {
//            This is not needed as for now, because I don't filter on libraries yet, only on versions!
//                // Works on check-box (de)select.
//                // 1. Selection of leaves(keywords) is disabled.
//                // 2. (De)selection of nodes under root (versions) causes (de)selection of it's children(libraries).
//                if (node.data.isVersion) {
//                    $.each(node.childList, function(index, value) {
//                        value.select(flag);
//                    });
//                }
//            },

            onExpand: function(flag, node) {
                var node_isver = node.data.isVersion,
                    node_islib = node.data.isLibrary,
                    icon_cls = instance.config.iconClasses,
                    node_span = node._locateLeafNodeIcon(node),
                    icon_opened = null,
                    icon_closed = null;
                if (flag) {
                    if (node_isver) {
                        icon_opened = icon_cls.versionIconClass.opened;
                        node.data.iconClass = icon_opened;
                        node_span.attr('class',icon_opened);
                    }
                    else if (node_islib) {
                        icon_opened = icon_cls.libraryIconClass.opened;
                        node.data.iconClass = icon_opened;
                        node_span.attr('class',icon_opened);
                    }
                }
                else {
                    if (node_isver) {
                        icon_closed = icon_cls.versionIconClass.closed;
                        node.data.iconClass = icon_closed;
                        node_span.attr('class',icon_closed);
                    }
                    else if (node_islib) {
                        icon_closed = icon_cls.libraryIconClass.closed;
                        node.data.iconClass = icon_closed;
                        node_span.attr('class',icon_closed);
                    }
                }
            },

            onIconClick: function(node, node_span, icon) {
                // prevent for folders
                if (node.data.isFolder) {
                    return;
                }
                // proceed for nodes (leaves)
                if (instance.isMarkedNode(node.data.key) === -1) {
                    logger.debug(instance, "onIconClick :: else :: mark node");
                    logger.debug(instance, "onIconClick :: node, node_span, icon", node, node_span, icon);
                    $.ajax({
                        url: node.data.api_href,
                        type: "GET",
                        dataType: "json",
                        beforeSend: function() {
                            logger.debug(instance, "onIconClick :: ajax :: beforeSend");
                            instance.updateNodeClass(node, node_span, icon.loading);
                        },
                        statusCode: {
                            // #TODO Forbidden - provide template to require auth, etc.
                            403: function(jqXHR, textStatus, errorThrown) {
                                logger.warn(instance,
                                    "onIconClick :: ajax :: statusCode :: 403","jqXHR:",
                                    jqXHR,"textStatus:",textStatus,"errorThrown:",errorThrown);
                                var received_data = $.parseJSON(jqXHR.responseText);
                                $.extend(received_data, {name: node.data.title, status: jqXHR.status});
                                $.publish(evmanager.tree.mark_node, [node.data.key, received_data, false]);
                            },
                            404: function(jqXHR, textStatus, errorThrown) {
                                logger.warn(instance,
                                    "onIconClick :: ajax :: statusCode :: 404:","jqXHR:",
                                    jqXHR,"textStatus:",textStatus,"errorThrown:",errorThrown);
                                var received_data = $.parseJSON(jqXHR.responseText);
                                $.extend(received_data, {name: node.data.title, status: jqXHR.status});
                                $.publish(evmanager.tree.mark_node, [node.data.key, received_data, false]);
                            },
                            500: function(jqXHR, textStatus, errorThrown) {
                                logger.warn(instance,
                                    "onIconClick :: ajax :: statusCode ::  500:","jqXHR:",
                                    jqXHR,"textStatus:",textStatus,"errorThrown:",errorThrown);
                                instance.data_container.html(jqXHR.responseText);
                            }
                        }
                    })
                        .done(function(data) {
                            logger.debug(instance, "onIconClick :: ajax :: .done :: data", data);
                            $.publish(evmanager.tree.mark_node, [node.data.key, data, true]);
                            instance.updateNodeClass(node, node_span, icon.success);
                        })
                        .fail(function(jqXHR, textStatus, errorThrown) {
                            // don't duplicate errors handling of statusCode
                            if (!_isHandledByStatusCode(jqXHR.status, Object.keys(this.statusCode))) {
                                instance.data_container.html(jqXHR.responseText);
                            }
                            logger.debug(instance,
                                "onIconClick :: ajax :: .fail :: jqXHR, textStatus, errorThrown",
                                jqXHR, textStatus, errorThrown);
                            instance.updateNodeClass(node, node_span, icon.fail);
                        })
                        .always(function() {
                            logger.debug(instance, "onIconClick :: ajax :: .always");
                        });
                }
                // the node has been marked before - unmark it
                else {
                    logger.debug(instance, "onIconClick :: else :: unmark node");
                    $.publish(evmanager.tree.unmark_node, [node.data.key]);
                    instance.updateNodeClass(node, node_span, icon.default);
                }
            },

            // this function is also used by popstate event handler
            // so, check if it is not called by 'popstate' event
            onActivate: function (node) {
                if (node.data.href) {
                    $.ajax({
                        url: node.data.href,
                        type: "GET",
                        beforeSend: function() {
                            $(node.span).append('    <span id="node-is-loading" class="spinner"><i class="icon-spin icon-spinner icon-large"></i></span>');
                            logger.debug(instance, 'onActivate :: ajax :: GET node', node);
                            instance.data_container.fadeOut("fast");
                        },
                        statusCode: {
                            // #TODO Forbidden resp - provide template to require auth, etc.
                            403: function(jqXHR, textStatus, errorThrown) {
                                logger.warn(instance, 'onActivate :: ajax :: statusCode :: 403', jqXHR);
                                instance.data_container.html(jqXHR.responseText);
                            },
                            404: function(jqXHR, textStatus, errorThrown) {
                                logger.warn(instance, 'onActivate :: ajax :: statusCode :: 404', jqXHR);
                                instance.data_container.html(jqXHR.responseText);
                            },
                            500: function(jqXHR, textStatus, errorThrown) {
                                logger.warn(instance, 'onActivate :: ajax :: statusCode :: 500', jqXHR);
                                instance.data_container.html(jqXHR.responseText);
                            }
                        }
                    })
                        .done(function(data, textStatus, jqXHR) {
                            logger.debug(instance, 'onActivate :: ajax :: .done :: 500');
                            instance.data_container.html(data);
                        })
                        .fail(function(jqXHR, textStatus, errorThrown) {
                            // don't duplicate errors handling of statusCode
                            if (!_isHandledByStatusCode(jqXHR.status, Object.keys(this.statusCode))) {
                                instance.data_container.html(jqXHR.responseText);
                            }
                            logger.warn(instance, 'onActivate :: ajax :: .fail :: jqXHR, textStatus, errorThrown',
                                jqXHR, textStatus, errorThrown);
                        })
                        .always(function(data, event) {
                            logger.debug(instance, 'onActivate :: ajax :: .always');
                            $('#node-is-loading').remove();
                            instance.data_container.fadeIn("fast");
                        });

                    // FF browser does not work with global `event` object.
                    // Have to use workaround - instead of simple
                    // if (event.type !== 'popstate') {
                    // use line below
                    if (history.state === null || history.state.nodeKey !== node.data.key) {
                        history.pushState({isMine:true, nodeKey: node.data.key}, node.data.title, node.data.href);
                    }
                }
                else {
                    // do nothing?
                }
            },

            onPostInit: function(isReloading, isError) {
                // Dynatree persistence works somewhat strange.
                // Looks like it returns coockieID-Active randomly.
                // So, the value which I have in URL always differs from tree.getActiveNode().
                // Here I force activation of current (as per URL) node.
                if (isReloading) {
                    $.publish(evmanager.page.reload, [this]);
                }
                if (isError) {
                    logger.error("ERROR!!!");
                }
            }
        };
        // Private vars and methods
        var marked_nodes = [],
            _isHandledByStatusCode = function(status, codes) {
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
            },
            _updateInitAjaxOpts = function(opts) {
                var old_opts = instance.config.initAjax;
                old_opts.data = opts;
                return old_opts;
            };

        // Public methods
        Tree.prototype.init = function (locator, options) {
            instance.container = $(locator || "#tree");
            if (options) {
                instance.container.dynatree($.extend({}, instance.config, options));
            }
            else {
                instance.container.dynatree(instance.config);
            }
            logger.info(instance, 'init :: config', instance.config);
            instance.search_form = $(instance.config.search_form);
            instance.dtree = instance.container.dynatree("getTree");
            instance.dtroot = instance.container.dynatree("getRoot");
            instance.data_container = $(UIAPP.LocatorManager.data_container);

            instance.search_form.submit(function(event) {
                event.preventDefault();
            });

        };

        Tree.prototype.updateNodeClass = function(node, node_span, status) {
            logger.log(instance, 'updateNodeClass :: node, node_span, status', node, node_span, status);
            node_span.attr("class", status);
            node.data.iconClass = status;
        };

        Tree.prototype.isMarkedNode = function(key) {
            logger.log(instance, 'isMarkedNode :: key', key);
            return $.inArray(key, marked_nodes);
        };

        Tree.prototype.getMarkedNodes = function() {
            logger.log(instance, 'getMarkedNodes');
            return marked_nodes;
        };

        Tree.prototype.markNode = function(key) {
            logger.log(instance, 'markNode :: key', key);
            marked_nodes.push(key);
        };

        Tree.prototype.unmarkNode = function(key, key_was_popped) {
            logger.log(instance, 'unmarkNode :: key, key_was_popped', key, key_was_popped);
            if (!key || key === null) {
                return;
            }
            var position = instance.isMarkedNode(key);
            if (position !== -1) {
                marked_nodes.splice(position, 1);
                // need this hook to handle stack limit
                if (key_was_popped) {
                    var node = instance.dtree.getNodeByKey(key),
                        node_span = node._locateLeafNodeIcon(node);
                    instance.updateNodeClass(node, node_span, instance.config.iconClasses.keywordIconClass.default);
                }
            }
        };

        Tree.prototype.clearMarkedNodes = function() {
            logger.log(instance, 'clearMarkedNodes');
            var icon_default = instance.config.iconClasses.keywordIconClass.default;
            $.each(marked_nodes, function(idx, key) {
                var node = instance.dtree.getNodeByKey(key),
                    node_span = node._locateLeafNodeIcon(node);
                instance.updateNodeClass(node, node_span, icon_default);
            });
            marked_nodes = []; //is it safe? or use FOR loop instead of $.each and splice inside FOR loop?
        };

        Tree.prototype.lock = function() {
            logger.log(instance, 'lock');
            // Clear cookies
            $.cookie(instance.config.cookieId + "-active", "");
            $.cookie(instance.config.cookieId + "-focus", "");
            $.cookie(instance.config.cookieId + "-expand", "");
            $.cookie(instance.config.cookieId + "-select", "");
            // Clear stack
            $.publish(evmanager.stack.clear, [this]);
            // Get selected nodes just before the tree is going to be locked
            var nodes = instance.dtree.getSelectedNodes(true),
                items = [];
            $.each(nodes, function(index, node){
                items.push(node.data.title);
            });
            $.storage.writeJSON($.storage.dataset, items);
            instance.init(null, {
                checkbox: false,
                initAjax: _updateInitAjaxOpts({version: items})
            });
            instance.dtree.reload();
            // Don't force reload, instead ask user to reload the page
            // window.location = window.location.origin;
            // This gives a possibility to review dataset
            $.publish(evmanager.toolbar.ask_reload, [this]);
        };

        Tree.prototype.unlock = function() {
            logger.log(instance, 'unlock');
            // Clear stack
            $.publish(evmanager.stack.clear, [this]);
            $.storage.writeJSON($.storage.dataset, []);
            instance.init(null, {
                checkbox: true,
                initAjax: _updateInitAjaxOpts({version: []})
            });
            instance.dtree.reload();
        };

        Tree.prototype.show = function(callback) {
            logger.log(instance, 'show');
            _show(callback);
        };

        Tree.prototype.hide = function(callback) {
            logger.log(instance, 'hide');
            _hide(callback);
        };

        Tree.prototype.showHide = function(callback) {
            logger.log(instance, 'showHide');
            if (instance.container.is(":visible")) {
                _hide(callback);
            }
            else {
                _show(callback);
            }
        };

        Tree.prototype.addSearchCapability = function(search_box,
                                                      search_box_search_icon,
                                                      search_box_count_badge,
                                                      search_box_clear_icon) {
            logger.log(instance,
                'addSearchCapability :: search_box, search_box_search_icon, search_box_count_badge, search_box_clear_icon',
                search_box, search_box_search_icon, search_box_count_badge, search_box_clear_icon);
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
                    var res_count = instance.dtroot.search($this.val());
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

        Tree.prototype.registerListeners = function() {
            (function() {
                hiJax(instance.data_container, function(event, elem_target) {
                    // if the link is an element of the tree, it will have `data-nodekey` attribute,
                    // otherwise the link must have HTML `data-` attribute,`data-nodekey`.
                    // If the link can be identified by it's href - it will be synced with corresponding node in tree.
                    var node_key = elem_target.attr('data-nodekey') || elem_target.data('nodekey');
                    if (node_key) {
                        UIAPP.shared.Tree.dtree.activateKey(node_key);
                    }
                    else {
                        var href = elem_target.attr('href');
                        // don't prevent default `a` tag behavior
                        if (href.indexOf("#") === 0) {
                            return;
                        }
                        if (UIAPP.shared.Tree.dtree.activateHref(href) === null) {
                            // don't prevent default `a` tag behavior
                            return;
                        }
                    }
                    // if we get here, we have element of tree
                    // prevent default `a` tag behavior
                    event.preventDefault();
                });
            })();
            //With JQuery's event handler we get state from event.originalEvent.state
            $(window).on("popstate", function(event) {
                var event_state = event.originalEvent.state;
                if (event_state === null) {
                    return;
                }
                if (event_state.isMine && event_state.nodeKey) {
                    instance.dtree.activateKey(event_state.nodeKey);
                }
            });
        };

        return instance;
    }
    return new Tree();
}(UIAPP.Logger, EventsManager));