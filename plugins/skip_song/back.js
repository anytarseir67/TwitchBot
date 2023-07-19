/* this whole thing is fucking cursed btw  */

const ws = require('ws');
const { BrowserWindow } = require('electron')
const fetch = require('node-fetch');
var socket;

const getSongControls = require("../../providers/song-controls");

var js_string = `var sleep = new Promise(r => setTimeout(r, 2000));
sleep.then(() => {
    document.querySelector("[aria-label=Shuffle]").click();
})`

const log = async (str) => {
    let data = {
        text: str
    }
	const port = 1608;
	headers = {
		'Content-Type': 'application/json',
		'Accept': 'application/json',
		'Access-Control-Allow-Headers': '*',
		'Access-Control-Allow-Origin': '*'
	}
	const url = `http://localhost:${port}/log`;
	fetch(url, { method: 'POST', headers, body: JSON.stringify({ data }) }).catch(e => console.log(`Error: '${e.code || e.errno}' - when trying to access obs-tuna webserver at port ${port}`));
}

const conn_socket = async (win, ran) => {
    if (ran === true) {
        if (socket.readyState == socket.CLOSED) {
            log("re-opening socket");
            socket = new ws('ws://127.0.0.1:1610/');
            await setup_socket(win)
        }
    }
    else {
        log("making new socket");
        socket = new ws('ws://127.0.0.1:1610/');
        await setup_socket(win)
    }
}

const setup_socket = async (win) => {
    const { playPause, previous, next, go10sBack} = getSongControls(win);
    socket.on('error', log);
    socket.on('message', function message(data) {
        var resp = JSON.parse(data.toString())
        if (resp.type == "skip") {
            log("skip")
            next()
            log("skipped")
        }
        else if (resp.type == "previous") {
            log("previous")
            for (let i = 0; i < 60; i++) {
                go10sBack()
            }
            previous()
            log("previoused...?")
        }
        else if (resp.type == "playpause") {
            log("playpause")
            playPause()
            log("playpaused...?")
        }
        else if (resp.type == "playlist") {
            var window = BrowserWindow.getAllWindows()
            window = window[0]
            try {
                window.webContents.loadURL(resp.url).then(() => {
                    log("load")
                    window.webContents.executeJavaScript(js_string, true)
                })
            }
            catch ({ name, message }) {
                log(name)
                log(message)
            }
        }
    });
}

/** @param {Electron.BrowserWindow} win */
module.exports = async (win) => {
    await conn_socket(win, false)
    setInterval(conn_socket, 2000, win, true)
}