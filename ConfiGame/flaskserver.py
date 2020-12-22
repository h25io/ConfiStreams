from flask import Flask, request, jsonify, send_file
from flask_api import status
import redis
import collections
import logging
import sched, time
import cron
import random
from PIL import Image

COLORMAP = [
        (0xd1, 0, 0), #Rouge
        (0x19, 0x7b, 0xbd), #Bleu
        (0x98, 0xce, 0), #Vert
        (0xff, 0x99, 0)  #Orange
]
COLORNAMES = ['RED', 'BLUE', 'GREEN', 'ORANGE']
schedo = sched.scheduler(time.time, time.sleep)

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

GRID_SIZE = 200
MAX_STEP = 20

app = Flask(__name__)
red = redis.Redis(host='localhost', port=6379, db=0)

def doTick():
    print('AM DOING THE TICK')
    for key in red.scan_iter("PREVPOSITION:*"):
        red.delete(key)

    userpositions = collections.defaultdict(list)
    teammap = {}
    for key in red.scan_iter("POSITION:*"):
        userid = key.split(b':')[1].decode()
        x, y, timestamp = red.get(key).split(b',')
        x = int(x)
        y = int(y)
        timestamp = float(timestamp)
        red.delete(key)
        userpositions[(x,y)].append((timestamp, userid))
        userteam = red.get('TEAM:'+userid).decode()
        teammap[userid] = userteam

    for pos in userpositions:
        userpositions[pos].sort()
        _, userid = userpositions[pos][0]
        x, y = pos
        red.set('PREVPOSITION:'+userid, f'{x},{y}')
        userpostitions[pos] = userid

    usercolormap = {}
    for pos in userpositions:
        userid = userpositions[pos]
        usercolor = []
        random.seed(userid)
        for i in range(3):
            component = COLORMAP[int(teammap[userid])][i] + random.randint(-20,20)
            component = min(255, component)
            component = max(0, component)
            usercolor.append(component)
        usercolormap[userid] = tuple(usercolor)

    grid = [[None for x in range(GRID_SIZE)] for y in range(GRID_SIZE)]
    for x in range(GRID_SIZE):
        for y in range(GRID_SIZE):
            bestusers = []
            bestdist = float('inf')
            for xx, yy in userpositions:
                userid = userpositions[(xx,yy)]
                dist = (xx-x)**2 + (yy-y)**2
                if dist < bestdist:
                    bestusers = [userid]
                    bestdist = dist
                elif dist == bestdist:
                    bestusers.append(userid)
            grid[y][x] = bestusers

    im = Image.new('RGB', (GRID_SIZE, GRID_SIZE))
    imdata = []
    score = collections.defaultdict(int)
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            imdata.append(usercolormap[grid[y][x][0]])
            for userid in grid[y][x]:
                score[userid] += 1

    for xx, yy in userpositions:
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                if not (0<=xx+dx<GRID_SIZE and 0<=yy+dy<GRID_SIZE):
                    continue
                imdata[xx+dx + GRID_SIZE * (yy+dy)] = (0, 0, 0)
    for xx, yy in deadpositions:
        if not (0<=xx<GRID_SIZE and 0<=yy<GRID_SIZE):
            continue
        imdata[xx + GRID_SIZE * yy] = (255, 255, 255)

    im.putdata(imdata)
    im.save('grid.png')
    im.save(f'grids/grid_{int(time.time())}.png')

    king = None
    kingScore = -1
    for userid in score:
        print(score[userid], userid, king, kingScore)
        if score[userid] > kingScore:
            king = userid
            kingScore = score[userid]

    red.set('KING', king)

    for userid in score:
        userscore = int(red.get('SCORE:'+userid) or 0)
        userteam = teammap[userid]
        red.set('TEAMSCORE:'+userteam, int(red.get('TEAMSCORE:'+userteam) or 0) + score[userid])
        score[userid] += userscore
        red.set('SCORE:'+userid, score[userid])

    for i in range(4):
        teamscore = red.get('TEAMSCORE:'+str(i))
        print(f'Team {i} has score {teamscore}')
    print('TICK DONE ! SCORES : ', score)

@app.route('/getKing')
def getking():
    kingid = red.get('KING')
    kingname = red.get(b'USERNAME:'+kingid).decode()
    kingteam = int(red.get(b'TEAM:'+kingid))
    hexcolor = '#'
    for j in range(3):
        hexcolor += hex(COLORMAP[kingteam][j])[2:].zfill(2)

    return '''
<html>
    <body>
    <p style="font-family:verdana;color:%s;margin:0">%s</p>
    <script>
        setTimeout(function(){
            window.location.reload(1);
        }, 30000);
    </script>
    </body>
</html>'''%(hexcolor, kingname)

