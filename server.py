from aiohttp import web
import websockets
from websockets import server
import asyncio

app = web.Application()

routes = web.RouteTableDef()

class Data:
    def __init__(self) -> None:
        self.name: str = None
        self.artists: str = None
        self.time: int = None
        self.dur: int = None
        self.playlist: str = None
        self.socket: server.WebSocketServerProtocol = None

    async def top(self, dat: dict) -> None:
        self.time, self.dur = dat['data']['progress'], dat['data']['duration']
        self.name = dat['data']['title']
        self.artists = ', '.join(dat['data']['artists'])

    async def set_playlist(self, dat: dict) -> None:
        self.playlist = dat['data']['playlist']

    async def get_time(self) -> int:
        return round(self.time / self.dur * 100)

data = Data()

@routes.post('/')
async def test(request: web.Request):
    dat = await request.json()
    await data.top(dat)

@routes.post('/playlist')
async def playlist_(request: web.Request):
    dat = await request.json()
    await data.set_playlist(dat)

@routes.get('/playlist')
async def get_playlist(request: web.Request):
    return web.Response(body=data.playlist)

@routes.get('/current')
async def current(request: web.Request):
    return web.Response(body=f"`{data.name}` by {data.artists}")

@routes.get('/time')
async def time(request: web.Request):
    percent = await data.get_time()
    return web.Response(body=str(percent))

@routes.get('/skip')
async def skip(request: web.Request):
    await data.socket.send('skip')
    return web.Response(body='skipped')

async def socket(websocket: server.WebSocketServerProtocol, path) -> None:
    data.socket = websocket
    async for msg in websocket:
        ...

app.add_routes(routes)
start_server = server.serve(socket, 'localhost', 1610)
asyncio.get_event_loop().run_until_complete(start_server)
web.run_app(app, port=1608, host="127.0.0.1", loop=asyncio.get_event_loop())