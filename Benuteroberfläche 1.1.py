# -*- coding: utf-8 -*-  # Encoding-Angabe (UTF-8) für Umlaute im Skript
# Der nachfolgende Code erstellt eine GUI die es ermöglicht eine externe Anwendung zu starten und zu bedienen.
# Zusätzlich wird eine SSH-Verbindung zu einem Raspberry Pi hergestellt, um dort Skripte auszuführen.
# Die GUI bietet Optionen zur Auswahl eines Consumables und einer Anzahl, sowie Pfeil-Buttons zum Steuern von Motoren.

# Installation der benötigten Bibliotheken:
#   pip install pyautogui pygetwindow paramiko



import tkinter as tk        # Wird dafür eine verwendete eine graphische Oberfläche (GUI) zu erstellen.
import subprocess           # Ermöglicht das Starten externer Prozesse (z.B. die RFID-Programmer.exe).  
import os                   # Wird für Dateipfade und Betriebssysteminteraktionen verwendet.
import time                 # Ermöglicht das Einfügen von Wartezeiten im Code.
import ctypes               # Ermöglicht den Zugriff auf Windows-API-Funktionen (z.B. Fenster in den Vordergrund bringen).
import paramiko             # Bibliothek zur Herstellung von SSH-Verbindungen und Ausführung von Befehlen auf entfernten Maschinen.
import pyautogui            # Bibliothek zur Automatisierung von Tastatur- und Mausaktionen.
import pygetwindow as gw    # Bibliothek zum Verwalten und Interagieren mit Anwendungsfenstern.

# =========================
# Konfiguration 
# =========================
APP_PATH = r"C:\Tag Maschine\Tag Maschine\RFID_Programmer.exe"       # Pfad zur RFID_Programmer-Anwendung (EXE-Datei)
APP_DIR = os.path.dirname(APP_PATH)                                  # Verzeichnis der Anwendung (Arbeitsverzeichnis), dies ist nötig damit die EXE im Ordner ausgeführt wird.

RASPI_HOST = "192.168.0.26"                                         # IP-Adresse des Raspberry Pi
RASPI_USER = "beat"                                                 # Benutzername für SSH-Login auf Raspberry P
RASPI_PASS = "1234"                                                 # Passwort für SSH-Login
REMOTE_SCRIPT_DIR = "/home/beat/Documents"                          # Verzeichnis auf dem Raspberry Pi mit den Steuer-Skripten (z.B. links_drehen.py)

# PyAutoGUI Settings
pyautogui.FAILSAFE = False     # Fail-Safe deaktivieren (sonst Abbruch bei Maus oben/links)
pyautogui.PAUSE = 0.0          # Keine Pause zwischen pyautogui-Aktionen (für schnellere Eingabe), wurde momentan auf 0 gesetzt um die Pausen in den Funktionen zu steuern.


# =========================
# Hilfsfunktionen
# =========================

# ---- SSH-Helfer ----
def ssh_run(client: paramiko.SSHClient, script_name: str):          #Diese Funktion führt ein Skript auf dem Raspberry Pi über SSH aus und gibt die Ausgabe zurück. Sie wird später verwendet, um Befehle wie das Stoppen von Motoren auszuführen.
    if not client:                                                  
        print("Kein SSH-Client verfügbar.")                         # Falls kein SSH-Client vorhanden ist, wird eine Meldung ausgegeben und die Funktion beendet.
        return
    try:
        cmd = f"python3 {REMOTE_SCRIPT_DIR}/{script_name}"                              # Befehl zum Ausführen des Skripts auf dem Raspberry Pi.
        stdin, stdout, stderr = client.exec_command(cmd)                                # Der Befehl wird über die SSH-Verbindung ausgeführt.
        out = stdout.read().decode('utf-8', errors='ignore').strip()                    # Ausgabe des Befehls wird gelesen und dekodiert.              
        err = stderr.read().decode('utf-8', errors='ignore').strip()                    # Fehlerausgabe wird gelesen und dekodiert.
        if out:
            print(f"[SSH OUT] {out}")                                               # Falls es eine Ausgabe gibt, wird diese ausgegeben.  
        if err:
            print(f"[SSH ERR] {err}")                                               # Falls es eine Fehlerausgabe gibt, wird diese ausgegeben.    
    except Exception as e:
        print(f"SSH-Ausführung fehlgeschlagen ({script_name}): {e}")

