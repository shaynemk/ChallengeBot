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
#TEMPLATE = '{"name": "","start": "","end": "","requirements": {}}'
TEMPLATE = {}
newChallenge = {}
newChallengeTime = ''
newRequirements = {}


#---------------------------------------------
# begin helpers
#---------------------------------------------
def readJSON():
    global CHALLENGES, TEMPLATE
    with open(JSON_CHALLENGES_FILE) as f:
        CHALLENGES = json.load(f)
    with open(JSON_TEMPLATE) as f:
        TEMPLATE = json.load(f)

def writeJSON():
    with open(JSON_CHALLENGES_FILE, 'w') as f:
        json.dump(CHALLENGES, f)

def init_JSON():
    readJSON()
    printAll()

def printAll():
    print(f'Challenges JSON:\n{json.dumps(CHALLENGES, indent=2)}')

def printNew():
    print(f'New Challenge:\n{json.dumps(newChallenge, indent=2)}')

def printNewRequirements():
    print(f'New Requirements:\n{json.dumps(newRequirements, indent=2)}')

def printTemplate():
    print(f'Template JSON:\n{json.dumps(TEMPLATE, indent=2)}')

def list(_id):
    print(CHALLENGES.get(_id))

def challengesAll(ctx):
    content = ''
    content = ', '.join(CHALLENGES.keys())
    ctx.send(content)

def startNewChallenge():
    global newChallenge
    global newChallengeTime
    newChallenge = TEMPLATE.copy()
    newChallengeTime = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()

def saveNewChallenge():
    newChallenge["requirements"] = newRequirements
    CHALLENGES[newChallengeTime] = newChallenge
    writeJSON()
    cancelNew()
    printAll()

def cancelNew():
    newChallenge.clear()
    newRequirements.clear()
    newChallengeTime = ''

def clearChannel(ctx):
    ctx.channel.purge()

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

@bot.command(name='cbanew', help='cba new <name>')
@commands.has_role(RO_CHALLENGER)
async def cbadmin_new(ctx, _name, _startDate, _endDate):
    if ctx.message.author == bot.user:
        return
    startNewChallenge()
    newChallenge['name'] = _name
    newChallenge['start'] = _startDate
    newChallenge['end'] = _endDate
    printNew()
    await ctx.send(f'Drafted new challenge, named "{_name}", running from {_startDate} to {_endDate}.\nUse "{CMD_PREFIX}cbareqadd <name> <number>" to add requirements to the challenge.')

@bot.command(name='cbacancel', help='cba cancel')
@commands.has_role(RO_CHALLENGER)
async def cbadmin_cancel(ctx):
    if ctx.message.author == bot.user:
        return
    cancelNew()
    printNew()

@bot.command(name='cbareqadd', help='cba req add <key> <number>')
@commands.has_role(RO_CHALLENGER)
async def cbadmin_req_add(ctx, _req, _value : int):
    if ctx.message.author == bot.user:
        return
    newRequirements[_req] = _value
    printNewRequirements()
    await ctx.send(f'Added requirement "{_value} {_req}(s)" to \"{newChallenge.get("name")}\". Add more, or use "{CMD_PREFIX}cbasave" to save.')

@bot.command(name='cbareqdel', help='cba req del <key> <number>')
@commands.has_role(RO_CHALLENGER)
async def cbadmin_req_del(ctx, _req, _value : int):
    if ctx.message.author == bot.user:
        return
    newRequirements.pop(_req)
    printNewRequirements()
    await ctx.send(f'Removed requirement "{_req}".')

@bot.command(name='cbasave', help='#asdf')
@commands.has_role(RO_CHALLENGER)
async def cbadmin_save(ctx):
    if ctx.message.author == bot.user:
        return
    if newChallengeTime != '':
        saveNewChallenge()
        printAll()
        await ctx.send(f'Created new challenge (ID: \'{newChallengeTime}\')')
    else:
        print(f'Failed to create')

@bot.command(name='cbaprint', help='cba print <all/new>')
@commands.has_role(RO_CHALLENGER)
async def cbadmin_print(ctx, _json):
    if _json == 'all':
        printAll()
    elif _json == 'new':
        printNew()
    elif _json == 'template':
        printTemplate()

@bot.command(name='cb')
@commands.has_role(RO_CHALLENGED)
async def cb(ctx, *args):
    if ctx.message.author == bot.user:
        return
    if len(args) > 0:
        if args[0] == 'list':
            if len(args) > 1:
                list(args[1])
            else:
                printAll()
        elif args[0] == 'me':
            # respond with user's current status
            print(f'')
        elif args[0] == 'all':
            # respond with how everyone is doing
            print(f'')


init_JSON()
bot.run(DISCORD_TOKEN)
