import aiohttp, configparser, discord, os, json, datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler

config_path = os.getenv('CONFIG_PATH', 'config.ini')
streamer_path = os.getenv('STREAMER_CONFIG_PATH', 'streamers.json')
config = configparser.ConfigParser()
config.read(config_path)

streamer_api = config['twitch']['streamer_api']
game_api     = config['twitch']['game_api']
client_id    = config['twitch']['clientid']
headers      = {'Client-ID': client_id}

class DiscordClient(discord.Client):
    async def on_ready(self):
        print(f"Logged in as {self.user}")

class Streamer():
    def __init__(self, streamer, frequency, message, channel):
        self.streamer = streamer
        self.went_live = 0
        self.live_last_tick = False
        self.message = message
        self.channel = channel
        self.job = sched.add_job(self.process_live_check, 'interval', seconds=10)#TESTING
        self.embed = discord.Embed(title=f"https://twitch.tv/{self.streamer}", color=discord.Color(0x6441a4))
        self.embed.set_footer(text="bot by Woovie#5555 | https://github.com/woovie/twitchlive")
        self.embed.set_thumbnail(url="https://assets.help.twitch.tv/Glitch_Purple_RGB.png")
    async def process_live_check(self):
        if (live_data := await self.is_live()) is not None:
            if not self.live_last_tick:
                now = int(datetime.datetime.now().strftime('%s'))
                if now - self.went_live > 600:
                    self.went_live = int(datetime.datetime.strptime(live_data[0]['started_at'], "%Y-%m-%dT%H:%M:%SZ").strftime('%s'))
                    self.live_last_tick = True
                    game_data = await self.get_game_data(live_data[0]['game_id'])
                    self.embed.add_field(name='Title', inline=False, value=live_data[0]['title'])
                    self.embed.add_field(name='Category', inline=False, value=game_data['name'])
                    self.embed.set_image(url=game_data['art'])
                    channel = discord_client.get_channel(int(self.channel))
                    await channel.send(content=self.message, embed=self.embed)
                    self.embed.clear_fields()
                else:
                    self.live_last_tick = True
            else:
                self.live_last_tick = True
        else:
            self.live_last_tick = False
    async def is_live(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{streamer_api}{self.streamer}", headers=headers) as r:
                if r.status == 200:
                    live_data = await r.json()
                    if len(live_data['data']) > 0:
                       return live_data['data']
                    else:
                        return None
                else:
                    return None
    async def get_game_data(self, game_id):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{game_api}{game_id}", headers=headers) as r:
                if r.status == 200:
                    game_data = await r.json()
                    return {
                        'name': game_data['data'][0]['name'],
                        'art': game_data['data'][0]['box_art_url'].format(width="170", height="226")
                    }

def add_streamer(twitch_username, message, channel):
    if '@here' in message or '@everyone' in message:
        return None
    else:
        sched.pause()
        streamer = {
            "twitch_name": twitch_username,
            "frequency": 5,
            "active": True,
            "message": message,
            "announce_channel": channel
        }
        Streamer(streamer['twitch_name'], streamer['frequency'], streamer['message'], streamer['announce_channel'])
        with open(streamer_path, 'w') as f:
            streamers = json.load(f)
            streamers.append(streamer)
            f.write(json.dump(streamers))

def set_announce_channel(server, channel):
    if not server in config:
        config[server] = {}
    config[server]['announce_channel'] = channel
    with open(config_path, 'w') as configfile:
        config.write(configfile)

discord_client = DiscordClient()
sched = AsyncIOScheduler()
with open(streamer_path, 'r') as f:
    streamers = json.load(f)
    for streamer in streamers:
        print(f"Reading streamer{streamer['twitch_name']}...")
        if streamer['active']:
                print(f"Adding streamer {streamer['twitch_name']}")
                streamer_obj = Streamer(streamer['twitch_name'], streamer['frequency'], streamer['message'], streamer['announce_channel'])
sched.start()
discord_client.run(config['discord']['token'])