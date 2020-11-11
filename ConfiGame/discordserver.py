import discord
import discord.utils
import redis
import random

red = redis.Redis(host='localhost', port=6379, db=0)
DISCORD_TOKEN = open('discord_token.txt').read()
COLORS = ['RED', 'BLUE', 'GREEN', 'ORANGE']
ROLE_IDS = [772912381894197288, 772912277673869374, 772912445613539329, 772912512726204440]

intents = discord.Intents.default()
intents.presences = True
intents.members   = True
client = discord.Client(intents=intents)

@client.event
async def on_message(message):
    '''for key in red.scan_iter('TEAM:*'):
        userid = int(key.decode().split(':')[1])
        username = client.get_user(userid).name
        red.set('USERNAME:' + str(userid), username)
    '''    
    if isinstance(message.channel, discord.channel.DMChannel) and message.author != client.user:
        print(f'New DM from {message.channel.recipient} : {message.content}')
        userid = str(message.channel.recipient.id).encode()
        username = message.channel.recipient.name
        #print(client.get_guild(650008117781725248).members,)
        memberid = discord.utils.get(client.get_guild(650008117781725248).members, id=message.channel.recipient.id)
        print(memberid)
        if not red.exists(b'USER:'+userid):
            usertoken = str(hex(random.getrandbits(256))[2:]).encode()
            userteam = random.randrange(4)
            red.set(b'USER:' + userid, usertoken)
            red.set(b'TOKEN:' + usertoken, userid)
            red.set(b'TEAM:' + userid, userteam)
            red.set(b'USERNAME:' + userid, username)
            role = client.get_guild(650008117781725248).get_role(ROLE_IDS[userteam])
            await memberid.add_roles(role)
        else:
            usertoken = red.get(b'USER:' + userid)
            userteam = int(red.get(b'TEAM:' + userid))
        teamcolor = COLORS[userteam]
        await message.channel.send(f'Your ConfiGame token is {usertoken.decode()} and you are in the {teamcolor} team')

client.run(DISCORD_TOKEN)
