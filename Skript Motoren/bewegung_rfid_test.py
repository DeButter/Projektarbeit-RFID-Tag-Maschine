#!/usr/bin/env python3, wird verwendet um das Skript mit Python 3 auszuführen

import RPi.GPIO as GPIO                     # Bibliothek zur Steuerung der GPIO-Pins des Raspberry Pi   
import time                                 # Bibliothek für Zeitfunktionen
import math                                 # Mathematische Funktionen
import random                               # Zufallszahlen
import argparse                             # Bibliothek zur Verarbeitung von Kommandozeilenargumenten

                                            # Motor 1 Pins
DIR1, STEP1 = 20, 21                        # DIR = Richtung, STEP = Schritt
M1_M0, M1_M1, M1_M2 = 13, 19, 26            # Microstepping-Pins für Motor 1
EN1 = 5                                     # Enable M1 (LOW=an, HIGH=aus)        

                                            # Motor 2 Pins
DIR2, STEP2 = 22, 24                        # DIR = Richtung, STEP = Schritt
M2_M0, M2_M1, M2_M2 = 14, 15, 18            # Microstepping-Pins für Motor 2
EN2 = 6                                     # Enable M2

CW, CCW = GPIO.HIGH, GPIO.LOW               # Drehrichtungen (CW=im Uhrzeigersinn, CCW=gegen Uhrzeigersinn)
BASE_SPR = 200                              # Vollschritte/Umdrehung

# ============== Einstellungen / Defaults ==============
DEFAULT_MICROSTEP_MODE = 32                     # Microstepping-Modus (1,2,4,8,16,32)
DEFAULT_DEGREES       = 90                      # Winkel in Grad
DEFAULT_OFFSET_SEC    = 0.5                     # Startverzögerung Motor1 (s)   
DEFAULT_SPEED_PERCENT = 40                      # Geschwindigkeit 1..100 %
DEFAULT_DITHER        = 0.0                     # Delay-Variation (z.B. 0.0002)
DEFAULT_ACCEL_STEPS   = 220                     # Rampen-Schritte (größer=weicher)
DEFAULT_DIR1          = "CW"                    # Drehrichtung Motor 1
DEFAULT_DIR2          = "CCW"                   # Drehrichtung Motor 2

                                                # Mapping von Geschwindigkeit (% 1..100) zu Step-Delays (Zeit zwischen Steps)   
SLOW_START_DELAY = 0.014                        # langsamer Start
SLOW_MIN_DELAY   = 0.0075                       # langsame Endgeschwindigkeit
FAST_START_DELAY = 0.0060                       # schneller Start 
FAST_MIN_DELAY   = 0.0035                       # schnelle Endgeschwindigkeit

def map_speed_to_delays(speed_percent: int):                                        # Mapping von Geschwindigkeit (%) zu Step-Delays
    sp = max(1, min(100, int(speed_percent)))                                       # auf 1..100 begrenzen
    t = (sp - 1) / 99.0                                                             # normieren auf 0..1                                         
    start_delay = SLOW_START_DELAY + (FAST_START_DELAY - SLOW_START_DELAY) * t      # Start-Delay interpolieren        
    min_delay   = SLOW_MIN_DELAY   + (FAST_MIN_DELAY   - SLOW_MIN_DELAY)   * t      # Min-Delay interpolieren
    return start_delay, min_delay

# ============== GPIO / Helpers ==============
def gpio_setup():                                                   # GPIO initialisieren   
    GPIO.setmode(GPIO.BCM)                                          # GPIO-Modus auf BCM setzen        
    GPIO.setwarnings(False)                                         # Warnungen deaktivieren                     
    for pin in (DIR1, STEP1, DIR2, STEP2,                           # Alle relevanten Pins als Output initialisieren  
                M1_M0, M1_M1, M1_M2,
                M2_M0, M2_M1, M2_M2,
                EN1, EN2):
        GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)                     
   
    GPIO.output(EN1, GPIO.HIGH)                     # Motoren zunächst deaktiviert lassen   
    GPIO.output(EN2, GPIO.HIGH)

def set_microstep_drv8825(m0, m1, m2, mode):                                        # Microstepping-Modus an beiden Treibern setzen (hier 1/32)
    tbl = {1:(0,0,0), 2:(1,0,0), 4:(0,1,0), 8:(1,1,0), 16:(0,0,1), 32:(1,0,1)}      # Mappings für die Microstepping-Modi
    if mode not in tbl:
        raise ValueError("Ungültiger Microstep-Mode (1,2,4,8,16,32)")                   
    GPIO.output([m0, m1, m2], tbl[mode])                                                

def motors_on():                                                                                                
    GPIO.output(EN1, GPIO.LOW)                                            # aktiv
    GPIO.output(EN2, GPIO.LOW)

def motors_off():
    GPIO.output(EN1, GPIO.HIGH)                                           # stromlos
    GPIO.output(EN2, GPIO.HIGH)

def leave_en_pulled_up():                                               # EN-Pins gegen Float absichern: als INPUT mit Pull-Up hinterlassen               
    GPIO.setup(EN1, GPIO.IN, pull_up_down=GPIO.PUD_UP)                  # Pull-Up an EN1
    GPIO.setup(EN2, GPIO.IN, pull_up_down=GPIO.PUD_UP)                  # Pull-Up an EN2    

