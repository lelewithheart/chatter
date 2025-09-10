import socket, threading
import sqlite3
from cipher import decrypt_message, encrypt_message
from datetime import datetime

KEY = "secretpass"
clients = []

# --- Chat DB für Instanz ---
chatdb = sqlite3.connect("chat.db", check_same_thread=False)
chatcur = chatdb.cursor()
chatcur.execute("""
CREATE TABLE IF NOT EXISTS chat (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    message TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")
chatdb.commit()

def save_chat(username, message):
    if not message.strip():
        return  # Leere Nachrichten nicht speichern
    chatcur.execute("INSERT INTO chat (username, message) VALUES (?, ?)", (username, message))
    chatdb.commit()

def handle_client(conn, addr):
    print(f"[+] New connection from {addr}")
    authenticated = False
    username = None
    try:
        while not authenticated:
            data = conn.recv(1024).decode()
            if data.startswith("LOGIN|"):
                _, user, pw = data.split("|", 2)
                # Keine User-DB, akzeptiere jeden User/Pass
                conn.send("LOGIN_OK".encode())
                authenticated = True
                username = user
            else:
                conn.send("INVALID_CMD".encode())
        clients.append((conn, username))
        # --- Sende Chatverlauf ---
        chatcur.execute("SELECT username, message, timestamp FROM chat ORDER BY id ASC")
        history = chatcur.fetchall()
        for uname, msg, ts in history:
            if not msg.strip():
                continue
            try:
                conn.send((encrypt_message(f"[{ts[:16]}] {uname}: {msg}", KEY) + "\n").encode())
            except:
                pass
        # --- Chat/PM-Loop ---
        while True:
            data = conn.recv(1024).decode()
            if not data.strip():
                continue
            if data.startswith("PM|"):
                _, empfaenger, nachricht = data.split("|", 2)
                for c, uname in clients:
                    if uname == empfaenger:
                        c.send(f"PM|{username}|{nachricht}".encode())
                        break
            else:
                msg = decrypt_message(data, KEY)
                now = datetime.now().strftime("%Y-%m-%d %H:%M")
                print(f"{username}@{addr}: {msg}")
                save_chat(username, msg)
                for c, uname in clients:
                    c.send((encrypt_message(f"[{now}] {username}: {msg}", KEY) + "\n").encode())
    except:
        clients[:] = [(c, u) for c, u in clients if c != conn]
        conn.close()

def main():
    s = socket.socket()
    s.bind(("0.0.0.0", 12346))
    s.listen(5)
    print("[*] Server-Instance listening on port 12346")
    while True:
        try:
            conn, addr = s.accept()
            threading.Thread(target=handle_client, args=(conn, addr)).start()
        except OSError:
            break

if __name__ == "__main__":
    main()
