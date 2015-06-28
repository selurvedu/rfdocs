/*
 This is the main JavaScript module which works with end-user interface.
*/

// At this time UIAPP should be already defined in scope of module.js!!!
// The line below was added to calm down js(lint)hint.
var UIAPP = UIAPP || {};

UIAPP.namespace('UIAPP.shared');
UIAPP.shared = (function() {
    "use strict";

    // Private properties, which should be used only inside of current module
    // Dependencies for module
    var logger = UIAPP.Logger,
        item = UIAPP.Item,
        tree = UIAPP.Tree,
        filter = UIAPP.Filter,
        stack = UIAPP.Stack,
        toolbar = UIAPP.ToolBar;

    // Manage logger for all apps in module.
    // Enable/disable, set log level here for all apps.
    logger.disable();
    //logger.enable();
    /*
     This is some kind of Mediator pattern, that
     allows loose coupling between classes(objects of module/namespace).
     Other objects in this module use Mediator to update each other.
     Mediator is subscribed for a set of custom events.
     Objects that want to update other objects should send correct event so they
     can be properly handled by Mediator.
     * */
    (function(evmanager){
        // Subscribe to custom events from other objects.
        // Ideally mediator should not reply to the sender
        // (do not publish other events in response to received events).
        $.subscribe(evmanager.tree.mark_node,  function(e, key, data, issuccess) {
            // Get the library and version info from parent (library node)
            // in UI instead of making larger queries to DB.
            var parent_lib = tree.dtree.getNodeByKey(key).getParent();
            data['library'] = parent_lib.parent.data.title + '['+parent_lib.data.title+']';
            stack.addItem(key, data, issuccess);
            var is_popped_key = stack.popLastItem();
            tree.unmarkNode(is_popped_key, is_popped_key);
            tree.markNode(key);
            item.highlightActive(key, issuccess);
            toolbar.updateCounter(stack.getCounter());
        });

        $.subscribe(evmanager.tree.unmark_node,  function(e, key) {
            stack.popItem(key);
            tree.unmarkNode(key, null);
            item.unhighlightActive(key);
            toolbar.updateCounter(stack.getCounter());
        });

        $.subscribe(evmanager.toolbar.counter_click,  function(e) {
            var node = tree.dtree.getActiveNode();
            // if node === null - currently active item is loaded,
            // but now it's node is not visible in the tree, so
            // get that node and then fire `onIconClick` event
            if (node === null) {
                node = tree.dtree.getNodeByKey(item.getActive());
                node.focus();
            }
            tree.config.onIconClick(node,
                node._locateLeafNodeIcon(node),
                tree.config.iconClasses.keywordIconClass);
        });

        $.subscribe(evmanager.toolbar.dataset_edit, function(e, state) {
            if (state) {
                tree.unlock();
            }
            else {
                tree.lock();
            }
        });

        $.subscribe(evmanager.toolbar.counter_hover,  function(e, locator, callback_yes, callback_no) {
            if (stack.isItemPresent(item.getActive())) {
                callback_yes(locator);
            }
            else {
                callback_no(locator);
            }
        });

        $.subscribe(evmanager.item.highlight,  function(e, key, callback_yes, callback_no) {
            if (stack.isItemPresent(key)) {
                callback_yes();
            }
            else {
                callback_no();
            }
        });

        $.subscribe(evmanager.stack.clear, function(e) {
            stack.clear();
            tree.clearMarkedNodes();
            item.unhighlightBlind();
            toolbar.updateCounter(stack.getCounter());
        });

        $.subscribe(evmanager.stack.copy, function(e) {
            stack.copy();
        });

        $.subscribe(evmanager.stack.save, function(e) {
            stack.save();
        });

        $.subscribe(evmanager.stack.restore, function(e) {
            var ico = tree.config.iconClasses.keywordIconClass,
                items = stack.restore();
            $.each(items, function(index, value) {
                var node = tree.dtree.getNodeByKey(value),
                    node_span = node._locateLeafNodeIcon(node);
                tree.config.onIconClick(node, node_span, ico);
            });
        });

        $.subscribe(evmanager.stack.cando, function(e) {
            var can = stack.canDo();
            toolbar.enableMenuItems(can.clear, can.copy, can.save, can.restore);
        });

        $.subscribe(evmanager.page.reload, function(e) {
            var key = item.getActive();
            if (key) {
                // After dataset has been edited we may run into state
                // when currently loaded page(keyword, version or library)
                // is not in dataset anymore.
                // For such case just focus on and activate first child
                // of tree (first 'version' container).
                var dtnode = tree.dtree.activateKey(key);
                if (dtnode === null) {
                    var children = tree.dtroot.getChildren();
                    for (var i=0;i<children.length;i++) {
                        var child = children[i];
                        if (child.data.isVersion) {
                            child.focus();
                            return child.activate();
                        }
                    }
                }
            }
            else {
                return tree.dtree.reactivate(true);
            }
        });

        $.subscribe(evmanager.toolbar.ask_reload, function(e) {
            toolbar.askReload();
        });

    })(EventsManager);

    // Make these objects public. Do not reveal the pseudo-Mediator outside of this module.
    // The objects below should be accessed from UIAPP.shared object (for example in <script> tags).
    return {
        Logger: logger,
        Item: item,
        Tree: tree,
        Filter: filter,
        Stack: stack,
        Toolbar: toolbar
    };
}());