@app.route('/getPreviousTick')
def getprevioustick():
    print('previousTick')
    resjson = {}
    for key in red.scan_iter("PREVPOSITION:*"):
        userid = key.split(b':')[1]
        x, y = map(int, red.get(key).split(b','))
        resjson[userid] = {
                'position': (x, y),
                'team': COLORNAMES[int(red.get(b'TEAM:'+userid))],
                'score': int(red.get(b'SCORE:'+userid)),
                'username': red.get(b'USERNAME:'+userid)
        }
    return jsonify(resjson)

@app.route('/setPosition')
def setpos():
    timestamp = time.time()
    args = request.args
    for arg in ('x', 'y', 'token'):
        if arg not in args:
            return 'Missing query param ' + arg, status.HTTP_400_BAD_REQUEST
    x = int(args.get('x'))
    y = int(args.get('y'))
    token = args.get('token')
    if not red.exists('TOKEN:'+token):
        return 'Invalid token. Please register with ConfiBot first.', status.HTTP_400_BAD_REQUEST
    userid = red.get('TOKEN:'+token).decode()

    if red.exists('PREVPOSITION:'+userid):
        prevx, prevy = map(int, red.get('PREVPOSITION:'+userid).split(b','))
        if abs(x - prevx) + abs(y-prevy) > MAX_STEP:
            return f'You can only move at most {MAX_STEP} Manhattan distance from your previous tick position {prevx}, {prevy}, or wait a turn', status.HTTP_400_BAD_REQUEST
    red.set('POSITION:'+userid, f'{x},{y},{timestamp}')
    print(f'Set position for user {userid} : {x},{y}')
    return 'OK'

@app.route('/image')
def getImage():
    return send_file('grid.png', mimetype='image/png')

@app.route('/scoreboard')
def getScoreboard():
    s = '''<html>
    <body>
        '''
    teamarr = []
    for i in range(4):
        hexcolor = '#'
        for j in range(3):
            hexcolor += hex(COLORMAP[i][j])[2:].zfill(2)
        teamscore = int(red.get('TEAMSCORE:'+str(i)))
        teamarr.append((-teamscore, f'<p style="font-family:verdana;color:{hexcolor};margin:0">{teamscore/1_000_000:.3f} M<br></p>'))
    teamarr.sort()
    for a, b in teamarr:
        s += b
    s += '''<script>
        setTimeout(function(){
            window.location.reload(1);
        }, 30000);
    </script>
    </body>
</html>'''
    return s

@app.route('/')
def root():
    return '''<html>
    <head>

    </head>
    <body>
        <img src="/image" id="myImage"/>
        <br><br><br>
        <h1>Règles du jeu</h1>
        <p>Bienvenue sur le ConfiGame, un jeu par équipe pour les viewers du <a href="https://twitch.tv/h25io">ConfiStream</a>.</p>
        <p>Le principe est simple : vous devez placer un pion sur la grille de jeu (taille 200x200), et votre but est de vous éloigner le plus possible des autres joueurs pour augmenter la taille de votre zone. Votre zone contient tous les points qui se trouvent plus proches de vous que d'un autre joueur.</p>
        <p>Créez des stratégies avec votre équipe pour répartir au mieux vos pions et faire gagner votre couleur !</p>
        <h2>Inscription</h2>
        <p>Pour vous inscrire, envoyez un message privé à l'utilisateur ConfiBot qui se trouve sur notre <a href="https://discord.h25.io">serveur Discord</a>, qui vous répondra avec un token secret et l'équipe dont vous faites partie.</p>
        <p>ConfiBot vous ajoute automatiquement au channel privé pour discuter avec le reste de votre équipe, par exemple <i>#configame-orange</i>.</p>
        <h2>Détails techniques</h2>
        <p>Pour placer votre pion, vous pouvez utiliser l'URL suivante : <pre>http://configame.h25.io/setPosition?x={x pion}&y={y pion}&token={votre token secret}</pre><b>Il n'est possible de se déplacer que de 20 unités à la fois</b> (comptées en <a href="https://fr.wikipedia.org/wiki/Distance_de_Manhattan">distance de Manhattan</a>). Si vous souhaitez vous déplacer à plus de 20 unités de distance, vous pouvez passer un tour mais vous ne recevrez aucun point pendant ce tour.</p>
        <p>Chaque tour dure une minute, et vous ne connaissez pas les positions des autres au tour actuel. Cependant, l'URL <pre>http://configame.h25.io/getPreviousTick</pre> vous permettra de récupérer les positions de chacun au tour précédent.</p>
        <p>Si vous avez des difficultés à jouer ou à automatiser vos requêtes, n'hésitez pas à demander à votre équipe dans le channel dédié !</p>
        <p>Le jeu est seulement actif pendant les ConfiStreams, le serveur ne répondra généralement pas aux requêtes en dehors des horaires de stream.</p>
    </body>
    <script>
        setTimeout(function(){
            window.location.reload(1);
        }, 30000);
    </script>
</html>'''

@app.after_request
def add_header(r):
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r

daemon = cron.Cron()
daemon.add('* * * * *', doTick)
daemon.start()

app.run('0.0.0.0', port=80, debug=False, threaded=True)
