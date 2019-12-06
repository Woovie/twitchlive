import aiohttp, configparser

config = configparser.ConfigParser()
config.read('config.ini')

streamer_api = config['twitch']['streamer_api']
game_api     = config['twitch']['game_api']
client_id    = config['twitch']['clientid']
headers      = {'Client-ID': client_id}

class Streamer():
    def __init__(self, streamer, speed, announce, announce_channel, message, discord_client):
        self.streamer = streamer
        self.check_freq = speed
        self.announce = announce
        self.announce_channel = announce_channel
        self.message = message
        self.discord = discord_client
        self.check_ticks = 0
        self.live = False
        self.announced = False
    async def get_live_data(self):
        streamer_data = await get_streamer_data(self.streamer)
        if len(streamer_data['data']) > 0:
            return streamer_data
        else:
            return None

    async def live_check(self, live_data):
        if self.check_ticks > 5 or self.check_ticks == 0:
            if live_data and self.live:
                self.check_ticks = 1
                return 'still live, reset ticks'
            elif live_data and not self.live:
                self.check_ticks = 1
                self.live = True
                return 'live'
            elif not live_data and self.live:
                self.check_ticks = 0
                self.live = False
                self.announced = False
                return 'not live'
        elif self.check_ticks < 6 and self.check_ticks > 0:
            self.check_ticks += 1
            return 'ticked'
    async def get_streamer_data(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{streamer_api}{self.streamer}", headers=headers) as r:
                if r.status == 200:
                    return await r.json()
                else:
                    return None

async def get_game_data(game_id):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{game_api}{game_id}", headers=headers) as r:
            if r.status == 200:
                return await r.json()
            else:
                return None
async def get_game_data_obj(streamer_data):
    game_id   = streamer_data['data'][0]['game_id']
    game_data = await get_game_data(game_id)
    width = "170"
    height = "226"
    return {
        'name': game_data['data'][0]['name'],
        'art': game_data['data'][0]['box_art_url'].format(width=width, height=height)
    }
