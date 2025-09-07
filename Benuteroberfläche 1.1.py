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
APP_PATH = r"C:\Tag Maschine\Tag Maschine\RFID_Programmer.exe"
APP_DIR = os.path.dirname(APP_PATH)

RASPI_HOST = "192.168.0.26"
RASPI_USER = "beat"
RASPI_PASS = "1234"
REMOTE_SCRIPT_DIR = "/home/beat/Documents"  # z.B. links_drehen.py, rechts_drehen.py, bewegung_rfid_test.py

# PyAutoGUI Settings
pyautogui.FAILSAFE = False     # Fail-Safe deaktivieren (sonst Abbruch bei Maus oben/links)
pyautogui.PAUSE = 0.0     
#pyautogui.PAUSE = None    # gemächlich tippen

# =========================
# Hilfsfunktionen
# =========================

# ---- SSH-Helfer ----
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


def run_selection_sequence(selection: str):
    """Tastenabfolge für den gewählten Reagenztyp (Stil wie im Screenshot)."""
    sel = selection.strip()
    
    old_pause = pyautogui.PAUSE
    pyautogui.PAUSE = 0.5                                                           

    if sel == "Washbuffer":
        pyautogui.press('right', presses=9) 
        pyautogui.press('enter')
        pyautogui.press('tab', presses=7)
        pyautogui.press('down', presses=6)
        pyautogui.press('enter')
        pyautogui.press('tab', presses=16)
        

    elif sel == "Lysis":
        pyautogui.press('right', presses=9) 
        pyautogui.press('enter')
        pyautogui.press('tab', presses=7)
        pyautogui.press('down', presses=3)
        pyautogui.press('enter')
        pyautogui.press('tab', presses=16)

    elif sel == "Diluent":
        pyautogui.press('right', presses=9) 
        pyautogui.press('enter')
        pyautogui.press('tab', presses=7)
        pyautogui.press('down', presses=2)
        pyautogui.press('enter')
        pyautogui.press('tab', presses=16)

    elif sel == "CMR +":
        pyautogui.press('right', presses=9) 
        pyautogui.press('enter')
        pyautogui.press('tab', presses=7)
        pyautogui.press('down', presses=1)
        pyautogui.press('enter')
        pyautogui.press('tab', presses=16)

    elif sel == "CMR -":
        pyautogui.press('right', presses=9) 
        pyautogui.press('enter')
        pyautogui.press('tab', presses=7)
        pyautogui.press('down', presses=1)
        pyautogui.press('up', presses=1)
        pyautogui.press('enter')
        pyautogui.press('tab', presses=16)

    elif sel == "MGP":
        pyautogui.press('right', presses=9) 
        pyautogui.press('enter')
        pyautogui.press('tab', presses=7)
        pyautogui.press('down', presses=4)
        pyautogui.press('enter')
        pyautogui.press('tab', presses=16)

    elif sel == "Reagent":
        pyautogui.press('right', presses=9) 
        pyautogui.press('enter')
        pyautogui.press('tab', presses=5)
        pyautogui.press('down', presses=6)
        pyautogui.press('enter')
        pyautogui.press('tab', presses=16)
    else:
        print(f"Unbekannte Option: {sel}")

    

def Beschriftungs_Sequenz(n: int):
    """Wiederholt n-mal: Tab → Enter → Tab → Enter."""
    for _ in range(n):
        time.sleep(3.0)
        pyautogui.press('enter')
        time.sleep(6)  # Wartezeit für Beschriftung
        ssh_run(ssh_client, "bewegung_rfid_test.py")
        time.sleep(2.0)
        pyautogui.press('tab', presses=15)
        time.sleep(1.0)
    pyautogui.press('tab', presses=5)

    
    ssh_start_bg(ssh_client, "Links_drehen.py")
    time.sleep(5.0)              # Motor laufen lassen
    ssh_run(ssh_client, "motor_stop.py")  # Motoren stoppen/stromlos
    print("Links-Drehen beendet. Motoren gestoppt.")
#Platzhalter für deine weiteren Start-Schritte ----



# =========================
# GUI
# =========================
root = tk.Tk()
root.title("Start")

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