# ============== Bewegungsprofil (S-Kurve) ==============
def ease_delay(i, total, start_delay, min_delay, accel_steps):          # S-Kurven-Delay für Schritt i von total    
    if total <= 0:                                                                  
        return start_delay  
    if i < accel_steps:
        t = i / max(1, accel_steps)
        return min_delay + (start_delay - min_delay) * 0.5 * (1 + math.cos(math.pi * t))
    if i >= total - accel_steps:
        t = (total - 1 - i) / max(1, accel_steps)
        return min_delay + (start_delay - min_delay) * 0.5 * (1 + math.cos(math.pi * t))
    return min_delay

def move_with_offset_quiet(steps, dir1, dir2, start_delay, min_delay, accel_steps, offset_sec, dither):        # Bewegung mit Offset, S-Kurve, leise
    motors_on()                                                                                                # Motoren aktivieren                                       
    GPIO.output(DIR1, dir1)                                                                                             
    GPIO.output(DIR2, dir2)

    t0 = time.perf_counter()                                                                                   # Startzeit merken                       
    for i in range(steps):                                                                                     # für alle Schritte
        base_d = ease_delay(i, steps, start_delay, min_delay, accel_steps)                                     # Basis-Delay für diesen Schritt                                        
        if dither:                                                                                                                          
            base_d += random.uniform(-dither, dither)                                                          # Delay etwas variieren (leiser)                         

        GPIO.output(STEP2, GPIO.HIGH)                                                                          # Step-Pin Motor 2 HIGH setzen                       
        if (time.perf_counter() - t0) >= offset_sec:                                                           # Motor 1 mit Offset starten                
            GPIO.output(STEP1, GPIO.HIGH)                                                                      # Step-Pin Motor 1 HIGH setzen           
        time.sleep(base_d)                                                                                  

        GPIO.output(STEP2, GPIO.LOW)                                                                           # Step-Pin Motor 2 LOW zurücksetzen                      
        if (time.perf_counter() - t0) >= offset_sec:                                                           # Motor 1 mit Offset starten                   
            GPIO.output(STEP1, GPIO.LOW)                                                                       # Step-Pin Motor 1 LOW zurücksetzen                           
        time.sleep(base_d)                                                                                  

# ============== CLI & Main ==============
def parse_args():                                                                                               # Kommandozeilenargumente parsen                            
    p = argparse.ArgumentParser(description="DRV8825 Bewegung – leise, Offset, stromlos am Ende")               
    p.add_argument("--microstep", type=int, default=DEFAULT_MICROSTEP_MODE, choices=[1,2,4,8,16,32])
    p.add_argument("--degrees", type=float, default=DEFAULT_DEGREES, help="Winkel in Grad")
    p.add_argument("--offset", type=float, default=DEFAULT_OFFSET_SEC, help="Startverzögerung Motor1 (s)")
    p.add_argument("--speed", type=int, default=DEFAULT_SPEED_PERCENT, help="Geschwindigkeit 1..100 %%")
    p.add_argument("--accel", type=int, default=DEFAULT_ACCEL_STEPS, help="Rampen-Schritte (größer=weicher)")
    p.add_argument("--dither", type=float, default=DEFAULT_DITHER, help="Delay-Variation (z.B. 0.0002)")
    p.add_argument("--dir1", type=str, default=DEFAULT_DIR1, choices=["CW","CCW"])
    p.add_argument("--dir2", type=str, default=DEFAULT_DIR2, choices=["CW","CCW"])
    return p.parse_args()

if __name__ == "__main__":                                # Direktaufruf: Bewegung mit Offset, S-Kurve, leise                               
    args = parse_args()                                   # Kommandozeilenargumente holen                   

    dir1_level = CW if args.dir1 == "CW" else CCW           
    dir2_level = CW if args.dir2 == "CW" else CCW           
    START_DELAY, MIN_DELAY = map_speed_to_delays(args.speed)            

    gpio_setup()                                                                # GPIO initialisieren           
    try:
        set_microstep_drv8825(M1_M0, M1_M1, M1_M2, args.microstep)            # Microstepping für Motor 1 setzen
        set_microstep_drv8825(M2_M0, M2_M1, M2_M2, args.microstep)            # Microstepping für Motor 2 setzen  

        steps_per_rev = BASE_SPR * args.microstep                             # Schritte pro Umdrehung 
        steps = int(round((args.degrees / 360.0) * steps_per_rev))            # Schritte für gewünschten Winkel
        if steps > 0:                                                         # nur bei Bewegung > 0
            move_with_offset_quiet(                                           # Bewegung mit Offset, S-Kurve, leise         
                steps=steps,
                dir1=dir1_level, dir2=dir2_level,
                start_delay=START_DELAY, min_delay=MIN_DELAY,
                accel_steps=args.accel, offset_sec=args.offset, dither=args.dither
            )

        
        motors_off()                                                   # Motoren stromlos schalten              
        leave_en_pulled_up()                                           # EN-Pins gegen Float absichern: als INPUT mit Pull-Up hinterlassen              

    except KeyboardInterrupt:                                          # Bei STRG-C abbrechen     
        print("Abbruch durch Benutzer.")
        try:
            motors_off()
            leave_en_pulled_up()
        except Exception:
            pass
    finally:
                                                                        # KEIN GPIO.cleanup(): sonst verschwinden die Pull-Ups an EN wieder
        pass

    
