#!/usr/bin/env python3
import RPi.GPIO as GPIO                             # Bibliothek zur Steuerung der GPIO-Pins des Raspberry Pi
import time                                         # Bibliothek für Zeitfunktionen           

                                                    
                                                    
                                                    
                                                    
                                                    # Pin-Konfiguration auf dem Raspberry Pi 
DIR1, STEP1 = 20, 21                                # DIR = Richtung, STEP = Schritt                            
M1_M0, M1_M1, M1_M2 = 13, 19, 26                    # Microstepping-Pins für Motor 1
EN1 = 5                                             # Enable für Motor 1 (LOW=aktiv)
DIR2, STEP2 = 22, 24                                # DIR = Richtung, STEP = Schritt    
M2_M0, M2_M1, M2_M2 = 14, 15, 18                    # Microstepping-Pins für Motor 2
EN2 = 6                                             # Enable für Motor 2
CW, CCW = GPIO.HIGH, GPIO.LOW                       # Drehrichtungen (CW=im Uhrzeigersinn, CCW=gegen Uhrzeigersinn)

                                                    # Einstellungen
MICROSTEP_MODE = 32                                 # 1/32-Schritte für beide Motoren
start_delay   = 0.006                               # Verzögerung zu Beginn (Sekunden)
min_delay     = 0.002                               # Verzögerung bei maximaler Geschwindigkeit
accel_steps   = 60                                  # Anzahl Schritte für Beschleunigungsrampe

                                                    # GPIO initialisieren
GPIO.setmode(GPIO.BCM)                              # GPIO-Modus auf BCM setzen     
GPIO.setwarnings(False)                             # Warnungen deaktivieren
for pin in (DIR1, STEP1, DIR2, STEP2,               # Alle relevanten Pins als Output initialisieren
            M1_M0, M1_M1, M1_M2,                        
            M2_M0, M2_M1, M2_M2,
            EN1, EN2):
    GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)     # Motoren zunächst deaktiviert lassen           

GPIO.output(EN1, GPIO.HIGH)                         
GPIO.output(EN2, GPIO.HIGH)


def set_microstep(m0, m1, m2, mode):                # Microstepping-Modus an beiden Treibern setzen (hier 1/32)
    mapping = {                                     # Mappings für die Microstepping-Modi
        1:  (GPIO.LOW,  GPIO.LOW,  GPIO.LOW),           
        2:  (GPIO.HIGH, GPIO.LOW,  GPIO.LOW),
        4:  (GPIO.LOW,  GPIO.HIGH, GPIO.LOW),
        8:  (GPIO.HIGH, GPIO.HIGH, GPIO.LOW),
        16: (GPIO.LOW,  GPIO.LOW,  GPIO.HIGH),
        32: (GPIO.HIGH, GPIO.LOW,  GPIO.HIGH)
    }
    if mode not in mapping:
        raise ValueError("Ungültiger Microstep-Mode!")
    GPIO.output([m0, m1, m2], mapping[mode])

set_microstep(M1_M0, M1_M1, M1_M2, MICROSTEP_MODE)              # Microstepping für Motor 1 setzen  
set_microstep(M2_M0, M2_M1, M2_M2, MICROSTEP_MODE)              # Microstepping für Motor 2 setzen

                                                                # Motoren aktivieren und Drehrichtung auf CW (gegen Uhrzeigersinn) setzen
GPIO.output(EN1, GPIO.LOW)                                      # Treiber einschalten
GPIO.output(EN2, GPIO.LOW)
GPIO.output(DIR1, CW)                                          # beide Motoren auf CW drehen
GPIO.output(DIR2, CW)

                                                               
current_delay = start_delay                             # Aktuelle Verzögerung initial auf Startwert setzen 
step_count = 0                                          # Schrittzähler initialisieren           
try:
    while True:
        GPIO.output(STEP1, GPIO.HIGH)               # Step-Pins HIGH setzen (Schritt auslösen)
        GPIO.output(STEP2, GPIO.HIGH)                   
        time.sleep(current_delay)                   # Kurze Pause (abhängig von der aktuellen Geschwindigkeit)
        GPIO.output(STEP1, GPIO.LOW)                # Step-Pins LOW zurücksetzen
        GPIO.output(STEP2, GPIO.LOW)
        time.sleep(current_delay)

        if step_count < accel_steps and current_delay > min_delay:                  # Beschleunigungsrampe
            current_delay -= (start_delay - min_delay) / accel_steps                # Verzögerung verringern
            if current_delay < min_delay:                                                   
                current_delay = min_delay
        step_count += 1
except KeyboardInterrupt:                                                           # Bei STRG-C abbrechen
  
    try:
        GPIO.output(EN1, GPIO.HIGH)                                                 # Treiber deaktivieren
        GPIO.output(EN2, GPIO.HIGH)
        GPIO.output(DIR1, GPIO.LOW); GPIO.output(DIR2, GPIO.LOW)                    # Alle anderen Pins Low setzen (optional, Sicherheit)
        GPIO.output(STEP1, GPIO.LOW); GPIO.output(STEP2, GPIO.LOW)                      
    finally:
        GPIO.cleanup()                                                              # GPIOs zurücksetzen          



