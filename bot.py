# bot.py

# TODO:
# || now ||
# - fix date management/displays for challenges
#
# || soonish ||
# - draft up leaderboard channel management
# - consolidate cba* commands into singular 'cba'
# - figure out how to fix the help documentation
#
# || later/maybe ||
# - add timezone spec and auto conversion to user inside of challenges/participants. but how to persist across challenges?
# - allow picture uploads
# - allow users to participate in multiple challenges at once
# - remove assumptions that we only have one challenge running at once
# - add in some randomized congratulatory responses after updating challenge states


import os, json, discord, datetime, logging
from dotenv import load_dotenv
from discord.ext import commands

# load variables from '.env' file
load_dotenv()
DEBUG = os.getenv('DEBUG')
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
CMD_PREFIX = os.getenv('CMD_PREFIX')
CH_LEADERBOARD = os.getenv('CH_LEADERBOARD')
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

DATEUTC = "%Y%m%d%H%M%S%f"
DATEDMON = "%d %b"


#---------------------------------------------
# begin helpers
#---------------------------------------------
def readJSON():
    global CHALLENGES, TEMPLATE
    with open(JSON_CHALLENGES_FILE) as f:
        CHALLENGES = json.load(f)
    f.close()
    with open(JSON_TEMPLATE) as f:
        TEMPLATE = json.load(f)
    f.close()

def writeJSON():
    global CHALLENGES
    with open(JSON_CHALLENGES_FILE, 'w') as f:
        json.dump(CHALLENGES, f)
    f.close()

def initJSON():
    readJSON()
    printAll()

def initLogging():
    logger = logging.getLogger('discord')
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler(filename='challengebot.log', encoding='utf-8', mode='w')
    handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
    logger.addHandler(handler)

def debug(_msg):
    if DEBUG:
        print('[DEBUG]: ',_msg)

def printAll():
    #debug(f'Challenges JSON:\n{json.dumps(CHALLENGES, indent=2)}')
    print(f'{json.dumps(CHALLENGES,indent=2)}')

def printNew():
    debug(f'New Challenge:\n{json.dumps(newChallenge, indent=2)}')

def printNewRequirements():
    debug(f'New Requirements:\n{json.dumps(newRequirements, indent=2)}')

def printTemplate():
    debug(f'Template JSON:\n{json.dumps(TEMPLATE, indent=2)}')

def listChallengeUser(_user):
    _id = getParticipating(_user)
    if not _id is None:
        msg = f'Challenge: {CHALLENGES[_id]["name"]} (ID: {_id})'
        if len(CHALLENGES[_id]["participants"][str(_user)].keys()) > 0:
            for _cycle,_reqs in CHALLENGES[_id]["participants"][str(_user)].items():
                msg += f'\n{dateStrReformat(_cycle,DATEDMON)}: ('
                for _item in _reqs.keys():
                    msg += f'{_item}: {_reqs[_item]}, '
        else:
            msg += f'\nNo updates yet. Use \'{CMD_PREFIX}cb update <requirement> <value>\'.'
    else:
        msg = f'Error in listing user\'s challenges.'
    if msg[-2:] == ', ': # remove any trailing commas and spaces, and close the parenthesis
        msg = msg[:-2] + ')'
    debug(f'Current status for {_user}:\nmsg')
    return msg

def listChallenge(_id):
    debug(f'starting listChallenge({_id})')
    _chall = CHALLENGES[_id]
    msg = f'__**{_chall["name"]}**__'
    msg += f'\nStarting: {dateStrReformat(_chall["start"],DATEDMON)}'
    msg += f'\nEnding: {dateStrReformat(_chall["end"],DATEDMON)}'
    msg += f'\nActive: {_chall["active"]}'
    msg += f'\nReset Cycle: {_chall["resetCycle"]}'
    msg += f'\n\n__Requirements:__'
    if len(_chall['requirements'].keys()) > 0:
        for _req in _chall['requirements'].keys():
            msg += f'\n{_req}: {_chall["requirements"][_req]}'
    else:
        msg += f'\nNo Requirements'
    msg += '\n\n__Participants:__'
    if len(_chall['participants'].keys()) > 0:
        debug(f'<listChallenge({_id})> _chall[\'participants\'].keys(): {_chall["participants"].keys()}')
        for _participant in _chall['participants'].keys():
            debug(f'<listChallenge({_id})> _participant: {_participant} [{type(_participant)}]')
            msg += f'\n{getUserNameFromID(_participant)}'
    else:
        msg += f'\nNo participants'
    debug(f'{msg}')
    return msg

