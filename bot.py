# bot.py
import os
from dotenv import load_dotenv
import discord
from discord.ext import commands

# load variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
CMD_PREFIX = os.getenv('CMD_PREFIX')


client = discord.Client()

@client.event
async def on_error(event, *args, **kwargs):
    with open('err.log', 'a') as f:
        if event == 'on_message':
            f.write(f'Unhandled message: {args[0]}\n')
        else:
            raise

@client.event
async def on_ready():
    guild = discord.utils.get(client.guilds, name=GUILD)

    print(
        f'{client.user} is connected to the following guild:\n'
        f'{guild.name} (id: {guild.id})'
    )

@client.event
async def on_message(msg):
    if msg.author == client.user:
        return
    
    #other stuff


client.run(TOKEN)