# bot.py

# TODO:
# || now ||
# - enable users to join/leave challenges
# - join challenges with (user).id but display (user).nick
#
# || soonish ||
# - draft up leaderboard channel management
# - consolidate cba* commands into singular 'cba'
#
# || later/maybe ||
# - allow picture uploads
# - allow users to participate in multiple challenges at once
# - remove assumptions that we only have one challenge running at once
# - add in some randomized congratulatory responses after updating challenge states


import os, json, discord, datetime
from dotenv import load_dotenv
from discord.ext import commands

# load variables from '.env' file
load_dotenv()
DEBUG = os.getenv('DEBUG')
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

def debug(_msg):
    if DEBUG:
        print('[DEBUG]: ',_msg)

def printAll():
    debug(f'Challenges JSON:\n{json.dumps(CHALLENGES, indent=2)}')

def printNew():
    debug(f'New Challenge:\n{json.dumps(newChallenge, indent=2)}')

def printNewRequirements():
    debug(f'New Requirements:\n{json.dumps(newRequirements, indent=2)}')

def printTemplate():
    debug(f'Template JSON:\n{json.dumps(TEMPLATE, indent=2)}')

def list(_id):
    debug(CHALLENGES.get(_id))
    return CHALLENGES.get(_id)

def getAllChallenges():
    challengesMsg = ''
    for _key in CHALLENGES:
        if challengesMsg != '':
            challengesMsg = f'{challengesMsg}\n\"{CHALLENGES[_key].get("name")}\" (ID: {_key})'
        else:
            challengesMsg = f'\"{CHALLENGES[_key].get("name")}\" (ID: {_key})'
    debug(f'Found these challenges: {challengesMsg}')
    return challengesMsg

# update user's progress as requested
def update(_user, _args):
    global CHALLENGES
    # 3 possible update states:
    # user is smart: in active challenge, and is correct
    # user didnt include both k,v entries for the update
    # user isnt listed as participating in any challenge
    if len(_args) >= 3:
        _id = getParticipating(_user)
        _req = _args[1]
        _val = _args[2]
        if not _id == 'none': # make sure the user is participating in a challenge
            checkForCurrentEntry(_id,_user)
            CHALLENGES[_id]['participants'][_user][_req] = _val
            msg = f'Updated {getUserNameFromID(_user)}\'s participation in {CHALLENGES[_id]["name"]}\'s required {CHALLENGES[_id]["requirements"][_req]} {_req}(s) to {_val}.'
        else:
            msg = f'It appears that you aren\'t participating in any active challenges. Try joining one by using \'cb join <id>\''
    elif len(_args) < 3:
        msg = f'Not enough information. Try \'cb update <requirement> <value>\''        
    return msg

def currentEntryExists(_id,_user):
    if CHALLENGES[_id]['resetCycle'] == 'daily':
        currCycle = getDayToday()
        for _entry in CHALLENGES[_id]['participants'][_user].keys():
            if _entry.startswith(currCycle):
                return True
        return False
    else:
        # TODO: implement other challenges (hourly/weekly/monthly/etc)
        print(f'')

def checkForCurrentEntry(_id,_user):
    if not currentEntryExists(_id,_user):
        global CHALLENGES
        CHALLENGES[_id]['participants'][_user][getNowTime()].fromkeys(CHALLENGES[_id]['requirements'],0)

def activateChallenge(_id, _active):
    global CHALLENGES
    CHALLENGES[_id]['active'] = _active
    return f'Challenge \"{CHALLENGES[_id]["name"]}\" is now {"active" if _active else "not active"}'

# get the first challenge user is participating in
def getParticipating(_user):
    for id,chall in CHALLENGES.items():
        if chall["active"] and _user in chall["participants"].keys():
            return id
    return 'none'

# get all challenges user is participating in
def getAllParticipating(_user):
    participatingIn = []
    for id,chall in CHALLENGES.items():
        if chall["active"] and _user in chall["participants"].keys():
            participatingIn.append(id)
    return participatingIn

