# Chatter

## Übersicht

Dieses Projekt ist ein verschlüsseltes Chat-System in Python. Es besteht aus einem Client ([client.py](client.py)), einer Verschlüsselungsbibliothek ([cipher.py](cipher.py)), einem zentralen Hauptserver und beliebig vielen dezentralen Chat-Server-Instanzen.

---

## Komponenten

- [`client.py`](client.py): Der Chat-Client (benötigt auch [`cipher.py`](cipher.py))
- [`cipher.py`](cipher.py): Verschlüsselungsfunktionen für Nachrichten
- [`server.py`](server.py): **Der zentrale Main Server**  
  - Verantwortlich für Login, Registrierung und Benutzerverwaltung
  - Vermittelt zwischen Clients und Chat-Instanzen
- [`server-instance.py`](server-instance.py): **Dezentrale Chat-Server-Instanz**  
  - Jeder kann damit einen eigenen Gruppenchat-Server hosten (z.B. mit Port-Forwarding)
  - Verbindet sich mit dem Main Server für Authentifizierung

---

## Was wird benötigt?

- **Python 3.8+**
- Für den Chat-Client: [`client.py`](client.py) und [`cipher.py`](cipher.py)
- Für den Main Server: [`server.py`](server.py) und [`cipher.py`](cipher.py)
- Für eigene Gruppenchat-Server: [`server-instance.py`](server-instance.py) und [`cipher.py`](cipher.py)

---

## Wie funktioniert das System?

1. **Main Server (`server.py`)**
   - Starten mit:
     ```sh
     python server.py
     ```
   - Verwaltet Benutzerkonten (Login/Registrierung)
   - Muss dauerhaft online sein, damit sich Clients und Instanzen authentifizieren können

2. **Chat-Instanz (`server-instance.py`)**
   - Jeder Nutzer kann eine eigene Instanz starten, z.B. für einen privaten Gruppenchat:
     ```sh
     python server-instance.py
     ```
   - Instanzen können öffentlich (mit Port-Forwarding) oder im lokalen Netzwerk betrieben werden
   - Authentifizierung erfolgt über den Main Server

3. **Client**
   - Starten mit:
     ```sh
     python client.py
     ```
   - Verbindet sich zuerst mit dem Main Server für Login/Registrierung
   - Danach Auswahl oder Eingabe einer Chat-Instanz (Server), um zu chatten

---

## Wichtige Hinweise

- **Der Main Server (`server.py`) ist zwingend erforderlich** für Login und Benutzerverwaltung!
- **`server-instance.py` ist für dezentrale Gruppen-Chats** – jeder kann damit einen eigenen Chat-Server hosten.
- **Ohne Main Server ist keine Anmeldung möglich!**
- **`client.py` und `cipher.py` werden immer benötigt**, egal ob du chattest oder einen Server betreibst.

---

## Zusammenfassung

- **Zum Chatten brauchst du:** [`client.py`](client.py) und [`cipher.py`](cipher.py)
- **Zum Hosten eines eigenen Gruppenchats:** [`server-instance.py`](server-instance.py) und [`cipher.py`](cipher.py)
- **Der zentrale Login läuft immer über den Main Server (`server.py`)** – ohne ihn keine Anmeldung!