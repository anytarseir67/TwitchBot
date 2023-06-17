const ws = require('ws');

const getSongControls = require("../../providers/song-controls");

/** @param {Electron.BrowserWindow} win */
module.exports = async (win) => {
    const { next } = getSongControls(win);
    const socket = new ws('ws://127.0.0.1:1610/');
    socket.on('error', console.error);
    
    socket.on('message', function message(data) {
        if (data.toString() == "skip") {
            next()
        }
    });
}