# --- NEU: Hintergrundprozess starten & PID zurückgeben
def ssh_start_bg(client: paramiko.SSHClient, script_name: str):
    """
    Startet remote 'python3 <script> &' und gibt die PID (int) zurück,
    oder None bei Fehler.
    """
    if not client: 
        print("Kein SSH-Client verfügbar.")
        return None
    try:
        cmd = f"python3 {REMOTE_SCRIPT_DIR}/{script_name} >/dev/null 2>&1 & echo $!"
        stdin, stdout, stderr = client.exec_command(cmd)
        pid_str = stdout.read().decode('utf-8', errors='ignore').strip()
        err = stderr.read().decode('utf-8', errors='ignore').strip()
        if err:
            print(f"[ssh_start_bg ERR] {err}")
        try:
            pid = int(pid_str)
            print(f"[ssh_start_bg] {script_name} gestartet, PID={pid}")
            return pid
        except Exception:
            print(f"[ssh_start_bg] Konnte PID nicht lesen: '{pid_str}'")
            return None
    except Exception as e:
        print(f"[ssh_start_bg] Fehler: {e}")
        return None

# --- NEU: Prozess per PID beenden
def ssh_kill_pid(client: paramiko.SSHClient, pid: int, signal="TERM"):
    if not client or not pid:
        return
    try:
        cmd = f"kill -{signal} {pid}"
        client.exec_command(cmd)
        print(f"[ssh_kill_pid] kill -{signal} {pid} gesendet")
    except Exception as e:
        print(f"[ssh_kill_pid] Fehler: {e}")

# --- NEU: Sicherheitshalber nach Scriptnamen killen
def ssh_pkill_script(client: paramiko.SSHClient, script_name: str):
    if not client:
        return
    try:
        cmd = f"pkill -f '{REMOTE_SCRIPT_DIR}/{script_name}'"
        client.exec_command(cmd)
        print(f"[ssh_pkill_script] pkill -f {script_name} gesendet")
    except Exception as e:
        print(f"[ssh_pkill_script] Fehler: {e}")


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

    # ======== Pfeil-Buttons (gedrückt halten => drehen; loslassen => stoppen) ========
    # Merker für laufenden Remote-Prozess (PID + welcher Scriptname)
    current_pid = {"name": None, "pid": None}

    def _stop_running_motion():
        """Aktiven Drehprozess sicher beenden + motor_stop aufrufen."""
        # 1) Falls ein PID bekannt ist: killen
        if current_pid["pid"]:
            ssh_kill_pid(ssh_client, current_pid["pid"], signal="TERM")
            # optional nachhaken:
            ssh_kill_pid(ssh_client, current_pid["pid"], signal="KILL")
        # 2) Sicherheitshalber nach Scriptnamen killen
        if current_pid["name"]:
            ssh_pkill_script(ssh_client, current_pid["name"])
        # 3) Motoren wirklich stoppen/stromlos
        ssh_run(ssh_client, "motor_stop.py")
        # 4) Merker leeren
        current_pid["name"] = None
        current_pid["pid"] = None

    # HINWEIS: Deine Datei heißt vermutlich 'rechts_drehen.py' (ohne 's').
    # In deinem Code steht 'rechts_drehen.py'. Bitte ggf. anpassen:
    SCRIPT_LEFT  = "links_drehen.py"
    SCRIPT_RIGHT = "rechts_drehen.py"   # <- falls deine Datei so heißt!

    # --- LEFT Button
    def on_left_press(event):
        # Optik: gedrückt darstellen
        btn_left.config(relief="sunken", state="active")
        # Falls bereits was läuft: stoppen
        _stop_running_motion()
        # Start links drehen als Hintergrundprozess
        pid = ssh_start_bg(ssh_client, SCRIPT_LEFT)
        current_pid["name"] = SCRIPT_LEFT
        current_pid["pid"]  = pid

    def on_left_release(event):
        btn_left.config(relief="raised", state="normal")
        _stop_running_motion()

    btn_left = tk.Button(menu_win, text="←", font=("Arial", 12, "bold"), width=4)
    btn_left.bind("<ButtonPress-1>", on_left_press)
    btn_left.bind("<ButtonRelease-1>", on_left_release)
    btn_left.pack(side=tk.LEFT, padx=20, pady=10)

    # --- RIGHT Button
    def on_right_press(event):
        btn_right.config(relief="sunken", state="active")
        _stop_running_motion()
        pid = ssh_start_bg(ssh_client, SCRIPT_RIGHT)
        current_pid["name"] = SCRIPT_RIGHT
        current_pid["pid"]  = pid

    def on_right_release(event):
        btn_right.config(relief="raised", state="normal")
        _stop_running_motion()

    btn_right = tk.Button(menu_win, text="→", font=("Arial", 12, "bold"), width=4)
    btn_right.bind("<ButtonPress-1>", on_right_press)
    btn_right.bind("<ButtonRelease-1>", on_right_release)
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



        # Wiederholt Tab/Enter
        Beschriftungs_Sequenz(n)

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


