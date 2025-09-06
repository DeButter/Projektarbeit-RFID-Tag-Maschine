#!/usr/bin/env python3
import RPi.GPIO as GPIO
import time

# --- Motor 1 Pins ---
DIR1, STEP1 = 20, 21
M1_M0, M1_M1, M1_M2 = 13, 19, 26
EN1 = 5  # ENABLE Motor 1 (LOW=an, HIGH=aus)

# --- Motor 2 Pins ---
DIR2, STEP2 = 22, 24
M2_M0, M2_M1, M2_M2 = 14, 15, 18
EN2 = 6  # ENABLE Motor 2

def motors_stop():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    # alle relevanten Pins als Output initialisieren
    for pin in (DIR1, STEP1, DIR2, STEP2,
                M1_M0, M1_M1, M1_M2,
                M2_M0, M2_M1, M2_M2,
                EN1, EN2):
        GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)

    # Treiber AUS (stromlos)
    GPIO.output(EN1, GPIO.HIGH)
    GPIO.output(EN2, GPIO.HIGH)

    # alle anderen Leitungen LOW (sicherer Zustand)
    for pin in (DIR1, STEP1, DIR2, STEP2,
                M1_M0, M1_M1, M1_M2,
                M2_M0, M2_M1, M2_M2):
        GPIO.output(pin, GPIO.LOW)

    # EN-Pins gegen Float absichern: als INPUT mit Pull-Up hinterlassen
    GPIO.setup(EN1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(EN2, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    print("Motoren gestoppt & stromlos (EN mit Pull-Up).")

if __name__ == "__main__":
    try:
        motors_stop()
        time.sleep(0.1)
    finally:
        # KEIN cleanup(): Pull-Ups an EN sollen erhalten bleiben
        pass

    