def ssh_connect():                                                                                       # Diese Funktion stellt eine SSH-Verbindung zum Raspberry Pi her und gibt den SSH-Client zurück.
    try:
        client = paramiko.SSHClient()                                                                       # Erstellen eines SSH-Client-Objekts. Durch diese Klasse wird z.B connect() und exec_command() automatisch bereitgestellt. Mann muss nur Passowrt und Benutzername angeben.                 
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())                                        # Automatisches Akzeptieren unbekannter Host-Schlüssel (nicht sicher, aber praktisch für Tests).                    
        client.connect(hostname=RASPI_HOST, username=RASPI_USER, password=RASPI_PASS, timeout=6)            # Verbindungsaufbau mit den angegebenen Zugangsdaten und einem Timeout von 6 Sekunden.          
        print(f"SSH verbunden: {RASPI_USER}@{RASPI_HOST}")
        return client
    except Exception as e:
        print(f"SSH-Verbindung fehlgeschlagen: {e}")
        return None

def find_and_focus_window(preferred_title=None, retries=25, sleep_between=0.4):         # Diese Funktion sucht nach einem Fenster mit einem bestimmten Titel (oder dem zuletzt gefundenen Fenster) und bringt es in den Vordergrund.
    for _ in range(retries):
        titles = [t for t in gw.getAllTitles() if t and t.strip()]
        win = None
        try:
            if preferred_title:
                matches = gw.getWindowsWithTitle("Roche RFID Programmer SW")                       # Mann kann nach einem bestimmten Fenstertitel suchen. In meinem Fall "Roche RFID Programmer SW".
                if matches:
                    win = matches[0]
            if not win:
                if titles:
                    win = gw.getWindowsWithTitle(titles[-1])[0]                                     # Falls kein bevorzugter Titel angegeben ist, wird das zuletzt gefundene Fenster verwendet.
        except Exception:
            win = None

        if win:                                                                                     # Wenn ein Fenster gefunden wurde, wird versucht, es zu aktivieren und in den Vordergrund zu bringen.                 
            try:
                if win.isMinimized:
                    win.restore()
                win.activate()
                time.sleep(0.25)
                try:                                                                   # Durch die eine Windows-API-Funktion wird das Fenster in den Vordergrund gebracht.
                    ctypes.windll.user32.SetForegroundWindow(win._hWnd)                            
                except Exception:                                                      # Falls das nicht klappt, wird der Fehler ignoriert.
                    pass
                x = win.left + min(60, max(10, win.width // 10))                       # Ein Klick in das Fenster, um sicherzustellen, dass es den Fokus hat.
                y = win.top + min(60, max(10, win.height // 10))                       # Ein Klick in das Fenster, um sicherzustellen, dass es den Fokus hat.
                pyautogui.click(x, y)
                time.sleep(0.25)
                return win
            except Exception:                                                          # Falls das Aktivieren fehlschlägt, wird der Fehler ignoriert und ein neuer Versuch gestartet.
                pass
        time.sleep(sleep_between)
    return None


def reader_oeffnen_sequence():                                  # Diese Funktion führt eine Abfolge von Tastendrücken aus, um in der Anwendung den Reader zu öffnen.
    pyautogui.press('tab', presses=7, interval=0.08)            # Tab-Taste 7-mal drücken um zur Port-Auswahl zu gelangen.
    pyautogui.press('down', presses=1)                          # Einmal nach unten drücken um den Port Nr. 2 auszuwählen.  
    pyautogui.press('tab', presses=9, interval=0.08)            # Tab-Taste 9-mal drücken um zum "Reader öffnen" Button zu gelangen.
    pyautogui.press('enter')                                    # Enter drücken um den Reader zu öffnen.   
    time.sleep(0.15)                                            # Kurze Pause um sicherzustellen, dass der Reader geöffnet ist.  
    pyautogui.press('tab', presses=11, interval=0.08)           # Tab-Taste 11-mal drücken um zum Antenne 1 Button zu gelangen.
    pyautogui.press('enter')                                    # Enter drücken um Antenne 1 auszuwählen.


def auswahl_consumable(selection: str):                     # Diese Funktion führt eine Abfolge von Tastendrücken aus, basierend auf der Auswahl des Consumables. Die Tasteabfolge vaariert je nach ausgewähltem Consumable nur leicht, da die ersten Schritte gleich sind.
    sel = selection.strip()
    
    old_pause = pyautogui.PAUSE                             # Für diese Funktion eine Pause von 0.5 Sekunden zwischen den Aktionen einstellen.
    pyautogui.PAUSE = 0.5                                                           

    if sel == "Washbuffer":                                 # Wenn "Washbuffer" ausgewählt wurde, wird diese Abfolge von Tastendrücken ausgeführt.
        pyautogui.press('right', presses=9)                 # Rechts-Taste 9-mal drücken um zum Load Data Content Button zu gelangen.
        pyautogui.press('enter')                            # Enter drücken um den Load Data Content Button zu aktivieren.
        pyautogui.press('tab', presses=7)                   # Tab-Taste 7-mal drücken um in die Datein-Auswahl zu gelangen.
        pyautogui.press('down', presses=6)                  # Sechs mal nach unten drücken um "Washbuffer" auszuwählen.
        pyautogui.press('enter')                            # Enter drücken um "Washbuffer" auszuwählen.
        pyautogui.press('tab', presses=16)                  # Tab-Taste 16-mal drücken um zum New RFID Button zu gelangen. Und somit ist die Vorbereitung für den Programmierprozess abgeschlossen.                            
        

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

    

def Beschriftungs_Sequenz(n: int):                                      # Hier wird die Funktion definiert welche eine mischung von Tastenabfolgen und SSH-Befehlen ausführt. Sie wird gemäss der Eingabe n-mal wiederholt. Die Eingabe n wird später im GUI-Fenster abgefragt.
    for _ in range(n):
        time.sleep(1.0)
        pyautogui.press('enter')                                        # Enter drücken um den New RFID Button zu aktivieren.
        time.sleep(6)                                                   # Warten bis der Programmierprozess abgeschlossen ist.
        ssh_run(ssh_client, "bewegung_rfid_test.py")                    # Über SSH das Skript bewegung_rfid_test.py auf dem Raspberry Pi ausführen.
        time.sleep(2.0)                                                 # Warten bis die Bewegung abgeschlossen ist.
        pyautogui.press('tab', presses=15)                              # Tab-Taste 15-mal drücken um zum New RFID Button Button zu gelangen.
        time.sleep(1.0)                                                 # Kurze Pause um sicherzustellen, dass der Fokus gesetzt ist. 
    pyautogui.press('tab', presses=18)                                  # Tab-Taste 18-mal drücken um zum Antenne 1 Button zu gelangen. Damit ist die Anwendung wieder im Ausgangszustand ist.

    
    ssh_start_bg(ssh_client, "links_drehen.py")                         # Nachdem die Schleife abgeschlossen ist, wird das Skript links_drehen.py gestartet damit das RFID-Band zum Ausgangspunkt gebracht wird und dort vom User entnommen werden kann.
    time.sleep(12.0)                                                    # Diese Zeit braucht es damit das RFID-Band in der Ausgangsposition ankommt.  
    ssh_run(ssh_client, "motor_stop.py")                                # Zum Schluss werden die Motoren gestoppt damit sie keinen Strom mehr verbrauchen.
    print("Links-Drehen beendet. Motoren gestoppt.")




# =========================
# GUI
# =========================
root = tk.Tk()                                                                       # Hier wird das Hauptfenster der GUI erstellt.
root.title("Start")                                                                  # Der Titel des Fensters wird auf "Start" gesetzt.

screen_width = root.winfo_screenwidth()                                             # Bildschirmbreite und -höhe werden ermittelt, um Fensterpositionen später berechnen zu können.
screen_height = root.winfo_screenheight()                                           

# Durch die folgenden 3 Funktionen wird dafür gesorgt das Skripte sauber im Hintergrund gestartet und gestoppt werden können.
def ssh_start_bg(client: paramiko.SSHClient, script_name: str):                                 # Diese Funktion startet ein Skript auf dem Raspberry Pi im Hintergrund und gibt die Prozess-ID (PID) zurück. Durch die PID kann der Prozess später gezielt beendet werden.
    if not client:
        print("Kein SSH-Client verfügbar.")
        return None
    try:
        cmd = f"python3 {REMOTE_SCRIPT_DIR}/{script_name} >/dev/null 2>&1 & echo $!"            # Befehl zum Starten des Skripts im Hintergrund und Ausgabe der PID.
        stdin, stdout, stderr = client.exec_command(cmd)                                        # Der Befehl wird über die SSH-Verbindung ausgeführt.                               
        pid_str = stdout.read().decode('utf-8', errors='ignore').strip()                        # Die Ausgabe (PID) wird gelesen und dekodiert.
        err = stderr.read().decode('utf-8', errors='ignore').strip()                            # Fehlerausgabe wird gelesen und dekodiert.
        if err:
            print(f"[ssh_start_bg ERR] {err}")
        try:                                                                                                                         
            pid = int(pid_str)                                                                  # Die PID wird in eine Ganzzahl umgewandelt.     
            print(f"[ssh_start_bg] {script_name} gestartet, PID={pid}")                         # Die gestartete Skript und die PID werden ausgegeben.                  
            return pid                                                                                                                                      
        except Exception:                                                                                                                           
            print(f"[ssh_start_bg] Konnte PID nicht lesen: '{pid_str}'")                        # Falls die PID nicht gelesen werden kann, wird eine Fehlermeldung ausgegeben.                                                                                       
            return None 
    except Exception as e:
        print(f"[ssh_start_bg] Fehler: {e}")
        return None

def ssh_kill_pid(client: paramiko.SSHClient, pid: int, signal="TERM"):                          # Diese Funktion sendet ein Signal (standardmäßig TERM) an einen Prozess auf dem Raspberry Pi, um ihn zu beenden. Ist eien saubere Methode um Prozesse zu stoppen.
    if not client or not pid:
        return
    try:
        cmd = f"kill -{signal} {pid}"
        client.exec_command(cmd)
        print(f"[ssh_kill_pid] kill -{signal} {pid} gesendet")
    except Exception as e:
        print(f"[ssh_kill_pid] Fehler: {e}")


def ssh_pkill_script(client: paramiko.SSHClient, script_name: str):                              # Diese Funktion beendet alle Prozesse auf dem Raspberry Pi, die ein bestimmtes Skript ausführen, indem sie den Befehl pkill verwendet. Dies ist eine Notfallmethode, falls die PID nicht bekannt ist.                                  
    if not client:
        return
    try:
        cmd = f"pkill -f '{REMOTE_SCRIPT_DIR}/{script_name}'"
        client.exec_command(cmd)
        print(f"[ssh_pkill_script] pkill -f {script_name} gesendet")
    except Exception as e:
        print(f"[ssh_pkill_script] Fehler: {e}")


def menue_starten():                                        # Diese Funktion wird aufgerufen, wenn der Start-Button im Hauptfenster gedrückt wird. Sie startet die externe Anwendung, richtet das Fenster aus, öffnet den Reader, stellt die SSH-Verbindung her und erstellt das Menü-Fenster.  
    """Start 1:
       - Software starten
       - Fenster finden/fokussieren/ausrichten
       - (direkt danach) Reader öffnen
       - Antenne auswählen
       - SSH-Verbindung herstellen
       - Menü öffnen

    """
    global ssh_client, process, menu_win, option_var, entry_count, program_window_title

  
    try:                                                                                                        # 1) Software starten
        if not os.path.isfile(APP_PATH):
            raise FileNotFoundError(f"EXE nicht gefunden: {APP_PATH}")
        process = subprocess.Popen([APP_PATH], cwd=APP_DIR)
        time.sleep(2.0)  # Splash/Start abwarten
    except Exception as e:
        print(f"Fehler beim Starten der Anwendung: {e}")
        return


    program_window_title = "Roche RFID Programmer SW"                                                           # 2) Fenster finden/fokussieren/ausrichten
    prog_win = find_and_focus_window(program_window_title, retries=25, sleep_between=0.4)
    if not prog_win:
        print("Programmfenster konnte nicht fokussiert werden – Abbruch.")
        return

  
    try:                                                                                                         # Fenster an linke Bildschirmseite andocken und Größe anpassen
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

   
    reader_oeffnen_sequence()                                                                                   # Hier wird die Funktion aufgerufen, welche die Tastensequenz zum Öffnen des Readers ausführt.                   
    time.sleep(0.3)


    ssh_client = ssh_connect()                                                                                   # 3) SSH-Verbindung herstellen                       


    menu_win = tk.Tk()                                                                                           # 4) Menü-Fenster öffnen (rechts daneben platzieren)                                    
    menu_win.title("Menü")
    menu_width = 420
    menu_height = 320
    menu_x = (prog_win.width if prog_win else screen_width // 2) + 50
    menu_y = 50
    menu_win.geometry(f"{menu_width}x{menu_height}+{menu_x}+{menu_y}")


    # ======= Menü-Elemente =======

                                                                                                            # Dropdown-Menü für Consumable-Auswahl
    option_var = tk.StringVar(menu_win)                                                                     # Variable für die Auswahl im Dropdown-Menü
    option_var.set("Bitte wählen")                                                                          # Standardwert (wird angezeigt wenn nichts ausgewählt ist)           
    options = ["Bitte wählen", "Washbuffer", "Lysis", "Diluent", "CMR +", "CMR -", "Reagent", "MGP"]        # Optionen im Dropdown-Menü
    dropdown = tk.OptionMenu(menu_win, option_var, *options)                                                # Erstellen des Dropdown-Menüs   
    dropdown.config(width=20)                                                                               # Breite des Dropdown-Menüs                             
    dropdown.pack(pady=10)                                                                                  # Abstand nach oben/unten                        

                                                                                                            # Eingabefeld für Anzahl 1-100 (wird bei der Beschriftungs-Sequenz verwendet)
    entry_count = tk.Entry(menu_win, width=6)                                                               # Eingabefeld für die Anzahl der Wiederholungen              
    entry_count.insert(0, "1")                                                                              # Standardwert ist 1                   
    entry_count.pack(pady=5)                                                                                # Abstand nach oben/unten          


    current_pid = {"name": None, "pid": None}                                                               # Merker für aktuell laufenden Prozess (Scriptname + PID)              

    def _stop_running_motion():                                                                             # Diese Funktion stoppt einen laufenden Bewegungsprozess auf dem Raspberry Pi. Sie wird aufgerufen, wenn ein Pfeil-Button losgelassen wird oder ein neuer Bewegungsprozess gestartet werden soll.
        if current_pid["pid"]:
            ssh_kill_pid(ssh_client, current_pid["pid"], signal="TERM")                                     # Zuerst versuchen den Prozess sauber zu beenden.
            ssh_kill_pid(ssh_client, current_pid["pid"], signal="KILL")                                     # Falls das nicht klappt, wird der Prozess mit KILL beendet.
        if current_pid["name"]:                                                                             # Falls der Prozessname bekannt ist, wird zusätzlich pkill verwendet um alle Prozesse mit diesem Skriptnamen zu beenden (Notfallmethode).
            ssh_pkill_script(ssh_client, current_pid["name"])                                                   
        ssh_run(ssh_client, "motor_stop.py")                                                                # Zum Schluss werden die Motoren gestoppt damit sie keinen Strom mehr verbrauchen.         
        current_pid["name"] = None                                                                          # Merker zurücksetzen        
        current_pid["pid"] = None                                                                          


    SCRIPT_LEFT  = "links_drehen.py"                                                                        # Skriptnamen für die Bewegungs-Skripte auf dem Raspberry Pi                    
    SCRIPT_RIGHT = "rechts_drehen.py"                                                                                               


    def links_druecken(event):                                                                               # Es wird definiert was passiert wenn der Links-Pfeil Button gedrückt wird.       
        btn_left.config(relief="sunken", state="active")                                                     # Button optisch als gedrückt darstellen.           
        _stop_running_motion()                                                                               # Zuerst einen eventuell laufenden Bewegungsprozess stoppen.                       
        pid = ssh_start_bg(ssh_client, SCRIPT_LEFT)                                                          # Dann das links_drehen.py Skript starten und die PID speichern.          
        current_pid["name"] = SCRIPT_LEFT                                                                    # Merker für aktuell laufenden Prozess aktualisieren.                 
        current_pid["pid"]  = pid                                                                            

    def links_loslassen(event):                                                                             # Es wird definiert was passiert wenn der Links-Pfeil Button losgelassen wird.                  
        btn_left.config(relief="raised", state="normal")                                                    # Button optisch als losgelassen darstellen.                   
        _stop_running_motion()                                                                              # Bewegungsprozess stoppen.                      

    btn_left = tk.Button(menu_win, text="←", font=("Arial", 12, "bold"), width=4)                           # Das erstellen des Links-Pfeil Buttons. Im GUI-Fenster wird der Button mit dem Text "←" dargestellt.
    btn_left.bind("<ButtonPress-1>", links_druecken)                                                        # Ereignisbindung: Wenn der Button gedrückt wird, wird die Funktion links_druecken aufgerufen.                      
    btn_left.bind("<ButtonRelease-1>", links_loslassen)                                                     # Ereignisbindung: Wenn der Button losgelassen wird, wird die Funktion links_loslassen aufgerufen.                      
    btn_left.pack(side=tk.LEFT, padx=20, pady=10)                                                           # Button im Menü-Fenster platzieren (links, mit Abstand zu anderen Elementen).                

                                                                                                            #Der Rechte-Pfeil Button wird auf die gleiche Weise erstellt wie der Linke.
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


    
    def start_sequence():                                                                           # Hier wird die Funktion definiert, die ausgeführt wird wenn der Start-Button im Menü-Fenster gedrückt wird. Sie liest die Eingaben aus dem Menü aus, stellt sicher dass das Programmfenster den Fokus hat, und startet dann die Sequenz für das ausgewählte Consumable und die angegebene Anzahl.       
        selection = option_var.get()                                                                # Ausgewählte Option         
        if selection == "Bitte wählen":
            print("Bitte eine gültige Option wählen.")
            return
        try:
            n = int(entry_count.get())                                                              # Anzahl der Wiederholungen (1-100)             
        except ValueError:
            print("Ungültige Anzahl. Bitte 1–100 eingeben.")
            return
        if n < 1 or n > 100:
            print("Ungültige Anzahl. Bitte 1–100 eingeben.")
            return

        
        win = find_and_focus_window(program_window_title, retries=5, sleep_between=0.2)             # Sicherstellen dass das Programmfenster den Fokus hat.    
        if not win:
            print("Fensterfokus fehlgeschlagen.")
            return

     
        auswahl_consumable(selection)                                                               # Tastensequenz für die Auswahl des Consumables ausführen.      

        Beschriftungs_Sequenz(n)                                                                    # Die Hauptsequenz mit der angegebenen Anzahl ausführen.     

        print("Sequenz abgeschlossen.")

    btn_start_menu = tk.Button(menu_win, text="Start", font=("Arial", 12), command=start_sequence)      # Start-Button im Menü-Fenster
    btn_start_menu.pack(pady=20)                                                                        # Abstand nach oben/unten                      


    def exit_app():                                                           # Diese Funktion wird aufgerufen, wenn der Beenden-Button im Menü-Fenster gedrückt wird. Sie sorgt dafür, dass alle laufenden Prozesse gestoppt werden, die SSH-Verbindung geschlossen wird, und das Menü-Fenster sowie die Anwendung beendet werden.
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

    btn_exit = tk.Button(menu_win, text="Beenden", command=exit_app)                                # Beenden-Button im Menü-Fenster        
    btn_exit.pack(pady=5)


    root.destroy()                                                                                  # Hauptfenster schließen (nur das Menü-Fenster bleibt offen).                       

# Start-Button (Start 1)
start_btn = tk.Button(root, text="Start", font=("Arial", 14, "bold"), command=menue_starten)        # Start-Button im Hauptfenster     
start_btn.pack(padx=50, pady=50)

root.mainloop()                                                                                     # Start der GUI-Ereignisschleife (Mainloop) für das Hauptfenster.                           


