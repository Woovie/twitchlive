import datetime, discord, json, twitch, configparser
from apscheduler.schedulers.asyncio import AsyncIOScheduler

config = configparser.ConfigParser()
config.read('config.ini')

streamer_objs = []

class DiscordClient(discord.Client):
    async def on_ready(self):
        print(f"Logged in as {self.user}")

async def check_streamer(streamer):
    print(f"Checking {streamer.streamer}")
    streamer_data = await streamer.get_streamer_data()
    if len(streamer_data['data']) > 0:
        print(f"Twitch returned data for {streamer.streamer}")
        now_time   = int(datetime.datetime.now().strftime('%s'))
        start_time = int(datetime.datetime.strptime(streamer_data['data'][0]['started_at'], "%Y-%m-%dT%H:%M:%SZ").strftime('%s'))
        print(f"Now: {now_time}, {streamer.streamer} Started: {start_time}")
        if (now_time-start_time) < 600:
            live_check = await streamer.live_check(streamer_data)
            print(f"{streamer.streamer} started less than 600sec ago, checking if announced")
            if live_check == 'live':
                print(f"First check, announcing for {streamer.streamer}")
                game_data = await twitch.get_game_data_obj(streamer_data)
                embed = discord.Embed(title=f"https://twitch.tv/{streamer.streamer}", color=discord.Color(0x6441a4))
                embed.set_footer(text="bot by Woovie#5555 | https://github.com/woovie")
                embed.set_thumbnail(url="https://assets.help.twitch.tv/Glitch_Purple_RGB.png")
                embed.set_image(url=game_data['art'])
                embed.add_field(name='Title', inline=False, value=streamer_data['data'][0]['title'])
                embed.add_field(name='Category', inline=False, value=game_data['name'])
                channel = discord_client.get_channel(int(streamer.announce_channel))
                await channel.send(content=streamer.message, embed=embed)
            else:
                print(f"Live checker message was: {live_check}")
        else:
            print(f"{streamer.streamer} started greater than 600 sec ago, no further checks.")
    else:
        print(f"No twitch data for {streamer.streamer}")

def main(discord_client):
    streamers = None
    with open('streamers.json', 'r') as f:
        streamers = json.load(f)
    for streamer in streamers:
        if streamer['announce']:
            print(f"Adding {streamer['streamer']}")
            streamer_obj = twitch.Streamer(streamer['streamer'], streamer['speed'], streamer['announce'], streamer['announce_channel'], streamer['message'], discord_client)
            sched.add_job(check_streamer, 'interval', args=[streamer_obj], minutes=streamer_obj.check_freq)
    sched.start()

sched = AsyncIOScheduler()
discord_client = DiscordClient()
main(discord_client)
discord_client.run(config['discord']['token'])
