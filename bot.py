# bot.py
import os, json, discord, datetime
from dotenv import load_dotenv
from discord.ext import commands

# load variables from '.env' file
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
CMD_PREFIX = os.getenv('CMD_PREFIX')
CH_CHALLENGE = os.getenv('CH_CHALLENGE')
CH_GENERAL = os.getenv('CH_GENERAL')
RO_CHALLENGED = os.getenv('RO_CHALLENGED')
RO_CHALLENGER = os.getenv('RO_CHALLENGER')

# init other variables
HELP_ADMIN_NEW = 'cbadmin new <name> <startdate> <enddate>'
HELP_CB = 'Use this command to document your challenge progress (requires Challenged role)'
JSON_CHALLENGES_FILE = 'challenges.json'
JSON_TEMPLATE = 'template.json'
CHALLENGES = {}
TEMPLATE = {}
newChallenge = {}


#---------------------------------------------
# begin helpers
#---------------------------------------------
def readJSON():
    with open(JSON_CHALLENGES_FILE) as f:
        CHALLENGES = json.load(f)
    with open(JSON_TEMPLATE) as f:
        TEMPLATE = json.load(f)

def writeJSON():
    with open(JSON_CHALLENGES_FILE, 'w') as f:
        json.dump(CHALLENGES, f)

def init_JSON():
    readJSON()
    print(json.dumps(CHALLENGES, indent=2))

def startNewChallenge():
    newChallenge = TEMPLATE.copy()

def createNewChallenge():
    newChallengeTime = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()
    CHALLENGES[newChallengeTime] = newChallenge


#---------------------------------------------
# begin bot specifics
#---------------------------------------------
bot = commands.Bot(command_prefix=CMD_PREFIX)

@bot.event
async def on_error(event, *args, **kwargs):
    with open('err.log', 'a') as f:
        if event == 'on_message':
            f.write(f'Unhandled message: {args[0]}\n')
        else:
            raise

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send('You do not have the correct role for this command.')

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

@bot.command(name='cbadmin new', help=HELP_ADMIN_NEW)
@commands.has_role(RO_CHALLENGER)
async def cbadmin_new(ctx, _name, _startDate, _endDate):
    if ctx.message.author == bot.user:
        return
    startNewChallenge()
    newChallenge['name'] = _name
    newChallenge['start'] = _startDate
    newChallenge['end'] = _endDate

@bot.command(name='cbadmin start', help='start date')
@commands.has_role(RO_CHALLENGER)
async def cbadmin_start(ctx, _startDate):
    if ctx.message.author == bot.user:
        return
    newChallenge['start'] = _startDate

@bot.command(name='cbadmin end', help='end date')
@commands.has_role(RO_CHALLENGER)
async def cbadmin_end(ctx, _endDate):
    if ctx.message.author == bot.user:
        return
    newChallenge['end'] = _endDate

@bot.command(name='cbadmin req add', help='cbadmin req add <key> <number>')
@commands.has_role(RO_CHALLENGER)
async def cbadmin_req_add(ctx, _key, _value : int):
    if ctx.message.author == bot.user:
        return
    newChallenge['requirements'][_key] = _value

@bot.command(name='cbadmin req del', help='cbadmin req del <key> <number>')
@commands.has_role(RO_CHALLENGER)
async def cbadmin_req_del(ctx, _key, _value : int):
    if ctx.message.author == bot.user:
        return
    newChallenge['requirements'][_key].pop

@bot.command(name='cbadmin create', help='#asdf')
@commands.has_role(RO_CHALLENGER)
async def cbadmin_create(ctx):
    if ctx.message.author == bot.user:
        return
    createNewChallenge()


@bot.command(name='cb')
@commands.has_role(RO_CHALLENGED)
async def cb(ctx):
    if ctx.message.author == bot.user:
        return


init_JSON()
bot.run(DISCORD_TOKEN)