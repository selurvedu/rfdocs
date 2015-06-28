var EventsManager = {
    page: {
        reload: "page/reload"
    },
    filter: {
        search: "filter/search",
        clear: "filter/clear"
    },
    storage: {
        get: "storage/get",
        set: "storage/set",
        clear: "storage/clear"
    },
    tree: {
        mark_node: "tree/mark",
        unmark_node: "tree/unmark",
        lock: "tree/lock",
        unlock: "tree/unlock"
    },
    stack: {
        add: "stack/add",
        pop: "stack/pop",
        copy: "stack/copy",
        save: "stack/save",
        restore: "stack/restore",
        clear: "stack/clear",
        cando: "stack/cando"
    },
    toolbar: {
        counter_click: "toolbar/counter_click",
        counter_hover: "toolbar/counter_hover",
        dataset_edit: "toolbar/dataset_edit",
        ask_reload: "toolbar/ask_reload"
    },
    item: {
        highlight: "item/highlight",
        unhighlight: "item/unhighlight",
        getcontainer: "item/getcontainer"
    }
};

// GLOBAL.
// I don't want to pass either of objects below as an additional params to all classes.

// Publish/Subscribe pattern implementation for jQuery >= 1.7.
// Uses `.on()` and `.off()` to work with custom(user-defined) events.
(function($) {
    "use strict";
    var o = $({});
    $.subscribe = function() {
        o.on.apply(o, arguments);
    };
    $.unsubscribe = function() {
        o.off.apply(o, arguments);
    };
    $.publish = function() {
        o.trigger.apply(o, arguments);
    };
}(jQuery));


// Simplified strategy pattern that provides facade for localStorage/sessionStorage API.
(function($){
    "use strict";
    $.storage = {
        _storage: localStorage,
        dataset: "dataset",
        stack: "stack"
    };
    $.storage.readJSON = function(item) {
        return JSON.parse(this._storage.getItem(item));
    };
    $.storage.writeJSON = function(item, value) {
        this._storage.setItem(item, JSON.stringify(value));
    };
    $.storage.read = function(item) {
        return this._storage.getItem(item);
    };
    $.storage.write = function(item, value) {
        this._storage.setItem(item, value);
    };
    $.storage.remove = function(item) {
        this._storage.removeItem(item);
    };
    $.storage.clear = function() {
        this._storage.clear();
    };
    $.storage.getLength = function(item) {
        return item === null ?
            this._storage.length : this._storage.getItem(item).length;
    };
}(jQuery));
