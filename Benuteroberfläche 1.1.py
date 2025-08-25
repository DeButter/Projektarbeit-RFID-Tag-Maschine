# -*- coding: utf-8 -*-
# RFID Programmer GUI – Windows 11
# - Tkinter-GUI
# - pyautogui für Tastenabfolgen
# - pygetwindow + Win32-API für zuverlässigen Fokus
# - Paramiko (SSH) statt Sockets für Raspberry Pi
#
# Installation:
#   pip install pyautogui pygetwindow paramiko
# (ggf. Script als Administrator starten, wenn das Zielprogramm mit Admin-Rechten läuft)

import tkinter as tk
import subprocess
import os
import time
import ctypes
import paramiko
import pyautogui
import pygetwindow as gw

# =========================
# Konfiguration
# =========================
APP_PATH = r"A:\RFID Software\RFID Software\RFID_Programmer.exe"
APP_DIR = os.path.dirname(APP_PATH)

RASPI_HOST = "192.168.0.26"
RASPI_USER = "beat"
RASPI_PASS = "1234"
REMOTE_SCRIPT_DIR = "/home/beat/Documents"  # z.B. links_drehen.py, rechts_drehen.py, bewegung_rfid.py

# PyAutoGUI Settings
pyautogui.FAILSAFE = False     # Fail-Safe deaktivieren (sonst Abbruch bei Maus oben/links)
pyautogui.PAUSE = 1.0         # gemächlich tippen

# =========================
# Hilfsfunktionen
# =========================

