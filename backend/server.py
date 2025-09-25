import eventlet
eventlet.monkey_patch()
import math
from flask import Flask, send_from_directory, request
from flask_socketio import SocketIO, emit
import threading, time 
import random

app = Flask(__name__, static_folder='../frontend/static', static_url_path='/')
socketio = SocketIO(app, cors_allowed_origins="*")

players = {}  # player_id = {x, y, color, health, kills, username, width, height, bodyAngle, turretAngle}
bullets = []
last_shot_time = {}
crates = []
explosions = []  # New list to track explosions
chat_history = []  # List to store chat messages

match_start_time = time.time()
match_running = True
match_ended_emmited = False
# Server-side Logic

GRID_COLS = 24
GRID_ROWS = 12
CRATE_SIZE = 20
CRATE_COUNT = 50
BULLET_RADIUS = 20

# 

def game_loop():
    global match_running, match_start_time, match_ended_emmited
    match_ended_emmited = False
    while True:
        update_bullets()
        cleanup_explosions()
        
        now = time.time()
        match_time_left = max(0, 300 - int(now - match_start_time))  # 5-minute rounds
        if match_time_left == 0:
            if not match_ended_emmited:
                match_running = False
                winner_id = max(players, key=lambda pid: players[pid]['kills']) if players else None
                winner_name = players[winner_id]['playerUsername'] if winner_id else "No one"
                winner_kills = players[winner_id]['kills'] if winner_id else 0
                socketio.emit('match_ended', {
                    'message': 'Match has ended!',
                    'winner': winner_name,
                    'kills': winner_kills,
                    }
                )
                match_ended_emmited = True
        else:
            match_running = True
            match_ended_emmited = False
        socketio.emit('game_state', {
            'players': players, 
            'bullets': bullets, 
            'crates': crates,
            'explosions': explosions,
            'match_time_left': match_time_left
        })
        time.sleep(1/30)




def generate_crate():
    crates = []
    used_cells = set()
    while len(crates) < CRATE_COUNT:
        col = random.randint(0, GRID_COLS - 1)
        row = random.randint(0, GRID_ROWS - 1)
        cell_key = f"({col}, {row})"
        if cell_key in used_cells:
            continue
        used_cells.add(cell_key)
        x = col * (1200 / GRID_COLS) + (1200 / GRID_COLS) / 2
        y = row * (600 / GRID_ROWS) + (600 / GRID_ROWS) / 2
        crates.append({'x': x, 'y': y, 'hits': 0})
    return crates

crates = generate_crate()

def update_bullets():
    global bullets, crates, players
    for i in range(len(bullets)-1, -1, -1):
        b = bullets[i]

        b['x'] += b['speed'] * math.cos(b['angle'])
        b['y'] += b['speed'] * math.sin(b['angle'])

        if b['x'] < 0 or b['x'] > 1200:
            b['angle'] = math.pi - b['angle']
            b['x'] = max(0, min(1200, b['x']))
            b['bounces'] = b.get('bounces', 0) + 1
        if b['y'] < 0 or b['y'] > 600:
            b['angle'] = -b['angle']
            b['y'] = max(0, min(600, b['y']))
            b['bounces'] = b.get('bounces', 0) + 1

        if b.get('bounces', 0) > 2:
            explosions.append({'x': b['x'],'y': b['y'],'startTime': time.time()})
            bullets.pop(i)

            continue
        # Check collision with players
        for pid, tank in players.items():
            dx = b['x'] - tank['x']
            dy = b['y'] - tank['y']
            distance = (dx**2 + dy**2)**0.5
            TANK_RADIUS = max(tank['width'], tank['height']) / 2
            if distance < TANK_RADIUS:
                tank['health'] -= 5
                explosions.append({'x': b['x'],'y': b['y'],'startTime': time.time()})  
                shooter_id = b.get('owner')
            # Award kill if tank destroyed
                if tank['health'] <= 0:
                    shooter_id = b.get('owner')
                    if shooter_id and shooter_id in players and shooter_id != pid:
                        players[shooter_id]['kills'] += 1
                    tank['x'], tank['y'] = safe_spawn()
                    tank['health'] = tank.get('maxHealth', 100)
                    leaderboard = {p: players[p]['kills'] for p in players}
                    socketio.emit('leaderboard', leaderboard)
                    socketio.emit('tank_destroyed', {'tank_id': pid, 'by': shooter_id})
                bullets.pop(i)
                break
        # Check collision with crates
        for crate in crates:
            if abs(b['x'] - crate['x']) < (CRATE_SIZE / 2 + BULLET_RADIUS) and abs(b['y'] - crate['y']) < (CRATE_SIZE / 2 + BULLET_RADIUS):
                
                dx = b['x'] - crate['x']
                dy = b['y'] - crate['y']
                if abs(dx) > abs(dy):
                    b['angle'] = math.pi - b['angle']
                else:
                    b['angle'] = -b['angle']
                b['crateBounces'] = b.get('crateBounces', 0) + 1
                crate['hits'] += 1
                if crate['hits'] >= 15:
                    crates.remove(crate)
                # Remove bullet after 3 bounces on crates
                if b['crateBounces'] >= 3:
                    explosions.append({'x': b['x'],'y': b['y'],'startTime': time.time()})  # or performance.now() on client
                    bullets.pop(i)
                break

    