def getAllChallenges():
    challengesMsg = ''
    for _key in CHALLENGES:
        if challengesMsg != '':
            challengesMsg = f'{challengesMsg}\n\"{CHALLENGES[_key]["name"]}\" (ID: {_key})'
        else:
            challengesMsg = f'\"{CHALLENGES[_key]["name"]}\" (ID: {_key})'
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
        if isParticipating(_user): # make sure the user is participating in a challenge
            checkForCurrentEntry(_id,_user)
            CHALLENGES[_id]['participants'][str(_user)][getCurrentEntry(_id,_user)][_req] = int(_val)
            writeJSON()
            msg = f'Updated {getUserNameFromID(_user)}\'s participation in \"{CHALLENGES[_id]["name"]}\"s required {CHALLENGES[_id]["requirements"][_req]} {_req}(s) to {_val}.'
        else:
            msg = f'It appears that you aren\'t participating in any active challenges. Try joining one by using \'cb join <id>\''
    elif len(_args) < 3:
        msg = f'Not enough information. Try \'cb update <requirement> <value>\''        
    return msg

def getCurrentEntry(_id,_user):
    if CHALLENGES[_id]['resetCycle'] == 'daily':
        currCycle = getDayToday()
        for _entry in CHALLENGES[_id]['participants'][str(_user)].keys():
            if _entry.startswith(currCycle):
                return _entry
        return None
    else:
        # TODO: implement other cycles (hourly/weekly/monthly/etc)
        print(f'')

def checkForCurrentEntry(_id,_user):
    if not getCurrentEntry(_id,_user):
        global CHALLENGES
        CHALLENGES[_id]['participants'][str(_user)][getNowTime()] = {}.fromkeys(CHALLENGES[_id]['requirements'].keys(),0)
        writeJSON() #probably redundant because we only get called from update() which after updating, saves.

def activateChallenge(_id, _active):
    debug(f'<activateChallenge> setting {_id} activation to {_active}.')
    global CHALLENGES
    CHALLENGES[_id].update(['active',_active])
    debug(f'<activateChallenge> post setting: {CHALLENGES[_id]["active"]}')
    writeJSON()
    debug(f'<activateChallenge> post save: {CHALLENGES[_id]["active"]}')
    return f'Challenge \"{CHALLENGES[_id]["name"]}\" is now {"active" if _active else "not active"}'

# get the first challenge user is participating in
def getParticipating(_user):
    debug(f'<getParticipating({_user})> entered')
    for _id,_chall in CHALLENGES.items():
        debug(f'<getParticipating({_user})> (_id: {_id}, _chall[\"active\"]: {_chall["active"]}, _chall[\"participants\"].keys(): {_chall["participants"].keys()})')
        if _chall["active"] == 1 and str(_user) in _chall["participants"].keys():
            debug(f'<getParticipating({_user})> _user is participating in this challenge.')
            return _id
        debug(f'<getParticipating({_user})> found no challenges the user is participating in.')
    return 'none'

# is the user participating in any challenge
def isParticipating(_user):
    debug(f'<isParticipating({_user})> entered; _user: {type(_user)}')
    for _id,_chall in CHALLENGES.items():
        debug(f'<isParticipating({_user})> (_id: {_id}, \'active\': {_chall["active"]}, \'participants\': {_chall["participants"].keys()})')
        #if DEBUG:
        #    for _part in _chall["participants"].keys():
        #        dMSG += f'{type(_part)}, '
        #debug(f'<isParticipating({_user})> types: {dMSG}')
        if _chall["active"] == 1 and str(_user) in _chall["participants"].keys():
            debug(f'<isParticipating({str(_user)})> _user is participating in this challenge.')
            return True
        debug(f'<isParticipating({str(_user)})> found no challenges the user is participating in.')
    return False

