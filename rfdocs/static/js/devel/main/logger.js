// At this time UIAPP should be already defined in scope of module.js!!!
// The line below was added to calm down js(lint)hint.
var UIAPP = UIAPP || {};

UIAPP.namespace('UIAPP.Logger');
UIAPP.Logger = (function () {
    "use strict";
    function Logger() {
        // the cached instance
        var instance;

        // rewrite the constructor
        Logger = function Logger() {
            return instance;
        };

        // carry over the prototype properties
        Logger.prototype = this;

        // the instance
        instance = new Logger();

        // reset the constructor pointer
        instance.constructor = Logger;

        // Private methods and vars
        var enabled = true,
            can_log = window.console ? true: false,
            modes = {
                info: 1,
                log: 2,
                warn: 3,
                debug: 4,
                trace: 5
            },
            mode = modes.debug,
            _check = function(level) {
                if (!can_log) {
                    // browser can't log
                    return false;
                }
                return (enabled && mode >= level);
            };

        // Public part
        Logger.prototype.setMode = function(set_mode) {
            mode = modes[set_mode];
        };

        Logger.prototype.enable = function() {
            enabled = true;
        };

        Logger.prototype.disable = function() {
            enabled = false;
        };

        Logger.prototype.log = function() {
            if (_check(modes.log)) {
                var args = [];
                for (var i=0; i<arguments.length; i++) {args.push(arguments[i]);}
                console.log.apply(console, args);
            }
        };

        Logger.prototype.info = function() {
            if (_check(modes.info)) {
                var args = [];
                for (var i=0; i<arguments.length; i++) {args.push(arguments[i]);}
                console.info.apply(console, args);
            }
        };

        Logger.prototype.warn = function() {
            if (_check(modes.warn)) {
                var args = [];
                for (var i=0; i<arguments.length; i++) {args.push(arguments[i]);}
                console.warn.apply(console, args);
            }
        };

        Logger.prototype.error = function() {
            if (_check(modes.error)) {
                var args = [];
                for (var i=0; i<arguments.length; i++) {args.push(arguments[i]);}
                console.error.apply(console, args);
            }
        };

        Logger.prototype.debug = function() {
            if (_check(modes.debug)) {
                var args = [];
                for (var i=0; i<arguments.length; i++) {args.push(arguments[i]);}
                console.debug.apply(console, args);
            }
        };

        Logger.prototype.trace = function() {
            if (_check(modes.trace)) {
                var args = [];
                for (var i=0; i<arguments.length; i++) {args.push(arguments[i]);}
                console.trace();
            }
        };
        return instance;
    }
    return new Logger();
}());
