#!/usr/bin/env python3
import RPi.GPIO as GPIO
import time

# Pin-Konfiguration (identisch zu bewegung_rfid_test.py)
DIR1, STEP1 = 20, 21
M1_M0, M1_M1, M1_M2 = 13, 19, 26
EN1 = 5   # Enable für Motor 1 (LOW=aktiv)
DIR2, STEP2 = 22, 24
M2_M0, M2_M1, M2_M2 = 14, 15, 18
EN2 = 6   # Enable für Motor 2
CW, CCW = GPIO.HIGH, GPIO.LOW  # Drehrichtungen

# Einstellungen
MICROSTEP_MODE = 32        # 1/32-Schritte für beide Motoren
start_delay   = 0.006      # Verzögerung zu Beginn (Sekunden)
min_delay     = 0.002      # Verzögerung bei maximaler Geschwindigkeit
accel_steps   = 60         # Anzahl Schritte für Beschleunigungsrampe

# GPIO initialisieren
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
for pin in (DIR1, STEP1, DIR2, STEP2,
            M1_M0, M1_M1, M1_M2,
            M2_M0, M2_M1, M2_M2,
            EN1, EN2):
    GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)
# Motoren zunächst deaktiviert lassen
GPIO.output(EN1, GPIO.HIGH)
GPIO.output(EN2, GPIO.HIGH)

# Microstepping-Modus an beiden Treibern setzen (hier 1/32)
def set_microstep(m0, m1, m2, mode):
    mapping = {
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

set_microstep(M1_M0, M1_M1, M1_M2, MICROSTEP_MODE)
set_microstep(M2_M0, M2_M1, M2_M2, MICROSTEP_MODE)

# Motoren aktivieren und Drehrichtung auf CCW (gegen Uhrzeigersinn) setzen
GPIO.output(EN1, GPIO.LOW)   # Treiber einschalten
GPIO.output(EN2, GPIO.LOW)
GPIO.output(DIR1, CW)       # beide Motoren auf CCW drehen
GPIO.output(DIR2, CW)

# Schritte in Dauerschleife ausführen
current_delay = start_delay
step_count = 0
try:
    while True:
        # Step-Pins HIGH setzen (Schritt auslösen)
        GPIO.output(STEP1, GPIO.HIGH)
        GPIO.output(STEP2, GPIO.HIGH)
        time.sleep(current_delay)
        # Step-Pins LOW zurücksetzen
        GPIO.output(STEP1, GPIO.LOW)
        GPIO.output(STEP2, GPIO.LOW)
        time.sleep(current_delay)
        # Beschleunigungsphase: Delay verkürzen bis min_delay erreicht ist
        if step_count < accel_steps and current_delay > min_delay:
            current_delay -= (start_delay - min_delay) / accel_steps
            if current_delay < min_delay:
                current_delay = min_delay
        step_count += 1
except KeyboardInterrupt:
    # Bei Unterbrechung: Motoren stoppen
    try:
        GPIO.output(EN1, GPIO.HIGH)  # Treiber deaktivieren
        GPIO.output(EN2, GPIO.HIGH)
        # Alle anderen Pins Low setzen (optional, Sicherheit)
        GPIO.output(DIR1, GPIO.LOW); GPIO.output(DIR2, GPIO.LOW)
        GPIO.output(STEP1, GPIO.LOW); GPIO.output(STEP2, GPIO.LOW)
    finally:
        GPIO.cleanup()
        # Alternativ könnte hier auch motor_stop.py aufgerufen werden:
        # import subprocess; subprocess.run(["python3", "motor_stop.py"])