# get all challenges user is participating in
def getAllParticipating(_user):
    participatingIn = []
    for id,chall in CHALLENGES.items():
        if chall["active"] == 1 and _user in chall["participants"].keys():
            participatingIn.append(id)
    return participatingIn

def joinChallenge(_user,_id):
    debug(f'<joinChallenge({_user},{_id})> _user: {type(_user)}, _id: {type(_id)}')
    if not isParticipating(_user):
        debug(f'<joinChallenge({_user},{_id})> user is not participating in any other challenges, attempting to add.')
        global CHALLENGES
        CHALLENGES[_id]['participants'][str(_user)] = {}
        writeJSON()
        debug(f'<joinChallenge({_user},{_id})> user added: {CHALLENGES[_id]["participants"]}')
        msg = f'Congratulations on joining the challenge: \'{CHALLENGES[_id]["name"]}\', now get to work! Use \'{CMD_PREFIX}cb me to show your current status.'
    else:
        debug(f'<joinChallenge({_user},{_id})> user is already participating in a challenge')
        msg = f'You were not added to this challenge because you\'re already in one.'
    return msg

def leaveChallenge(_user,_id):
    debug(f'<leaveChallenge({_user},{_id})> entered, _user: {type(_user)}, _id: {type(_id)}')
    global CHALLENGES
    debug(f'<leaveChallenge({_user},{_id})> CHALLENGES[_id][\'participants\'].keys(): {CHALLENGES[_id]["participants"].keys()}')
    if str(_user) in CHALLENGES[_id]['participants'].keys():
        debug(f'<leaveChallenge({_user},{_id})> trying to leave challenge')
        CHALLENGES[_id]['participants'].pop(str(_user))
        writeJSON()
        debug(f'<leaveChallenge({_user},{_id})> user removed from challenge')
        msg = f'You have been removed from \"{CHALLENGES[_id]["name"]}\".'
    else: 
        debug(f'<leaveChallenge({_user},{_id})> user not found in challenge ({CHALLENGES[_id]["participants"].keys()})')
        msg = f'You aren\'t listed as participating in \"{CHALLENGES[_id]["name"]}\".'
    return msg

def getUserNameFromID(_id: int):
    #if _id is str:
    #    _id2 = int(_id)
    #    _id = _id2
    #    debug(f'<getUserNameFromID({_id})> _id: {type(_id)}, _id2: {type(_id2)}')
    _username = bot.get_user(_id)
    if _username is None:
        debug(f'<getUserNameFromID({_id})> _username is {type(_username)}, switching _id from str to int.')
        _username = bot.get_user(int(_id))
    debug(f'<getUserNameFromID({_id})> _username: {_username} ({type(_username)})')
    return str(_username)

def getNowTime():
    return getDateString(datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc))

def getDayToday():
    return getDateString(datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc),"%Y%m%d")

def getDateObject(_input, _format=DATEUTC):
    return datetime.datetime.strptime(_input,_format)

def getDateString(_input, _format=DATEUTC):
    return _input.strftime(_format)

# take a date string in our std fmt and make it _format
def dateStrReformat(_input : str, _format : str):
    return getDateString(getDateObject(_input),_format)

def startNewChallenge():
    global newChallenge
    global newChallengeTime
    newChallenge = TEMPLATE.copy()
    newChallengeTime = getNowTime()

def saveNewChallenge():
    global newChallenge
    global newRequirements
    global CHALLENGES
    newChallenge["requirements"] = newRequirements
    CHALLENGES[newChallengeTime] = newChallenge
    writeJSON()
    printAll()

def cancelNew():
    global newChallenge, newRequirements, newChallengeTime
    newChallenge.clear()
    newRequirements.clear()
    newChallengeTime = ''

def removeChallenge(_id):
    global CHALLENGES
    _value = CHALLENGES.pop(_id,-1)
    debug(f'CHALLENGES.pop({_id},-1) = {_value}')
    writeJSON()
    printAll()
    #return f'fail/non-exist' if _value == '-1' else f'Successfully deleted challenge (ID: {_id}).'
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
        #else:
            #raise

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send('You do not have the correct role for this command.')

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

