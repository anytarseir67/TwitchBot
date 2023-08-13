from twitchio.ext import commands, routines
import twitchio
import aiohttp
import timeago
from datetime import datetime
import pytz
import platform
import asyncpg
from typing import Any, Callable

import config

def get_token() -> str:
    with open('./token.txt', 'r') as f:
        return f.read()

server_url: str = "http://127.0.0.1:1608"

class ModCommand(commands.Command):
    def __init__(self, name: str, func: Callable[..., Any], **attrs) -> None:
        super().__init__(name, func, **attrs)
        self.__skip__ = True

class Playlist:
    def __init__(self, id: str, name: str) -> None:
        self.id = id
        self.name = name

class Bot(commands.Bot):

    def __init__(self) -> None:
        super().__init__(token=get_token(), prefix='!', initial_channels=[config.channel])
        self.session: aiohttp.ClientSession = None
        self.user: twitchio.User = None
        self.conn: asyncpg.connection.Connection = None
        self.live: bool = False
        self.update_live.start()
        self.send_help.start()

    @routines.routine(minutes=1)
    async def update_live(self) -> None:
        resp = await self.search_channels(config.channel)
        for user in resp:
            if user.name == config.channel:
                if not self.live and user.live:
                    self.update_live.change_interval(seconds=30)
                elif self.live and not user.live:
                    self.update_live.change_interval(minutes=1)

                self.live = user.live
                return
        self.live = False

    @update_live.before_routine
    async def before_update_live(self) -> None:
        await self.wait_for_ready()

    @routines.routine(minutes=10, wait_first=True)
    async def send_help(self) -> None:
        if self.live:
            msg = ' - '.join([f"!{x}" for x in self.commands.keys() if (x != "help") or (not hasattr(x, '__skip__'))])
            await self.user.channel.send(msg)

    @send_help.before_routine
    async def before_send_help(self) -> None:
        await self.wait_for_ready()

    async def handle_commands(self, message: twitchio.Message):
        if self.live or message.author.name == config.channel:
            return await super().handle_commands(message)

    async def event_ready(self) -> None:
        if not self.conn:
            self.conn = await asyncpg.connect(**config.pg_config)
        if not self.session:
            self.session = aiohttp.ClientSession()
        if not self.user:
            self.user = await self.get_channel(config.channel).user()
        print("Ready")

    @commands.command(aliases=["commands"])
    async def help(self, ctx: commands.Context) -> None:
        msg = ' - '.join([f"!{x.name}" for x in self.commands.values() if x.name != "help" and not hasattr(x, '__skip__')])
        await ctx.reply(msg)

    @commands.command()
    async def nowplaying(self, ctx: commands.Context) -> None:
        async with self.session.get(f'{server_url}/current') as resp:
            dat = await resp.text()
        if dat == "`None` by None":
            dat = "Unknown"
        async with self.session.get(f'{server_url}/time') as resp:
            time = int(await resp.text())
        await ctx.reply(f"{dat} --> {time}%")

    @commands.command()
    async def tab_count(self, ctx: commands.Context) -> None:
        async with self.session.get("http://127.0.0.1:8081/count") as resp:
            dat = await resp.json()
        count = dat['ch']
        await ctx.reply(f"`{count}` tabs open in chrome")

    @commands.command()
    async def followage(self, ctx: commands.Context) -> None:
        fol = await self.user.fetch_followers()
        for f in fol:
            if f.from_user.id == (await ctx.author.user()).id:
                await ctx.reply(f"You followed {timeago.format(f.followed_at, datetime.now(pytz.UTC))}.")
                break

    @commands.command()
    async def discord(self, ctx: commands.Context) -> None:
        await ctx.reply("Join the discord! https://discord.gg/fDQPCBybVJ")
    
    @commands.command()
    async def github(self, ctx: commands.Context) -> None:
        await ctx.reply("Check out my github! https://github.com/anytarseir67")

    @commands.command()
    async def playlist(self, ctx: commands.Context) -> None:
        async with self.session.get(f"{server_url}/playlist") as resp:
            playlist = await resp.text()
        await ctx.reply(f"https://music.youtube.com/playlist?list={playlist}")

    @commands.command()
    async def source(self, ctx: commands.Context) -> None:
        await ctx.reply("You can find my source here: https://github.com/anytarseir67/TwitchBot")
    
    @commands.command()
    async def about(self, ctx: commands.Context) -> None:
        ver = platform.python_version()
        await ctx.reply(f"python: {ver}, twitchio: {twitchio.__version__}")

    @commands.command()
    async def skip(self, ctx: commands.Context) -> None:
        async with self.session.get(f"{server_url}/skip") as _:
            ... # do nothing since we don't actually need the response
        await ctx.reply("Skipped.")

    @commands.command()
    async def previous(self, ctx: commands.Context) -> None:
        async with self.session.get(f"{server_url}/previous") as _:
            ... # do nothing since we don't actually need the response
        await ctx.reply("playing previous song.")

    @commands.command()
    async def cough(self, ctx: commands.Context) -> None:
        dat = await self.conn.fetch("SELECT value FROM data WHERE name ='cough'")
        coughs = int(dat[0]['value']) + 1
        await ctx.reply(f"{config.channel} has coughed {coughs} times.")
        await self.conn.execute(f"UPDATE data SET value=$1 WHERE name=$2", str(coughs), "cough")
        
    async def set_playlist(self, id: str) -> None:
        json = {'id': id}
        try:
            async with self.session.post(f"{server_url}/switch", data=json) as resp:
                ...
        except:
            pass

    @commands.command()
    async def playlist(self, ctx: commands.Context, name: str=None) -> None:
        msg = ""

        lists = {
            'banime': Playlist('PL90pfRlPsZRMKf1wr27WZ0v_fw-Tf4VAk', 'Banime'),
            'demondice': Playlist('PL90pfRlPsZRNehjeYnQCRqGlNWRtnL5Ce', 'DemonDice'),
            'rats': Playlist('PL90pfRlPsZROTixdxzfxzgEd78LefK3GS', 'Rats'),
            'goodstuff': Playlist('PL90pfRlPsZRN8gGgQaUUP0mPTLlVETEki', 'The Good Stuff')
        }

        names = {
            'banime': 'Banime',
            'demondice': 'DemonDice',
            'rats': 'Rats'
        }

        # why do i do this to myself o_o 

        if not name:
            async with self.session.get(f"{server_url}/playlist") as resp:
                playlist = await resp.text()
            msg = f"https://music.youtube.com/playlist?list={playlist}"
        if pl := lists.get(name.lower()):
            await self.set_playlist(pl.id)
            msg = f'Switched to the "{pl.name}" playlist.'
        else: return

        await ctx.reply(msg)

    @commands.command()
    async def play(self, ctx: commands.Context) -> None:
        async with self.session.get(f"{server_url}/play") as resp:
            ...
        await ctx.reply("toggled the playing state!")

    @commands.command()
    async def raid(self, ctx: commands.Context) -> None:
        dat = await self.conn.fetch("SELECT value FROM data WHERE name ='raid'")
        msg = dat[0]['value']
        await ctx.reply(msg)

    @commands.command(cls=ModCommand)
    async def setraid(self, ctx: commands.Context, *, msg : str) -> None:
        if ctx.author.is_mod:
            await self.conn.execute(f"UPDATE data SET value=$1 WHERE name='raid'", msg)
            await ctx.reply(f"Set raid message to: {msg}")

    @commands.command(name="7tv")
    async def _7tv(self, ctx: commands.Context) -> None:
        site = "https://7tv.app/"
        set_url = "https://7tv.app/emote-sets/64b386e495725c174ecd782b"
        await ctx.reply(f"7tv is an emote extension for twitch, you can get it here: {site} and you can find our emote set here: {set_url}")

    @commands.command(name="project")
    async def project(self, ctx: commands.Context) -> None:
        dat = await self.conn.fetch("SELECT value FROM data WHERE name=$1", 'project')
        await ctx.reply(dat[0]['value'])

    @commands.command()
    async def set_project(self, ctx: commands.Context, *, msg: str) -> None:
        if ctx.author.is_mod:
            await self.conn.execute("UPDATE data SET value=$1 WHERE name=$2", msg, 'project')



bot = Bot()
bot.run()