import aiohttp, configparser, discord, os, json, datetime
from abc import ABC, abstractmethod
from apscheduler.schedulers.asyncio import AsyncIOScheduler

config_path = os.getenv('CONFIG_PATH', 'config.ini')
streamer_path = os.getenv('STREAMER_CONFIG_PATH', 'streamers.json')
config = configparser.ConfigParser()
config.read(config_path)

streamer_api = config['twitch']['streamer_api']
game_api = config['twitch']['game_api']
client_id = config['twitch']['clientid']
headers = {'Client-ID': client_id}


class NotificationState(ABC):
    @abstractmethod
    async def next(self, streamer, live_data):
        pass


class Offline(NotificationState):
    async def next(self, streamer, live_data):
        if live_data is not None:
            return await Pending().next(streamer, live_data)
        return self


class Pending(NotificationState):
    def __init__(self):
        self.observed = datetime.datetime.utcnow()

    async def next(self, streamer, live_data):
        if live_data is None:
            return Offline()

        now = datetime.datetime.utcnow()
        elapsed = (now - self.observed).seconds
        print(f"Elapsed: {elapsed}")
        if elapsed > streamer['delay']:
            return await Announcing().next(streamer, live_data)
        return self


class Announcing(NotificationState):
    @staticmethod
    async def get_game_data(game_id):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{game_api}{game_id}", headers=headers) as r:
                if r.status == 200:
                    game_data = await r.json()
                    return {
                        'name': game_data['data'][0]['name'],
                        'art': game_data['data'][0]['box_art_url'].format(width="170", height="226")
                    }

    @staticmethod
    def build_embed(twitch_name, stream_title, game_name, image_url):
        embed = discord.Embed(title=f"https://twitch.tv/{twitch_name}", color=discord.Color(0x6441a4))
        embed.add_field(name='Title', inline=False, value=stream_title)
        embed.add_field(name='Category', inline=False, value=game_name)
        embed.set_image(url=image_url)
        embed.set_footer(text="bot by Woovie#5555 | https://github.com/woovie/twitchlive")
        embed.set_thumbnail(url="https://assets.help.twitch.tv/Glitch_Purple_RGB.png")
        return embed

    async def next(self, streamer, live_data):
        if live_data is None:
            return Offline()

        game_data = await self.get_game_data(live_data[0]['game_id'])
        embed = self.build_embed(streamer['twitch_name'], live_data[0]['title'], game_data['name'], game_data['art'])
        channel = discord_client.get_channel(int(streamer['announce_channel']))
        await channel.send(content=streamer['message'], embed=embed)
        return await Announced().next(streamer, live_data)


class Announced(NotificationState):
    async def next(self, streamer, live_data):
        if live_data is None:
            return Offline()
        return self


class DiscordClient(discord.Client):
    async def on_ready(self):
        print(f"Logged in as {self.user}")


class Notifier:
    def __init__(self, streamer):
        self.streamer = streamer
        self.state = Offline()
        self.job = None

    def start(self):
        if self.job is None:
            self.job = sched.add_job(self.process_live_check, 'interval', seconds=self.streamer['frequency'])

    def stop(self):
        if self.job is not None:
            self.job.remove()
            self.job = None
            self.state = Offline()

    async def process_live_check(self):
        live_data = await self.is_live()
        current_state = self.state
        self.state = await self.state.next(self.streamer, live_data)

    async def is_live(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{streamer_api}{self.streamer['twitch_name']}", headers=headers) as r:
                if r.status == 200:
                    live_data = await r.json()
                    if len(live_data['data']) > 0:
                        return live_data['data']
                    else:
                        return None
                else:
                    return None


def add_streamer(twitch_username, message, channel):
    if '@here' in message or '@everyone' in message:
        return None
    else:
        if twitch_username in notifiers:
            notifiers[twitch_username].stop()

        streamer = {
            "twitch_name": twitch_username,
            "frequency": 10,
            "delay": 10,
            "active": True,
            "message": message,
            "announce_channel": channel
        }
        with open(streamer_path, 'w') as f:
            streamers = json.load(f)
            streamers.append(streamer)
            f.write(json.dump(streamers))

        to_add = Notifier(streamer)
        notifiers[twitch_username] = to_add
        to_add.start()


def set_announce_channel(server, channel):
    if not server in config:
        config[server] = {}
    config[server]['announce_channel'] = channel
    with open(config_path, 'w') as configfile:
        config.write(configfile)


discord_client = DiscordClient()
sched = AsyncIOScheduler()
notifiers = {}

with open(streamer_path, 'r') as f:
    streamerJson = json.load(f)
    for json in streamerJson:
        notifiers[json['twitch_name']] = Notifier(json)

print(f"Found configurations for streamers: {list(notifiers)}")
for name, notifier in notifiers.items():
    if notifier.streamer['active']:
        print(f"Starting notifier for streamer {name}...")
        notifier.start()

sched.start()
discord_client.run(config['discord']['token'])
