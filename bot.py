from twitchio.ext import commands, routines
import twitchio
import aiohttp
import timeago
from datetime import datetime
import pytz
import platform
import asyncpg

import config

def get_token() -> str:
    with open('./token.txt', 'r') as f:
        return f.read()

server_url: str = "http://127.0.0.1:1608"

class Bot(commands.Bot):

    def __init__(self) -> None:
        super().__init__(token=get_token(), prefix='!', initial_channels=[config.channel])
        self.session: aiohttp.ClientSession = None
        self.user: twitchio.User = None
        self.conn: asyncpg.connection.Connection = None
        self.live: bool = False
        self.update_live.start()

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
        msg = ' - '.join([f"!{x}" for x in self.commands.keys() if x != "help"])
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
    async def cough(self, ctx: commands.Context) -> None:
        dat = await self.conn.fetch("SELECT value FROM data WHERE name ='cough'")
        coughs = int(dat[0]['value']) + 1
        await ctx.reply(f"{config.channel} has coughed {coughs} times.")
        await self.conn.execute(f"UPDATE data SET value=$1 WHERE name=$2", str(coughs), "cough")
        

bot = Bot()
bot.run()