def joinChallenge(_user,_id):
    if not getParticipating(_user) == 'none':
        global CHALLENGES
        CHALLENGES[_id]['participating'].append(_user)

def getUserNameFromID(_id):
    return bot.get_user(_id)

def getNowTime():
    return datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).strftime("%Y%m%d%H%M%S%f")

def getDayToday():
    return datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).strftime("%Y%m%d")

def startNewChallenge():
    global newChallenge
    global newChallengeTime
    newChallenge = TEMPLATE.copy()
    newChallengeTime = getNowTime()

def saveNewChallenge():
    global newChallenge, newRequirements, CHALLENGES
    newChallenge["requirements"] = newRequirements
    CHALLENGES[newChallengeTime] = newChallenge
    writeJSON()
    cancelNew()
    printAll()

def cancelNew():
    global newChallenge, newRequirements, newChallengeTime
    newChallenge.clear()
    newRequirements.clear()
    newChallengeTime = ''

def removeChallenge(_id):
    global CHALLENGES
    _value = CHALLENGES.pop(_id,-1)
    writeJSON()
    printAll()
    return _value

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

@bot.command(name='cbadelete', help='cbadelete <id>')
@commands.has_role(RO_CHALLENGER)
async def cbadmin_delete(ctx, _id=-1):
    debug('entering <cbadelete>')
    if ctx.message.author == bot.user:
        debug('message author is the bot')
        return
    if _id != -1:
        debug('<cbadelete> _id is not default (-1), continuing.')
        _return = removeChallenge(_id)
        printAll()
        if _return != -1:
            msg = f'Deleted challenge \"{CHALLENGES[_id].get("name")}\" (ID: \'{_id}\')'
        else:
            msg = f'Challenge not found. Name: \"{CHALLENGES[_id].get("name")}\" (ID: {_id})'
    else:
        debug('<cbadelete> _id is default, can\'t continue deleting.')
        msg = f'Can\' delete a challenge without knowing the ID of it...'
    await ctx.send(msg)

@bot.command(name='cbaprint', help='cba print <all/new>: Printing stuff to the console.')
@commands.has_role(RO_CHALLENGER)
async def cbadmin_print(ctx, _json):
    if _json == 'all':
        printAll()
    elif _json == 'new':
        printNew()
    elif _json == 'template':
        printTemplate()

@bot.command(name='cbaactive', help='cbaactive <id> (<true>/<false>) - set challenge as active or not')
@commands.has_role(RO_CHALLENGER)
async def cbadmin_activate(ctx, _id: int, _active: bool):
    if ctx.message.author == bot.user:
        return
    msg = activateChallenge(_id,_active)
    await ctx.send(msg)

@bot.command(name='cb', help='cb - show current challenge(s).\ncb join <id> - join challenge corresponding to <id>.\ncb update <requirement> <update> - Update your challenge status on <requirement> with <update>.')
async def cb(ctx, *args):
    if ctx.message.author == bot.user:
        return
    if len(args) > 0:
        if args[0] == 'me' or args[0] == 'all':
            # respond with user's current status
            msg = list(args[0])
        elif args[0] == 'join':
            if (not ctx.message.author.has_role(RO_CHALLENGED) or getParticipating(ctx.message.author.id) == 'none') and len(args) >= 2:
                joinChallenge(ctx.message.author.id, args[1])
        elif args[0] == 'update':
            if ctx.message.author.has_role(RO_CHALLENGED):
                # user has role, now check for challenges and update
                msg = update(ctx.message.author.id, args)
            else: # user does not have the role
                msg = f'You don\'t appear to have the appropriate role ({RO_CHALLENGED}). Join a challenge via \"({CMD_PREFIX}cb join <id>\" to join a challenge or have someone give you the role.'
        else: # command not understood
            msg = 'I didn\' understand that command.'
    else: # no command given, default to showing all challenges
        msg = f'These are the challenges I\'m tracking:\n{getAllChallenges()}'
    await ctx.send(msg)

init_JSON()
bot.run(DISCORD_TOKEN)
