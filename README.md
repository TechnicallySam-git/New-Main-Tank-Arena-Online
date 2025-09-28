# Main Tank Arena Online

A real-time multiplayer tank battle game built with Flask, Flask-SocketIO, and a modern JavaScript frontend.

---

## Features

- Real-time multiplayer tank battles
- Player chat and leaderboard
- Crates and destructible environment
- Custom tank color selection
- Match timer and automatic restarts
- Responsive UI with in-game overlays

---

## Project Structure

```
New Main Tank Arena Online/
├── backend/
│   └── server.py
├── frontend/
│   └── static/
│       └── index.html
│       └── camo-pat.jpg
│       └── explosion.png
│       └── Picture1.png
├── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.8+
- pip
- (Recommended) Virtual environment

### Backend Setup

1. **Install dependencies:**
    ```bash
    pip install flask flask-socketio eventlet
    ```

2. **Run the server:**
    ```bash
    python backend/server.py
    ```
    The server will start on `0.0.0.0:5000`.

### Frontend

- The frontend is served automatically by Flask at `/` and `/static/`.
- Open your browser and go to `http://localhost:5000` (or your server's public URL).

---

## Production Deployment

### Using nginx as a Reverse Proxy

1. **Configure nginx:**
    ```
    server {
        listen 80;
        server_name yourdomain.com;

        location / {
            include proxy_params;
            proxy_pass http://127.0.0.1:5000;
        }

        location /static/ {
            alias /path/to/your/project/frontend/static/;
            expires 30d;
        }

        location /socket.io {
            include proxy_params;
            proxy_http_version 1.1;
            proxy_buffering off;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "Upgrade";
            proxy_pass http://127.0.0.1:5000/socket.io;
        }
    }
    ```

2. **Firewall:**  
   Block public access to port 5000; only allow nginx (localhost) to connect.

3. **Frontend Socket.IO:**  
   In `index.html`, use:
   ```javascript
   const socket = io();
   ```
   This ensures the client connects via the main URL and port 80.

---

## How to Play

1. Open the game in your browser.
2. Enter a username and password to log in.
3. Select your tank color.
4. Use **WASD** to move, **mouse** to aim, **spacebar** or **mouse click** to shoot.
5. Chat with other players and climb the leaderboard!

---

## Credits

- Built with Flask, Flask-SocketIO, and JavaScript Canvas
- Developed by Ethiën Maduro

---
