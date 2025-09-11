# client.py
import socket, threading
import tkinter as tk
from tkinter import messagebox
import sqlite3
from cipher import encrypt_message, decrypt_message
import subprocess
import sys
import os
from pathlib import Path

# AppData/Local für den Benutzer
appdata = Path(os.getenv('LOCALAPPDATA')) / "GhostChat"
appdata.mkdir(parents=True, exist_ok=True)

db_path = appdata / "messages.db"

KEY = "secretpass"
HOST = "46.62.206.103"

client = socket.socket()
user_password = None  # Passwort global speichern

# --- SQLite DB für PNs ---
msgdb = sqlite3.connect(db_path)
msgcur = msgdb.cursor()
msgcur.execute("""
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    sender TEXT,
    message TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")
msgdb.commit()

msgcur.execute("""
CREATE TABLE IF NOT EXISTS favorites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    favname TEXT,
    ip TEXT
)
""")
msgdb.commit()

def save_pm(username, sender, message):
    msgcur.execute("INSERT INTO messages (username, sender, message) VALUES (?, ?, ?)", (username, sender, message))
    msgdb.commit()

def load_inbox(username):
    msgcur.execute("SELECT sender, message, timestamp FROM messages WHERE username=? ORDER BY timestamp DESC", (username,))
    return msgcur.fetchall()

def add_favorite(favname, ip):
    msgcur.execute("INSERT INTO favorites (favname, ip) VALUES (?, ?)", (favname, ip))
    msgdb.commit()

def load_favorites():
    msgcur.execute("SELECT id, favname, ip FROM favorites ORDER BY favname")
    return msgcur.fetchall()

def delete_favorite(favid):
    msgcur.execute("DELETE FROM favorites WHERE id=?", (favid,))
    msgdb.commit()

# --- Inbox GUI ---
def show_inbox(username):
    inbox_win = tk.Toplevel()
    inbox_win.title("Inbox")
    inbox_win.geometry("500x500")  # Größer
    inbox_win.configure(bg="#f0f4fa")
    font_label = ("Segoe UI", 12)
    tk.Label(inbox_win, text=f"Inbox von {username}", font=("Segoe UI", 15, "bold"), bg="#f0f4fa").pack(pady=(12, 8))
    listbox = tk.Listbox(inbox_win, font=font_label, width=60, height=22)
    listbox.pack(padx=12, pady=8, fill="both", expand=True)
    for sender, msg, ts in load_inbox(username):
        listbox.insert(tk.END, f"[{ts[:16]}] Von {sender}: {msg}")
    btn_frame = tk.Frame(inbox_win, bg="#f0f4fa")
    btn_frame.pack(pady=8)
    tk.Button(btn_frame, text="Zurück zum Hauptmenü", command=lambda: [inbox_win.destroy(), show_homescreen(username)],
              font=font_label, bg="#e0e7ef", bd=0).pack(side='left', padx=4)
    tk.Button(btn_frame, text="Schließen", command=inbox_win.destroy, font=font_label, bg="#e0e7ef", bd=0).pack(side='left', padx=4)
    inbox_win.bind('<Return>', lambda e: inbox_win.destroy())

# --- Homescreen GUI ---
def show_homescreen(username):
    home = tk.Toplevel()
    home.title("Chatter Homescreen")
    home.geometry("500x500")  # Größer
    home.configure(bg="#f0f4fa")
    font_title = ("Segoe UI", 16, "bold")
    font_button = ("Segoe UI", 12, "bold")
    font_label = ("Segoe UI", 12)
    tk.Label(home, text=f"Willkommen, {username}!", font=font_title, bg="#f0f4fa").pack(pady=(30, 20))

    def go_global():
        home.destroy()
        connect_and_start_chat(username, user_password, HOST)

    def go_custom():
        def connect_custom():
            ip = entry_ip.get().strip()
            if not ip:
                msg_label.config(text="Bitte IP eingeben.")
                return
            win.destroy()
            home.destroy()
            connect_and_start_chat(username, user_password, ip)
        win = tk.Toplevel(home)
        win.title("Zu Chat-Server verbinden")
        win.geometry("400x200")
        win.configure(bg="#f0f4fa")
        tk.Label(win, text="Server-IP:", font=font_label, bg="#f0f4fa").pack(pady=(18,2))
        entry_ip = tk.Entry(win, font=font_label)
        entry_ip.pack(pady=2)
        msg_label = tk.Label(win, text="", fg="red", bg="#f0f4fa", font=font_label)
        msg_label.pack()
        btn_frame = tk.Frame(win, bg="#f0f4fa")
        btn_frame.pack(pady=12)
        tk.Button(btn_frame, text="Verbinden", command=connect_custom, font=font_button, bg="#4f8cff", fg="white", bd=0, relief="ridge", activebackground="#357ae8").pack(side='left', padx=4)
        tk.Button(btn_frame, text="Zurück zum Hauptmenü", command=win.destroy, font=font_button, bg="#e0e7ef", fg="#333", bd=0, relief="ridge", activebackground="#d0d7df").pack(side='left', padx=4)
        entry_ip.bind('<Return>', lambda e: connect_custom())

    tk.Button(home, text="Globaler Chat", command=go_global, font=font_button, bg="#4f8cff", fg="white", bd=0, relief="ridge", activebackground="#357ae8").pack(fill="x", padx=60, pady=12, ipady=6)
    tk.Button(home, text="Zu Chat-Server mit IP verbinden", command=go_custom, font=font_button, bg="#4f8cff", fg="white", bd=0, relief="ridge", activebackground="#357ae8").pack(fill="x", padx=60, pady=12, ipady=6)
    tk.Button(home, text="Favoriten", command=lambda: show_favorites(username, home), font=font_button, bg="#e0e7ef", fg="#333", bd=0, relief="ridge", activebackground="#d0d7df").pack(fill="x", padx=60, pady=12, ipady=6)

    home.mainloop()

def connect_and_start_chat(username, password, host):
    global client
    client = socket.socket()
    try:
        client.connect((host, 12346))
    except:
        messagebox.showerror("Fehler", f"Verbindung zu {host} fehlgeschlagen.")
        show_homescreen(username)
        return
    client.send(f"LOGIN|{username}|{password}".encode())
    resp = client.recv(1024).decode()
    if resp != "LOGIN_OK":
        messagebox.showerror("Fehler", "Login am Zielserver fehlgeschlagen.")
        show_homescreen(username)
        return
    
    server_version_msg = client.recv(1024).decode("us-ascii", errors="ignore")
    if server_version_msg.startswith("VERSION|"):
        server_version = server_version_msg.split("|", 1)[1].strip()
        try:
            with open("version.txt", "r") as f:
                local_version = f.read().strip()
        except FileNotFoundError:
            local_version = "unknown"

        if local_version != server_version:
            # Popup anzeigen
            def run_updater():
                try:
                    subprocess.Popen(["Updater.exe"])
                except FileNotFoundError:
                    messagebox.showerror("Fehler", "Updater.exe nicht gefunden!")
                finally:
                    client.close()
                    sys.exit(0)  # Client beenden

            update_win = tk.Toplevel()
            update_win.title("Update notwendig")
            tk.Label(update_win, text=f"Deine Version: {local_version}\nServer-Version: {server_version}\n\nBitte updaten!", font=("Segoe UI", 12)).pack(padx=20, pady=20)
            tk.Button(update_win, text="Update starten", command=run_updater, font=("Segoe UI", 12, "bold"), bg="#4f8cff", fg="white").pack(pady=10)
            update_win.protocol("WM_DELETE_WINDOW", run_updater)  # Wenn Fenster geschlossen wird → auch Updater starten
            return
    
    start_chat(username)

# --- Auth GUI ---
def show_auth_window():
    global user_password
    auth_win = tk.Toplevel()
    auth_win.title("Login/Register")
    auth_win.geometry("500x400")  # Größer
    auth_win.configure(bg="#f0f4fa")
    mode = tk.StringVar(value="login")

    def switch_mode():
        if mode.get() == "login":
            mode.set("register")
            btn_login.pack_forget()
            btn_register.pack(side="left", expand=True, fill="x", padx=5)
            label_pw2.pack(after=entry_pw, pady=(0,0))
            entry_pw2.pack(after=label_pw2, pady=5)
        else:
            mode.set("login")
            btn_register.pack_forget()
            btn_login.pack(side="left", expand=True, fill="x", padx=5)
            label_pw2.pack_forget()
            entry_pw2.pack_forget()

    font_label = ("Segoe UI", 12)
    font_entry = ("Segoe UI", 12)
    font_button = ("Segoe UI", 12, "bold")

    tk.Label(auth_win, text="Benutzername:", bg="#f0f4fa", font=font_label).pack(pady=(28,0))
    entry_user = tk.Entry(auth_win, font=font_entry, bd=2, relief="groove")
    entry_user.pack(pady=8, ipadx=8, ipady=4)
    tk.Label(auth_win, text="Passwort:", bg="#f0f4fa", font=font_label).pack()
    entry_pw = tk.Entry(auth_win, show="*", font=font_entry, bd=2, relief="groove")
    entry_pw.pack(pady=8, ipadx=8, ipady=4)
    label_pw2 = tk.Label(auth_win, text="Passwort wiederholen:", bg="#f0f4fa", font=font_label)
    entry_pw2 = tk.Entry(auth_win, show="*", font=font_entry, bd=2, relief="groove")
    entry_pw2.insert(0, "")

    msg_label = tk.Label(auth_win, text="", fg="red", bg="#f0f4fa", font=font_label)
    msg_label.pack(pady=(8,0))

    def do_login():
        global user_password
        user = entry_user.get()
        pw = entry_pw.get()
        try:
            client.connect((HOST, 12346))
        except:
            msg_label.config(text="Verbindung fehlgeschlagen")
            return
        client.send(f"LOGIN|{user}|{pw}".encode())
        resp = client.recv(1024).decode()
        if resp == "LOGIN_OK":
            user_password = pw  # Passwort speichern
            auth_win.destroy()
            show_homescreen(user)
        else:
            msg_label.config(text="Login fehlgeschlagen")
            client.close()
            reset_client()

    def do_register():
        user = entry_user.get()
        pw = entry_pw.get()
        pw2 = entry_pw2.get()
        if not user or not pw:
            msg_label.config(text="Bitte alle Felder ausfüllen.")
            return
        if pw != pw2:
            msg_label.config(text="Passwörter stimmen nicht überein.")
            return
        try:
            client.connect((HOST, 12346))
        except:
            msg_label.config(text="Verbindung fehlgeschlagen")
            return
        client.send(f"REGISTER|{user}|{pw}".encode())
        resp = client.recv(1024).decode()
        if resp == "REGISTER_OK":
            messagebox.showinfo("Erfolg", "Registrierung erfolgreich! Bitte einloggen.")
            client.close()
            reset_client()
            switch_mode()
        else:
            msg_label.config(text="Benutzername existiert bereits.")
            client.close()
            reset_client()

    def reset_client():
        global client
        client = socket.socket()

    btn_frame = tk.Frame(auth_win, bg="#f0f4fa")
    btn_frame.pack(pady=20, fill="x")
    btn_login = tk.Button(btn_frame, text="Login", command=do_login, font=font_button, bg="#4f8cff", fg="white", bd=0, relief="ridge", activebackground="#357ae8", activeforeground="white", highlightthickness=0)
    btn_login.pack(side="left", expand=True, fill="x", padx=5, ipadx=6, ipady=3)
    btn_register = tk.Button(btn_frame, text="Register", command=do_register, font=font_button, bg="#4f8cff", fg="white", bd=0, relief="ridge", activebackground="#357ae8", activeforeground="white", highlightthickness=0)
    # initially hidden

    tk.Button(auth_win, text="Zurück zum Hauptmenü", command=lambda: [auth_win.destroy(), show_homescreen(entry_user.get() or "Gast")],
              font=font_button, bg="#e0e7ef", fg="#333", bd=0, relief="ridge", activebackground="#d0d7df").pack(pady=8, ipadx=2, ipady=1)

    switch_btn = tk.Button(auth_win, text="Zu Register/Login wechseln", command=switch_mode, font=("Segoe UI", 11), bg="#e0e7ef", fg="#333", bd=0, relief="ridge", activebackground="#d0d7df", highlightthickness=0)
    switch_btn.pack(pady=5, ipadx=2, ipady=1)

    entry_user.bind('<Return>', lambda e: do_login())
    entry_pw.bind('<Return>', lambda e: do_login())
    entry_pw2.bind('<Return>', lambda e: do_register())

    auth_win.mainloop()

# --- Chat GUI ---
def start_chat(username):
    def receive():
        buffer = ""
        while True:
            try:
                data = client.recv(1024).decode()
                if not data:
                    break
                buffer += data
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if line.startswith("PM|"):
                        _, sender, msg = line.split("|", 2)
                        save_pm(username, sender, msg)
                        continue
                    msg = decrypt_message(line, KEY)
                    chat_box.config(state='normal')
                    chat_box.insert(tk.END, f"{msg}\n")
                    chat_box.config(state='disabled')
                    chat_box.see(tk.END)
            except:
                break

    def send_msg():
        msg = msg_entry.get()
        if not msg.strip():
            return
        encrypted = encrypt_message(msg, KEY)
        client.send(encrypted.encode())
        msg_entry.delete(0, tk.END)

    window = tk.Tk()
    window.title(f"🛡️ Encrypted Chat - {username}")
    window.geometry("700x700")  # Größer
    window.configure(bg="#f0f4fa")

    chat_frame = tk.Frame(window, bg="#f0f4fa")
    chat_frame.pack(expand=True, fill='both', padx=18, pady=(18,0))

    chat_box = tk.Text(chat_frame, state='disabled', wrap='word', font=("Segoe UI", 13), bg="#eaf1fb", fg="#222", bd=0, relief="flat")
    chat_box.pack(side='left', expand=True, fill='both', padx=(0,2), pady=0, ipadx=6, ipady=6)

    scrollbar = tk.Scrollbar(chat_frame, command=chat_box.yview)
    scrollbar.pack(side='right', fill='y')
    chat_box.config(yscrollcommand=scrollbar.set)

    entry_frame = tk.Frame(window, bg="#f0f4fa")
    entry_frame.pack(fill='x', padx=18, pady=18)

    msg_entry = tk.Entry(entry_frame, font=("Segoe UI", 13), bd=2, relief="groove")
    msg_entry.pack(side='left', fill='x', expand=True, padx=(0, 12), ipady=6)

    def on_enter(event):
        send_msg()

    msg_entry.bind('<Return>', on_enter)

    send_button = tk.Button(entry_frame, text="Send", command=send_msg, font=("Segoe UI", 13, "bold"), bg="#4f8cff", fg="white", bd=0, relief="ridge", activebackground="#357ae8", activeforeground="white", highlightthickness=0)
    send_button.pack(side='right', ipadx=12, ipady=4)

    tk.Button(window, text="Zurück zum Hauptmenü", command=lambda: [window.destroy(), show_homescreen(username)],
              font=("Segoe UI", 12, "bold"), bg="#e0e7ef", fg="#333", bd=0, relief="ridge", activebackground="#d0d7df").pack(pady=8, ipadx=2, ipady=1)

    threading.Thread(target=receive, daemon=True).start()
    window.mainloop()

def show_favorites(username, parent_win=None):
    if parent_win:
        parent_win.destroy()
    fav_win = tk.Toplevel()
    fav_win.title("Favoriten")
    fav_win.geometry("500x500")
    fav_win.configure(bg="#f0f4fa")
    font_label = ("Segoe UI", 12)
    tk.Label(fav_win, text="Deine Lieblingsserver", font=("Segoe UI", 15, "bold"), bg="#f0f4fa").pack(pady=(12, 8))
    listbox = tk.Listbox(fav_win, font=font_label, width=60, height=18)
    listbox.pack(padx=12, pady=8, fill="both", expand=True)

    def refresh():
        listbox.delete(0, tk.END)
        for fid, name, ip in load_favorites():
            listbox.insert(tk.END, f"{name} ({ip})")

    def add_fav():
        def save_new():
            name = entry_name.get().strip()
            ip = entry_ip.get().strip()
            if not name or not ip:
                msg_label.config(text="Name und IP angeben!")
                return
            add_favorite(name, ip)
            win.destroy()
            refresh()
        win = tk.Toplevel(fav_win)
        win.title("Favorit hinzufügen")
        win.geometry("350x180")
        win.configure(bg="#f0f4fa")
        tk.Label(win, text="Name:", font=font_label, bg="#f0f4fa").pack(pady=(18,2))
        entry_name = tk.Entry(win, font=font_label)
        entry_name.pack(pady=2)
        tk.Label(win, text="IP:", font=font_label, bg="#f0f4fa").pack(pady=(10,2))
        entry_ip = tk.Entry(win, font=font_label)
        entry_ip.pack(pady=2)
        msg_label = tk.Label(win, text="", fg="red", bg="#f0f4fa", font=font_label)
        msg_label.pack()
        tk.Button(win, text="Add", command=save_new, font=font_label, bg="#4f8cff", fg="white", bd=0).pack(pady=8)
        entry_ip.bind('<Return>', lambda e: save_new())

    def delete_selected():
        sel = listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        favs = load_favorites()
        favid = favs[idx][0]
        delete_favorite(favid)
        refresh()

    def connect_selected():
        sel = listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        favs = load_favorites()
        name, ip = favs[idx][1], favs[idx][2]
        fav_win.destroy()
        connect_and_start_chat(username, user_password, ip)

    btn_frame = tk.Frame(fav_win, bg="#f0f4fa")
    btn_frame.pack(pady=8)
    tk.Button(btn_frame, text="Hinzufügen", command=add_fav, font=font_label, bg="#4f8cff", fg="white", bd=0).pack(side='left', padx=4)
    tk.Button(btn_frame, text="Löschen", command=delete_selected, font=font_label, bg="#e0e7ef", bd=0).pack(side='left', padx=4)
    tk.Button(btn_frame, text="Verbinden", command=connect_selected, font=font_label, bg="#4f8cff", fg="white", bd=0).pack(side='left', padx=4)
    tk.Button(btn_frame, text="Zurück", command=fav_win.destroy, font=font_label, bg="#e0e7ef", bd=0).pack(side='left', padx=4)
    refresh()

if __name__ == "__main__":
    # Root-Fenster erzeugen und verstecken
    root = tk.Tk()
    root.withdraw()
    show_auth_window()
