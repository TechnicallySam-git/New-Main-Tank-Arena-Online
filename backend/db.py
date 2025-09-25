import sqlite3


DB_Path = "tankbattle.db"

import bcrypt





def get_db_connection():
    conn = sqlite3.connect(DB_Path)
    conn.row_factory = sqlite3.Row
    return conn

def create_match():
    with get_db_connection() as db:
        cur = db.execute('INSERT INTO matches DEFAULT VALUES()')
        db.commit()
        return cur.lastrowid

def end_match(match_id):
    with get_db_connection() as db:
        db.execute('UPDATE matches SET end_time = CURRENT_TIMESTAMP WHERE id = ?', (match_id,))
        db.commit()


def add_match_player(user_id, match_id):
    with get_db_connection() as db:
        db.execute(
            'INSERT INTO match_players (user_id, match_id) VALUES (?, ?)',
            (user_id, match_id)
        )
        db.commit()

def update_match_player_kills(user_id, match_id, kills=1):
    with get_db_connection() as db:
        db.execute(
            'UPDATE match_players SET kills = kills + ? WHERE user_id = ? AND match_id = ?',
            (kills, user_id, match_id)
        )
        db.commit()

def update_match_player_deaths(user_id, match_id, deaths=1):
    with get_db_connection() as db:
        db.execute(
            'UPDATE match_players SET deaths = deaths + ? WHERE user_id = ? AND match_id = ?',
            (deaths, user_id, match_id)
        )
        db.commit()


def update_match_player_score(user_id, match_id, score):
    with get_db_connection() as db:
        db.execute(
            'UPDATE match_players SET score = score + ? WHERE user_id = ? AND match_id = ?',
            (score, user_id, match_id)
        )
        db.commit()

def get_user_by_username(username):
    with get_db_connection() as db:
        return db.execute(
            'SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    


def update_kills(user_id, kills=1):
    with get_db_connection() as db:
        db.execute(
            'UPDATE leaderboard SET total_kills = total_kills + ? WHERE user_id = ?',
            (kills, user_id)
        )
        db.commit()


def add_user_to_leaderboard(username,password_hash, display_name, tank_color):
    hashed_pw = bcrypt.hashpw(password_hash.encode(), bcrypt.gensalt())
    with get_db_connection() as db:
        cur = db.execute(
            'INSERT INTO users (username, password_hash, display_name, tank_color) VALUES (?, ?, ?, ?)',
            (username, hashed_pw, display_name, tank_color)
        )
        user_id = cur.lastrowid
        db.execute(
            'INSERT INTO leaderboard (user_id) VALUES (?)',
            (user_id,)
        )
        db.commit()
        return user_id
    
def verify_user_password(username, password):
    user = get_user_by_username(username)
    if user and bcrypt.checkpw(password.encode(), user['password_hash']):
        return user
    return None


def update_deaths(user_id, deaths=1):
    with get_db_connection() as db:
        db.execute(
            'UPDATE leaderboard SET total_deaths = total_deaths + ? WHERE user_id = ?',
            (deaths, user_id)
        )
        db.commit() 

def update_score(user_id, score):
    with get_db_connection() as db:
        db.execute(
            'UPDATE leaderboard SET total_score = total_score + ? WHERE user_id = ?',
            (score, user_id)
        )
        db.commit()


def increment_matches_played(user_id):
    with get_db_connection() as db:
        db.execute(
            'UPDATE leaderboard SET matches_played = matches_played + 1 WHERE user_id = ?',
            (user_id,)
        )
        db.commit()

def get_leaderboard(limit=10):
    with get_db_connection() as db:
        return db.execute(
            'SELECT u.username, l.total_kills, l.total_score, l.matches_played '
            'FROM leaderboard l JOIN users u ON l.user_id = u.id '
            'ORDER BY l.total_kills DESC, l.total_score DESC LIMIT ?',
            (limit,)
        ).fetchall()
    

def get_user_match_history(user_id, limit=10):
    with get_db_connection() as db:
        return db.execute(
            'SELECT m.id as match_id, m.start_time, m.end_time, mp.kills, mp.deaths, mp.score '
            'FROM match_players mp JOIN matches m ON mp.match_id = m.id '
            'WHERE mp.user_id = ? ORDER BY m.start_time DESC LIMIT ?',
            (user_id, limit)
        ).fetchall()