from aitoken import token_balkanIA
import requests
import json
import chess
import random
import time

def make_get_requests(req):
    headers = {"Authorization": "Bearer " + token_balkanIA}
    req = requests.get("https://lichess.org" + req, headers=headers)
    return json.loads(req.text)

def make_post_requests(req):
    headers = {"Authorization": "Bearer " + token_balkanIA}
    req = requests.post("https://lichess.org" + req, headers=headers)
    return json.loads(req.text)

def make_stream_request(req):
    headers = {"Authorization": "Bearer " + token_balkanIA}
    return requests.get("https://lichess.org" + req, headers=headers, stream=True)

# A run une seule fois pour upgrade le compte en bot
def upgrade_bot():
    return make_post_requests("/api/bot/account/upgrade")

# Recupere la liste des events qui concerne le bot
def get_events():
    return make_stream_request("/api/stream/event")

# Accepte le challenge (c'est a dire la proposition de partie)
def accept_challenge(challenge_id):
    return make_post_requests("/api/challenge/" + challenge_id + "/accept")

def iter_lines(fd, chunk_size=1024):
    '''Iterates over the content of a file-like object line-by-line.'''
    pending = None
    while True:
        chunk = os.read(fd.fileno(), chunk_size)
        if not chunk:
            break
        if pending is not None:
            chunk = pending + chunk
            pending = None
        lines = chunk.splitlines()
        if lines and lines[-1]:
            pending = lines.pop()
        for line in lines:
            yield line
    if pending:
        yield(pending)

def score_values(board, player):
    values = {'p' : 1, 'b' : 3, 'n' : 3, 'r' : 5, 'q' : 9}
    ans = 0
    for c in board.fen().split()[0]:
        if c.lower() not in values:
            continue
        if player == chess.BLACK and c.islower():
            ans += values[c]
        if player == chess.WHITE and c.isupper():
            ans += values[c.lower()]
    return ans

def evaluate_values(board):
    return score_values(board, board.turn) - score_values(board, not board.turn)



def score_bishops(board, player):
    nb_bishop = 0
    for c in board.fen():
        if c.lower() != 'b':
            continue
        if player == chess.BLACK and c.islower():
            nb_bishop += 1
        if player == chess.WHITE and c.isupper():
            nb_bishop += 1
    return nb_bishop // 2

def evaluate_bishops(board):
    return score_bishops(board, board.turn) - score_bishops(board, not board.turn)

def score_center(board, player):
    base_board = board #chess.BaseBoard(board.fen())
    x = []
    for i in range(8):
        for j in range(8):
            if base_board.color_at(8*i + j) == player:
                x.append(abs(i-3.5))
                x.append(abs(j-3.5))
    return -sum(x)/len(x)

def evaluate_center(board):
    return score_center(board,board.turn) - score_center(board,not board.turn) 

def nb_controlled_cases(board):
    return len(set([x.to_square for x in board.legal_moves]))

def evaluate(board):
    if board.is_checkmate():
        return -100000000000
    return 1000 * (evaluate_values(board) + evaluate_bishops(board)) + 250*evaluate_center(board) + len(list(board.legal_moves)) + 20*nb_controlled_cases(board)


def rec_evaluate(board,n):
    if n == 1:
        return evaluate(board)
    else:
        l = list(board.legal_moves)
        ans =  -1000000000
        for x in l:
            board.push(x)
            ans = max(ans, -rec_evaluate(board, n - 1))
            board.pop()
        return ans

def play_game(challenge_id):
    print("Game lancee")
    #game_request = make_post_requests("/api/bot/game/stream/" + challenge_id)
    #print(make_post_requests("/api/bot/game/" + challenge_id + "/move/e2e4")
    my_color = ""
    for game_request_text in make_stream_request("/api/bot/game/stream/" + challenge_id).iter_lines():
        if game_request_text:
            game_request = json.loads(game_request_text)
            #print('\n\n',game_request)
            #if game_request_text)
            if game_request["type"] == "gameFull":
                if game_request["white"].get("name") == "balkanIA":
                    my_color = chess.WHITE
                    print(make_post_requests("/api/bot/game/" + challenge_id + "/move/d2d4"))
                else:
                    my_color = chess.BLACK
                print("J'ai trouvé ma couleur, qui est", my_color)
            if game_request["type"] == "gameState":
                board = chess.Board()
                moves = game_request["moves"]
                for mv in moves.split():
                    board.push_uci(mv)
                if board.turn == my_color:
                    list_moves = []
                    for x in board.legal_moves:
                        board.push(x)
                        list_moves.append((rec_evaluate(board,2),random.random(),x))
                        board.pop()
                    if list_moves:
                        (_,_,move) = min(list_moves)
                        print(move)
                        print(make_post_requests("/api/bot/game/" + challenge_id + "/move/" + move.uci()))

def challenge_ai():
    headers = {"Authorization": "Bearer " + token_balkanIA}
    req = requests.post("https://lichess.org/api/challenge/ai", headers=headers,data={"level":3, "color":"white"})
    print("The post for AI challenge is", req.text)
    game_id = req.json()['id']
    print('https://lichess.org/'+game_id)
    time.sleep(3)
    play_game(game_id)

def main():
    #https://lichess.org/api#operation/challengeAi
    #challenge_ai()
    for current_event in get_events().iter_lines():
        print("On vient de recevoir un event", current_event)
        if current_event:
            event = json.loads(current_event)
            if event["type"] == "challenge":
                challenge = event["challenge"]
                print("Cet event est un challenge de " + challenge["challenger"]["id"])
                challenge_id = challenge["id"]
                print('https://lichess.org/'+challenge_id)
                if challenge["challenger"]["name"] == "DominiqueDiPierro":
                    accept_challenge(challenge_id)
                    play_game(challenge_id)


main()