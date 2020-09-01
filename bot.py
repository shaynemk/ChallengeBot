# bot.py
import os
from dotenv import load_dotenv
import discord
from discord.ext import commands

# load variables
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
CMD_PREFIX = os.getenv('CMD_PREFIX')
#GUILD = os.getenv('DISCORD_GUILD')

#client = discord.Client()

#@client.event
#async def on_error(event, *args, **kwargs):
#    with open('err.log', 'a') as f:
#        if event == 'on_message':
#            f.write(f'Unhandled message: {args[0]}\n')
#       else:
#            raise

#@client.event
#async def on_ready():
#    guild = discord.utils.get(client.guilds, name=GUILD)
#
#    print(
#        f'{client.user} is connected to the following guild:\n'
#        f'{guild.name} (id: {guild.id})'
#    )

#@client.event
#async def on_message(msg):
#    if msg.author == client.user:
#        return
#    
#    if msg.content == "!@#raise-exception":
#        raise discord.DiscordException
#    
#    #other stuff

#client.run(TOKEN)

bot = commands.Bot(command_prefix=CMD_PREFIX)

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')

bot.run(DISCORD_TOKEN)