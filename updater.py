import os
import time
import requests
import shutil
import subprocess
import ctypes
import sys
import subprocess


def restart_client():
    print("Starte Client...")
    subprocess.Popen([CLIENT_PATH])
    sys.exit()  # statt exit()

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    # Neustart mit Adminrechten
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, " ".join(sys.argv), None, 1
    )
    sys.exit()


# URLs zur neuesten Version (Client & Version)
UPDATE_URL = "https://github.com/lelewithheart/chatter/raw/refs/heads/main/dist/client.exe"
VERSION_URL = "https://raw.githubusercontent.com/lelewithheart/chatter/refs/heads/main/version.txt"

CLIENT_PATH = "client.exe"
NEW_CLIENT_PATH = "client_new.exe"
VERSION_PATH = "version.txt"
NEW_VERSION_PATH = "version_new.txt"

def download_new_client():
    print("Lade neue Version herunter...")
    r = requests.get(UPDATE_URL, stream=True)
    with open(NEW_CLIENT_PATH, "wb") as f:
        shutil.copyfileobj(r.raw, f)
    print("Client.exe heruntergeladen.")

def download_version_file():
    print("Lade neue Versionsdatei herunter...")
    r = requests.get(VERSION_URL)
    with open(NEW_VERSION_PATH, "w", encoding="utf-8") as f:
        f.write(r.text.strip())
    print("version.txt heruntergeladen.")

def replace_files():
    # Falls alte Client.exe noch nicht geschlossen -> etwas warten
    time.sleep(2)

    # Client ersetzen
    if os.path.exists(CLIENT_PATH):
        os.remove(CLIENT_PATH)
    os.rename(NEW_CLIENT_PATH, CLIENT_PATH)
    print("Client aktualisiert.")

    # Version.txt ersetzen
    if os.path.exists(VERSION_PATH):
        os.remove(VERSION_PATH)
    os.rename(NEW_VERSION_PATH, VERSION_PATH)
    print("Versionsdatei aktualisiert.")

if __name__ == "__main__":
    download_new_client()
    download_version_file()
    replace_files()
    restart_client()
