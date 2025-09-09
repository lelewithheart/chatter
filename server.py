# server.py
import socket, threading
import sqlite3
from cipher import decrypt_message, encrypt_message
import sys
from datetime import datetime

KEY = "secretpass"
clients = []
stop_flag = threading.Event()

# --- SQLite DB Setup ---
db = sqlite3.connect("users.db", check_same_thread=False)
cur = db.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT NOT NULL
)
""")
db.commit()

# --- Chat DB für Main Server ---
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
                cur.execute("SELECT * FROM users WHERE username=? AND password=?", (user, pw))
                if cur.fetchone():
                    conn.send("LOGIN_OK".encode())
                    authenticated = True
                    username = user
                else:
                    conn.send("LOGIN_FAIL".encode())
            elif data.startswith("REGISTER|"):
                _, user, pw = data.split("|", 2)
                cur.execute("SELECT * FROM users WHERE username=?", (user,))
                if cur.fetchone():
                    conn.send("REGISTER_FAIL".encode())
                else:
                    cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (user, pw))
                    db.commit()
                    conn.send("REGISTER_OK".encode())
            else:
                conn.send("INVALID_CMD".encode())
        # Nach erfolgreichem Login:
        clients.append((conn, username))
        # --- Sende Chatverlauf aus chat.db ---
        chatcur.execute("SELECT username, message, timestamp FROM chat ORDER BY id ASC")
        history = chatcur.fetchall()
        for uname, msg, ts in history:
            try:
                # Immer im Chat-Format mit Zeitstempel senden
                conn.send(encrypt_message(f"[{ts[:16]}] {uname}: {msg}", KEY).encode())
            except:
                pass
        # --- Chat/PM-Loop ---
        while True:
            data = conn.recv(1024).decode()
            if data.startswith("PM|"):
                # PM|empfaenger|nachricht
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
                    # Sende immer im Chat-Format mit Zeitstempel
                    c.send((encrypt_message(f"[{now}] {username}: {msg}", KEY) + "\n").encode())
    except:
        # Client entfernen
        clients[:] = [(c, u) for c, u in clients if c != conn]
        conn.close()

def console_thread(server_socket):
    while True:
        cmd = input()
        if cmd.strip().lower() == "stopp":
            print("Server wird gestoppt...")
            stop_flag.set()
            # Alle Clients trennen
            for c, _ in clients:
                try:
                    c.shutdown(socket.SHUT_RDWR)
                    c.close()
                except:
                    pass
            try:
                server_socket.close()
            except:
                pass
            sys.exit(0)

def main():
    s = socket.socket()
    s.bind(("0.0.0.0", 12346))
    s.listen(5)
    print("[*] Server listening on port 12346")
    threading.Thread(target=console_thread, args=(s,), daemon=True).start()
    while not stop_flag.is_set():
        try:
            conn, addr = s.accept()
            threading.Thread(target=handle_client, args=(conn, addr)).start()
        except OSError:
            break

if __name__ == "__main__":
    main()
