from twitchio.ext import commands
import twitchio
import aiohttp

import timeago
from datetime import datetime

import pytz

def get_token() -> str:
    with open('./token.txt', 'r') as f:
        return f.read()

server_url: str = "http://127.0.0.1:1608"

class Bot(commands.Bot):

    def __init__(self):
        super().__init__(token=get_token(), prefix='!', initial_channels=['anytarseir67'])
        self.session: aiohttp.ClientSession = None
        self.user: twitchio.User = None

    async def event_ready(self):
        if not self.session:
            self.session = aiohttp.ClientSession()
        if not self.user:
            self.user = await self.get_channel('anytarseir67').user()
        print("Ready")

    @commands.command(aliases=["commands"])
    async def help(self, ctx: commands.Context):
        msg = ' - '.join([f"!{x}" for x in self.commands.keys() if x != "help"]) # why
        await ctx.reply(msg)

    @commands.command()
    async def nowplaying(self, ctx: commands.Context):
        async with self.session.get(f'{server_url}/current') as resp:
            dat = await resp.text()
        if dat == "`None` by None":
            dat = "Unknown"
        async with self.session.get(f'{server_url}/time') as resp:
            time = int(await resp.text())
            # time_str = f"|{'-' * (int(time/10) or 1)}{'_' * (10 - (int(time/10) or 1))}|"
        await ctx.reply(f"{dat} --> {time}%")

    @commands.command()
    async def tab_count(self, ctx: commands.Context):
        async with self.session.get("http://127.0.0.1:8081/count") as resp:
            dat = await resp.json()
        count = dat['ch']
        await ctx.reply(f"`{count}` tabs open in chrome")

    @commands.command()
    async def followage(self, ctx: commands.Context):
        fol = await self.user.fetch_followers()
        print(ctx.author.name)
        for f in fol:
            if f.from_user.id == (await ctx.author.user()).id:
                await ctx.reply(f"You followed {timeago.format(f.followed_at, datetime.now(pytz.UTC))}.")
                break

    @commands.command()
    async def discord(self, ctx: commands.Context):
        await ctx.reply("Join the discord! https://discord.gg/fDQPCBybVJ")
    
    @commands.command()
    async def github(self, ctx: commands.Context):
        await ctx.reply("Check out my github! https://github.com/anytarseir67")

    @commands.command()
    async def playlist(self, ctx: commands.Context):
        async with self.session.get(f"{server_url}/playlist") as resp:
            playlist = await resp.text()
        await ctx.reply(f"https://music.youtube.com/playlist?list={playlist}")

bot = Bot()
bot.run()