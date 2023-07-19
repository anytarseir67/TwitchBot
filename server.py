from aiohttp import web
from websockets import server
from websockets.exceptions import ConnectionClosedError
import asyncio
import json
from functools import partial

routes = web.RouteTableDef()

async def socket(websocket: server.WebSocketServerProtocol, path) -> None:
    print("socket connected")
    app.socket = websocket
    try:
        async for msg in websocket:
            ...
    except ConnectionClosedError:
        print("socket disconnected...")

class Server(web.Application):
    def __init__(self) -> None:
        super().__init__()
        self.name: str = None
        self.artists: str = None
        self.time: int = None
        self.dur: int = None
        self.playlist: str = None
        self.socket: server.WebSocketServerProtocol = None

    def run(self) -> None:
        loop = asyncio.get_event_loop()
        self.add_routes(routes)

        # god i hate this so fucking much, why aiohttp socket no work ;-;
        start_server = server.serve(socket, 'localhost', 1610)
        loop.run_until_complete(start_server)

        web.run_app(self, port=1608, host="127.0.0.1", loop=loop)

    async def top(self, dat: dict) -> None:
        self.time, self.dur = dat['data']['progress'], dat['data']['duration']
        self.name = dat['data']['title']
        self.artists = ', '.join(dat['data']['artists'])

    async def set_playlist(self, dat: dict) -> None:
        self.playlist = dat['data']['playlist']

    async def get_time(self) -> int:
        return round(self.time / self.dur * 100)

    @routes.post('/')
    async def test(request: web.Request):
        dat = await request.json()
        await app.top(dat)

    @routes.post('/playlist')
    async def playlist_(request: web.Request):
        dat = await request.json()
        await app.set_playlist(dat)

    @routes.get('/playlist')
    async def get_playlist(request: web.Request):
        return web.Response(body=app.playlist)

    @routes.get('/current')
    async def current(request: web.Request):
        return web.Response(body=f"`{app.name}` by {app.artists}")

    @routes.get('/time')
    async def time(request: web.Request):
        percent = await app.get_time()
        return web.Response(body=str(percent))

    @routes.get('/skip')
    async def skip(request: web.Request):
        await app.socket.send(json.dumps({'type': 'skip'}))
        return web.Response(body='skipped')
    
    @routes.get('/previous')
    async def skip(request: web.Request):
        await app.socket.send(json.dumps({'type': 'previous'}))
        return web.Response(body='previoused')

    @routes.get('/play')
    async def play(request: web.Request):
        await app.socket.send(json.dumps({'type': 'playpause'}))
        return web.Response(body='played')

    @routes.post('/switch')
    async def switch_playlist(request: web.Request):
        resp = await request.text()
        resp = resp.split('=')[1]
        print(resp)
        url = f"https://music.youtube.com/playlist?list={resp}"
        await app.socket.send(json.dumps({'type': 'playlist', 'url': url}))

    @routes.post('/log')
    async def log(request: web.Request):
        print((await request.json())['data']['text'])

app = Server()
app.run()