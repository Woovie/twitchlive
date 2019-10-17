import discord, configparser, asyncio, aiohttp, json, datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler

dConfig = configparser.ConfigParser()
dConfig.read('discordconfig.ini')
twitchConfig = configparser.ConfigParser()
twitchConfig.read('twitchconfig.ini')

live = False
debug = True

class discordClient(discord.Client):
    async def on_ready(self):
        print(f"Logged in as {self.user} at { datetime.datetime(2017, 12, 1, 0, 0).strftime('%s')}")

async def checkIfLive():
    global live
    global debug
    global dConfig
    global twitchConfig
    async with aiohttp.ClientSession() as session:
        headers = {'Client-ID': twitchConfig['twitch']['clientid']}
        async with session.get(f"{twitchConfig['twitch']['apiurl']}{twitchConfig['twitch']['streamer']}", headers=headers) as r:
            if r.status == 200:
                twitchStream = await r.json()
    if len(twitchStream['data']) > 0 and live == False:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.twitch.tv/helix/games?id={twitchStream['data'][0]['game_id']}", headers=headers) as r:
                if r.status == 200:
                    twitchGame = await r.json()
        live = True
        embed = discord.Embed(color=discord.Color(0x6441a4), title=f"https://twitch.tv/{twitchConfig['twitch']['streamer']}")
        embed.set_footer(text="bot by Woovie#5555 | https://github.com/woovie")
        embed.set_thumbnail(url="https://assets.help.twitch.tv/Glitch_Purple_RGB.png")
        width = "170"
        height = "226"
        boxart = twitchGame['data'][0]['box_art_url'].format(width=width, height=height)
        embed.set_image(url=boxart)
        embed.add_field(name="Title", inline=False, value=twitchStream['data'][0]['title'])
        embed.add_field(name="Category", inline=False, value=twitchGame['data'][0]['name'])
        await client.get_channel(int(dConfig['discord']['channelid'])).send(embed=embed, content=dConfig['discord']['message'])
        print(f"Went life on { datetime.datetime(2017, 12, 1, 0, 0).strftime('%s')}")
    elif len(twitchStream['data']) == 0 and live == True:
        live = False

sched = AsyncIOScheduler()
sched.add_job(checkIfLive, 'interval', minutes=1)#TODO: Somehow load the `minutes=1` from the twitchconfig. Not sure if I can really do that with Python
sched.start()

client = discordClient()

client.run(dConfig['discord']['token'])
