var system = require('system'),
    url;

if (system.args.length !== 2) {
    console.error('Usage: '+ system.args[0] + ' <some_url>');
    phantom.exit();
}
else {
    url = system.args[1];
}

var page = require('webpage').create();
page.open(url, function (status) {
    if (status !== 'success') {
        console.error('Failed to fetch resource from URL:', url);
    } else {
        console.log(page.content);
    }
    phantom.exit();
});