def cleanup_explosions():
    now = time.time()
    explosions[:] = [e for e in explosions if now - e['startTime'] < 2.0]  # keep for 2 seconds

# Find a safe spawn point away from crates
def safe_spawn():
    for _ in range(200):
        x = random.uniform(50, 1200 - 50)
        y = random.uniform(50, 600 - 50)
        safe = True
        for crate in crates:
            if abs(x - crate['x']) < (CRATE_SIZE / 2 + 50) and abs(y - crate['y']) < (CRATE_SIZE / 2 + 50):
                safe = False
                break
        if safe:
            return x, y
    # Center if no safe spot found
    return 600, 300  


# Start the game loop in a separate thread

threading.Thread(target=game_loop, daemon=True).start()

# Flask Routes and SocketIO Events

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

@socketio.on('connect')
def connect():
    print(f"Player connected: {request.sid}")
    



@socketio.on('join')
def join(data):
    print(f"Player joined: {request.sid} with data: {data}")
    x, y = safe_spawn()
    color = data.get('color', 'green')
    players[request.sid] = {
        'x': x, 
        'y': y,
        'playerUsername': data.get('username', 'Player'),
        'color': color,
        'health': 100,
        'maxHealth': 100,
        'kills': 0,
        'width': 40,
        'height': 25,
        'bodyAngle': 0,
        'turretAngle': 0
    }
    emit('all_players', players, broadcast=True)
    emit('chat_history', chat_history, broadcast=True)

@socketio.on('move')
def move(data):
    if request.sid in players:
        players[request.sid]['x'] = data.get('x', players[request.sid]['x'])
        players[request.sid]['y'] = data.get('y', players[request.sid]['y'])
        players[request.sid]['bodyAngle'] = data.get('bodyAngle', players[request.sid].get('bodyAngle', 0))
        players[request.sid]['turretAngle'] = data.get('turretAngle', players[request.sid].get('turretAngle', 0))
        emit('all_players', players, broadcast=True)

@socketio.on('shoot')
def shoot(data):
    now = time.time()
    min_delay = 0.3  # seconds
    last_time = last_shot_time.get(request.sid, 0)
    if now - last_time >= min_delay:   
        data['owner'] = request.sid
        bullets.append(data)
        last_shot_time[request.sid] = now
    else :
        print(f"Shoot ignored for {request.sid}, too soon since last shot.")

@socketio.on('new_match')
def new_match():
    global crates, match_start_time, match_running, bullets, explosions
    match_start_time = time.time()
    match_running = True
    crates = generate_crate()
    for pid, player in players.items():
        player['x'], player['y'] = safe_spawn()
        player['health'] = player.get('maxHealth', 100)
        player['kills'] = 0
    bullets.clear()
    explosions.clear()

    emit('game_state', {
            'players': players,
            'bullets': bullets,
            'crates': crates,
            'explosions': explosions,
            'match_time_left': 300  
        }, broadcast=True)
    print("New match started.")


@socketio.on('chat_message')
def handle_chat(data):
    message = data.get('message', '')
    username = players.get(request.sid, {}).get('playerUsername', 'Player')
    chat_entry = {'username': username, 'message': message}
    chat_history.append(chat_entry)
    emit('chat_message', {'username': username, 'message': message}, broadcast=True)


@socketio.on('force_end') # For testing purposes do not use if ur not admin!!!!
def force_end():
    global match_start_time
    match_start_time = time.time() - 299  # Forces timer to 0

@socketio.on('disconnect')
def disconnect():
    print(f"Player disconnected: {request.sid}")
    players.pop(request.sid, None)
    emit('all_players', players, broadcast=True)



if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)



# Run this server with: python server.py


# The server will handle WebSocket connections for real-time game updates.