@bot.command(name='cbanew', help='cba new <name> <startDate> <endDate> [startTime] [endTime] - draft up <name> challenge, with start/end dates ("2020/09/21") and optionally start/end times in 24hr format ("2301").')
@commands.has_role(RO_CHALLENGER)
async def cbadmin_new(ctx, _name, _startDate, _endDate, _startTime = "0000", _endTime = "0000"):
    if ctx.message.author == bot.user:
        return
    startNewChallenge()
    newChallenge['name'] = _name
    newChallenge['start'] = getDateString(getDateObject(_startDate+_startTime,"%Y/%m/%d%H%M"))
    newChallenge['end'] = getDateString(getDateObject(_endDate+_endTime,"%Y/%m/%d%H%M"))
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
        await ctx.send(f'Created new challenge (ID: \'{newChallengeTime}\')')
        cancelNew()
    else:
        print(f'Failed to create')

@bot.command(name='cbadelete', help='cbadelete <id>')
@commands.has_role(RO_CHALLENGER)
async def cbadmin_delete(ctx, _id= '-1'):
    debug('entering <cbadelete>')
    if ctx.message.author == bot.user:
        debug('message author is the bot')
        return
    if _id != '-1':
        debug(f'<cbadelete> _id ({_id}) is not default (-1), continuing.')
        msg = f'Deleted challenge \"{CHALLENGES[_id].get("name")}\" (ID: \'{_id}\')'
        _return = removeChallenge(_id)
        #printAll()
        if _return == -1:
            msg = f'Challenge not found. Name: \"{CHALLENGES[_id].get("name")}\" (ID: {_id})'
    else:
        debug('<cbadelete> _id wasn\'t supplied, can\'t continue deleting.')
        msg = f'Can\' delete a challenge without knowing the ID of it.'
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
async def cbadmin_activate(ctx, _id: int, _active: int):
    if ctx.message.author == bot.user:
        return
    debug(f'<cbaactive> requested to set active=\'{_active}\'')
    if _active == 1 or _active == 0:
        msg = activateChallenge(_id,_active)
    else:
        msg = f'To activate, use \'1\'. To deactivate, use \'0\'.'
    await ctx.send(msg)

@bot.command(name='cb', help='cb - show current challenge(s).\ncb show <id> - show challenge information.\ncb join <id> - join challenge corresponding to <id>.\ncb update <requirement> <update> - Update your challenge status on <requirement> with <update>.')
async def cb(ctx, *args):
    if ctx.message.author == bot.user:
        return
    if len(args) > 0:
        if args[0] == 'me': #or args[0] == 'all':
            # respond with user's current status
            msg = listChallengeUser(int(ctx.message.author.id))
        elif args[0] == 'show' or args[0] == 'list':
            if len(args) >= 2 and args[1].isnumeric():
                msg = listChallenge(args[1])
            else:
                msg = f'Can\'t display challenge info without the challenge ID.'
        elif args[0] == 'join':
            debug(f'<cb join> entered')
            if len(args) >= 2 and args[1].isnumeric():
                debug(f'<cb join> _user: {int(ctx.message.author.id)}, _id: {args[1]}')
                msg = joinChallenge(int(ctx.message.author.id), args[1])
            else:
                msg = f'fail on joining, weird.'
        elif args[0] == 'update':
            if discord.ext.commands.has_role(RO_CHALLENGED):
                # user has role, now check for challenges and update
                msg = update(int(ctx.message.author.id), args)
            else: # user does not have the role
                msg = f'You don\'t appear to have the appropriate role ({RO_CHALLENGED}). Join a challenge via \"({CMD_PREFIX}cb join <id>\" to join a challenge or ask someone to give you the role.'
        elif args[0] == 'leave':
            debug(f'<cb leave> {args}')
            if len(args) >= 2 and args[1].isnumeric():
                msg = leaveChallenge(int(ctx.message.author.id), args[1])
            else:
                msg = f'Can\'t leave a challenge without knowing which challenge you wish to leave.'
        else: # command not understood
            msg = 'I didn\' understand that command.'
    else: # no command given, default to showing all challenges
        currChalls = getAllChallenges()
        if len(currChalls) > 0:
            msg = f'These are the challenges I\'m tracking:\n{getAllChallenges()}'
        else:
            msg = f'I\'m not tracking any challenges. How about you set one up?'
    await ctx.send(msg)

initJSON()
initLogging()
bot.run(DISCORD_TOKEN)
