#!/usr/bin/env node


if(process.argv.length != 4) {
    console.log("Usage: <exec> <host> <port>");
    process.exit();
}
var net = require('net');
process.stdout.write("Connecting to the server...");
net.connect(process.argv[3], process.argv[2]).on('connect', function() {
    console.log("Success");
}).on('error', function(error) {
    this.setTimeout(1, function() {
        this.connect(process.argv[3], process.argv[2]);
    });
}).on('data', function(data) {
    var parsed = JSON.parse(data);
    var keys = Object.keys(parsed);
    if(keys[0] == 'welcome') {
        console.log(parsed.welcome);
        this.write(JSON.stringify({'state': null}));
    } else if(keys[0] == 'state') {
        var output = ["Server state:"];
        for(var k in parsed.state) {
            output.push(k + ": " + parsed.state[k]);
        }
        console.log(output.join('\n'));
        this.end();
    }
});