def find_and_focus_window(preferred_title=None, retries=25, sleep_between=0.4):
    """
    Sucht wiederholt nach dem Fenster, holt es in den Vordergrund,
    klickt hinein (damit der Fokus sicher dort ist) und gibt das Window-Objekt zurück.
    """
    for _ in range(retries):
        titles = [t for t in gw.getAllTitles() if t and t.strip()]
        win = None
        try:
            if preferred_title:
                matches = gw.getWindowsWithTitle(preferred_title)
                if matches:
                    win = matches[0]
            if not win:
                # Fallback: nimm das zuletzt hinzugekommene sinnvolle Fenster
                # (Heuristik – bei Bedarf anpassen)
                if titles:
                    win = gw.getWindowsWithTitle(titles[-1])[0]
        except Exception:
            win = None

        if win:
            try:
                if win.isMinimized:
                    win.restore()
                win.activate()
                time.sleep(0.25)
                # Windows-API zusätzlich nutzen
                try:
                    ctypes.windll.user32.SetForegroundWindow(win._hWnd)
                except Exception:
                    pass
                # In das Fenster klicken, damit Eingabefokus garantiert ist
                x = win.left + min(60, max(10, win.width // 10))
                y = win.top + min(60, max(10, win.height // 10))
                pyautogui.click(x, y)
                time.sleep(0.25)
                return win
            except Exception:
                pass
        time.sleep(sleep_between)
    return None

def run_selection_sequence(selection: str):
    """Tastenabfolge für den gewählten Reagenztyp (Stil wie im Screenshot)."""
    sel = selection.strip()
    if sel == "Washbuffer":
        pyautogui.press('enter')
        pyautogui.press('tab', presses=7)
        pyautogui.press('down', presses=6)
        pyautogui.press('enter')
        pyautogui.press('tab', presses=4)
        pyautogui.press('down', presses=6)
        pyautogui.press('enter')
        pyautogui.press('down', presses=6)
        pyautogui.press('down', presses=6)
    elif sel == "Lysis":
        pyautogui.press('enter')
        pyautogui.press('tab', presses=7)
        pyautogui.press('down', presses=3)
        pyautogui.press('enter')
    elif sel == "Diluent":
        pyautogui.press('enter')
        pyautogui.press('tab', presses=7)
        pyautogui.press('down', presses=2)
        pyautogui.press('enter')
    elif sel == "CMR +":
        pyautogui.press('enter')
        pyautogui.press('tab', presses=7)
        pyautogui.press('down', presses=1)
        pyautogui.press('enter')
    elif sel == "CMR -":
        pyautogui.press('enter')
        pyautogui.press('tab', presses=7)
        pyautogui.press('enter')
    elif sel == "MGP":
        pyautogui.press('enter')
        pyautogui.press('tab', presses=7)
        pyautogui.press('down', presses=4)
        pyautogui.press('enter')
    elif sel == "Reagent":
        pyautogui.press('enter')
        pyautogui.press('tab', presses=7)
        pyautogui.press('down', presses=5)
        pyautogui.press('enter')
    else:
        print(f"Unbekannte Option: {sel}")

def run_repeated_tab_enter(n: int):
    """Wiederholt n-mal: Tab → Enter → Tab → Enter."""
    for _ in range(n):
        pyautogui.press('tab')
        pyautogui.press('enter')
        pyautogui.press('tab')
        pyautogui.press('enter')

# ---- Platzhalter für deine weiteren Start-Schritte ----

def reader_auswaehlen():
    """TODO: Eigene Tastenabfolge für 'Reader auswählen' hier einsetzen."""
    # Beispiel (löschen/ersetzen):
    # pyautogui.press('tab', presses=3)
    # pyautogui.press('enter')
    pass

def reader_oeffnen_sequence():
    """Deine Sequenz direkt nach dem Fensterausrichten:
       7x Tab, 1x Down, 9x Tab, Enter, 11x Tab, Enter."""
    pyautogui.press('tab', presses=7, interval=0.08)
    pyautogui.press('down', presses=1)
    pyautogui.press('tab', presses=9, interval=0.08)
    pyautogui.press('enter')
    time.sleep(0.15)
    pyautogui.press('tab', presses=11, interval=0.08)
    pyautogui.press('enter')

def antenne_auswaehlen():
    """TODO: Eigene Tastenabfolge für 'Antenne auswählen' hier einsetzen."""
    # Beispiel (löschen/ersetzen):
    # pyautogui.press('tab', presses=2)
    # pyautogui.press('enter')
    pass

# ---- SSH-Helfer ----

def ssh_connect():
    """Stellt eine SSH-Verbindung zum Raspberry Pi her und gibt den Client zurück (oder None)."""
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=RASPI_HOST, username=RASPI_USER, password=RASPI_PASS, timeout=6)
        print(f"SSH verbunden: {RASPI_USER}@{RASPI_HOST}")
        return client
    except Exception as e:
        print(f"SSH-Verbindung fehlgeschlagen: {e}")
        return None

def ssh_run(client: paramiko.SSHClient, script_name: str):
    """Führt ein Python-Skript auf dem Raspberry Pi aus."""
    if not client:
        print("Kein SSH-Client verfügbar.")
        return
    try:
        cmd = f"python3 {REMOTE_SCRIPT_DIR}/{script_name}"
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode('utf-8', errors='ignore').strip()
        err = stderr.read().decode('utf-8', errors='ignore').strip()
        if out:
            print(f"[SSH OUT] {out}")
        if err:
            print(f"[SSH ERR] {err}")
    except Exception as e:
        print(f"SSH-Ausführung fehlgeschlagen ({script_name}): {e}")

# =========================
# GUI
# =========================

root = tk.Tk()
root.title("Start")

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

def launch_menu():
    """Start 1:
       - Software starten
       - Fenster finden/fokussieren/ausrichten
       - (direkt danach) Reader öffnen (deine Sequenz)
       - SSH-Verbindung herstellen
       - Menü öffnen
       - Reader auswählen (Platzhalter)
       - Antenne auswählen (Platzhalter)
    """
    global ssh_client, process, menu_win, option_var, entry_count, program_window_title

    # 1) Software starten
    try:
        if not os.path.isfile(APP_PATH):
            raise FileNotFoundError(f"EXE nicht gefunden: {APP_PATH}")
        process = subprocess.Popen([APP_PATH], cwd=APP_DIR)
        time.sleep(2.0)  # Splash/Start abwarten
    except Exception as e:
        print(f"Fehler beim Starten der Anwendung: {e}")
        return

    # 2) Fenster finden/fokussieren
    program_window_title = "Roche RFID Programmer SW"  # falls bekannt, ansonsten auto
    prog_win = find_and_focus_window(program_window_title, retries=25, sleep_between=0.4)
    if not prog_win:
        print("Programmfenster konnte nicht fokussiert werden – Abbruch.")
        return

    # links andocken / ggf. Größe anpassen (optional)
    try:
        prog_width, prog_height = prog_win.size.width, prog_win.size.height
        prog_win.moveTo(0, 0)
        if prog_width > screen_width // 2:
            new_width = screen_width // 2
            new_height = min(prog_height, screen_height)
            prog_win.resizeTo(new_width, new_height)
            prog_width = new_width
    except Exception as e:
        print(f"Fensteranpassung fehlgeschlagen: {e}")
        prog_width = screen_width // 2

    # >>> Direkt nach dem Aktivieren: Reader öffnen (deine Sequenz)
    reader_oeffnen_sequence()
    time.sleep(0.3)

    # 3) SSH aufbauen
    ssh_client = ssh_connect()

    # 4) Menü-Fenster öffnen (rechts daneben platzieren)
    menu_win = tk.Tk()
    menu_win.title("Menü")
    menu_width = 420
    menu_height = 320
    menu_x = (prog_win.width if prog_win else screen_width // 2) + 50
    menu_y = 50
    menu_win.geometry(f"{menu_width}x{menu_height}+{menu_x}+{menu_y}")

    # 5) Reader auswählen (Platzhalter für deine Sequenz)
    try:
        reader_auswaehlen()
    except Exception as e:
        print(f"Fehler bei 'Reader auswählen': {e}")

    # 6) Antenne auswählen (Platzhalter für deine Sequenz)
    try:
        antenne_auswaehlen()
    except Exception as e:
        print(f"Fehler bei 'Antenne auswählen': {e}")

    # ======= Menü-Elemente =======

    # Dropdown für Reagenztyp
    option_var = tk.StringVar(menu_win)
    option_var.set("Bitte wählen")
    options = ["Bitte wählen", "Washbuffer", "Lysis", "Diluent", "CMR +", "CMR -", "Reagent", "MGP"]
    dropdown = tk.OptionMenu(menu_win, option_var, *options)
    dropdown.config(width=20)
    dropdown.pack(pady=10)

    # Eingabefeld für Anzahl
    entry_count = tk.Entry(menu_win, width=6)
    entry_count.insert(0, "1")
    entry_count.pack(pady=5)

    # Pfeil-Buttons (SSH)
    def send_left():
        ssh_run(ssh_client, "links_drehen.py")

    def send_right():
        ssh_run(ssh_client, "rechts_drehen.py")

    btn_left = tk.Button(menu_win, text="←", font=("Arial", 12, "bold"), command=send_left)
    btn_right = tk.Button(menu_win, text="→", font=("Arial", 12, "bold"), command=send_right)
    btn_left.pack(side=tk.LEFT, padx=20, pady=10)
    btn_right.pack(side=tk.LEFT, padx=20, pady=10)

    # Start-Button im Menü
    def start_sequence():
        selection = option_var.get()
        if selection == "Bitte wählen":
            print("Bitte eine gültige Option wählen.")
            return
        try:
            n = int(entry_count.get())
        except ValueError:
            print("Ungültige Anzahl. Bitte 1–100 eingeben.")
            return
        if n < 1 or n > 100:
            print("Ungültige Anzahl. Bitte 1–100 eingeben.")
            return

        # Fokus sicherstellen
        win = find_and_focus_window(program_window_title, retries=5, sleep_between=0.2)
        if not win:
            print("Fensterfokus fehlgeschlagen.")
            return

        # Sequenz für Reagenztyp
        run_selection_sequence(selection)

        # Bewegung auf dem Pi starten (SSH)
        ssh_run(ssh_client, "bewegung_rfid.py")

        # Wiederholt Tab/Enter
        run_repeated_tab_enter(n)

        print("Sequenz abgeschlossen.")

    btn_start_menu = tk.Button(menu_win, text="Start", font=("Arial", 12), command=start_sequence)
    btn_start_menu.pack(pady=20)

    # Beenden-Button
    def exit_app():
        if ssh_client:
            try:
                ssh_client.close()
            except Exception:
                pass
        try:
            process.terminate()
        except Exception:
            pass
        try:
            menu_win.destroy()
        except Exception:
            pass
        print("Anwendung beendet.")

    btn_exit = tk.Button(menu_win, text="Beenden", command=exit_app)
    btn_exit.pack(pady=5)

    # Startfenster schließen
    root.destroy()

# Start-Button (Start 1)
start_btn = tk.Button(root, text="Start", font=("Arial", 14, "bold"), command=launch_menu)
start_btn.pack(padx=50, pady=50)

root.mainloop()
