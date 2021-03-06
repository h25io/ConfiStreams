import discord
import discord.utils
from discord.ext import tasks
import time
import asyncio
import random

DISCORD_TOKEN = open('discord_token.txt').read()
CHANNEL_ID = 814932250444824647
ORANGE_EMOJI = b'\xf0\x9f\x9f\xa0'
GREEN_EMOJI = b'\xf0\x9f\x9f\xa2'
NUM_EMOJIS = [b'1\xef\xb8\x8f\xe2\x83\xa3',
          b'2\xef\xb8\x8f\xe2\x83\xa3',
          b'3\xef\xb8\x8f\xe2\x83\xa3',
          b'4\xef\xb8\x8f\xe2\x83\xa3',
          b'5\xef\xb8\x8f\xe2\x83\xa3',
          b'6\xef\xb8\x8f\xe2\x83\xa3',
          b'7\xef\xb8\x8f\xe2\x83\xa3']

global akiltour, players, GAME_BOARD
akiltour = -1
players = [None, set(), set()]

client = discord.Client()

GAME_BOARD = [[0 for i in range(7)] for j in range(6)]

def who_wins(board):
    # ça rep 0/1/2
    for color in [1, 2]:
        for i in range(len(board)):
            for j in range(len(board[i]) - 3):
                if all(board[i][x] == color for x in range(j, j+4)):
                    return color

        for i in range(len(board) - 3):
            for j in range(len(board[i])):
                if all(board[x][j] == color for x in range(i, i+4)):
                    return color

        for i in range(len(board) - 3):
            for j in range(len(board[0]) - 3):
                if all(board[i + x][j+x] == color for x in range(4)):
                    return color
                
        for i in range(3, len(board)):
            for j in range(len(board[0]) - 3):
                if all(board[i-x][j+x] == color for x in range(4)):
                    return color
    return 0


def move(board, column, color):
    if board[0][column] !=0:
        return False
    c = max(x for x in range(6) if board[x][column]==0)
    board[c][column] = color


def getBoardAsString(board):
    s = ''
    for r in range(6):
        for c in range(7):
            v = board[r][c]
            if v == 0:
                s += ':black_large_square:'
            elif v == 1:
                s += ':orange_circle:'
            elif v == 2:
                s += ':green_circle:'
            else:
                assert False
        s += '\n'
    s += ':one::two::three::four::five::six::seven:'
    return s

async def printTurn(channel, board, akiltour):
    team_emoji = [None, ':orange_circle:', ':green_circle:'][akiltour]
    await channel.send('Equipe '+team_emoji+', faites vos jeux!\n'+getBoardAsString(board))
    lastmsg = await channel.fetch_message(channel.last_message_id)
    for emoji in NUM_EMOJIS:
        await lastmsg.add_reaction(emoji.decode())

# Welcome
# Init (chacun choisit son camp)
# Game akiltour = 1
# Game akiltour = 2
# Game akiltour = 1
# ...
# quelqu'un win
# bravo

@tasks.loop(seconds=15)
async def gameLoop():
    global akiltour, players, GAME_BOARD
    channel = client.get_channel(CHANNEL_ID)
    message = await channel.fetch_message(channel.last_message_id)
    if akiltour == -1:
        msg = await channel.send('New game ! React pour choisir ton camp')
        await msg.add_reaction(ORANGE_EMOJI.decode())
        await msg.add_reaction(GREEN_EMOJI.decode())
        akiltour = 0
    elif akiltour == 0:
        orange_reactors, green_reactors = [], []
        for reaction in message.reactions:
            emoji = reaction.emoji
            reactors = await reaction.users().flatten()
            if isinstance(emoji, str):
                if emoji.encode() == ORANGE_EMOJI:
                    orange_reactors = [reactor.id for reactor in reactors]
                elif emoji.encode() == GREEN_EMOJI:
                    green_reactors = [reactor.id for reactor in reactors]
        #green_reactors = [x for x in green_reactors if x not in orange_reactors] # TODO O(N)
        players = [None, set(orange_reactors), set(green_reactors)]
        
                
        print('Equipes choisies', players)
        akiltour = random.choice((1,2))
        await printTurn(channel, GAME_BOARD, akiltour)
    else:
        votes = []
        for reaction in message.reactions:
            emoji = reaction.emoji
            reactors = await reaction.users().flatten()
            if emoji.encode() in NUM_EMOJIS:
                for reactor in reactors:
                    if reactor.id in players[akiltour]:
                        idx = NUM_EMOJIS.index(emoji.encode())
                        if GAME_BOARD[0][idx] == 0:
                            votes.append(idx)
        print('Votes:', votes)
        playpos = random.randrange(7)
        
        if votes:
            max_votes = max(votes.count(x) for x in votes)
            top_choices = [x for x in votes if votes.count(x) == max_votes]
            playpos = random.choice(top_choices) 
            
        move(GAME_BOARD, playpos, akiltour)
        winner = who_wins(GAME_BOARD)
        if winner != 0:
            team_emoji = [None, ':orange_circle:', ':green_circle:'][akiltour]
            await channel.send('Team '+ team_emoji +' wins!')
            await printTurn(channel, GAME_BOARD, akiltour)
            GAME_BOARD = [[0 for i in range(7)] for j in range(6)]
            akiltour = -1
        else:
            akiltour = 3 - akiltour # 2 -> 1, 1 -> 2
            await printTurn(channel, GAME_BOARD, akiltour)
           
                
    #await channel.send(getBoardAsString(GAME_BOARD))
    #LAST_MESSAGE_SENT = await channel.send("lel :fire:")

@client.event
async def on_ready():
    print('connected and ready')
    gameLoop.start()

client.run(DISCORD_TOKEN)

