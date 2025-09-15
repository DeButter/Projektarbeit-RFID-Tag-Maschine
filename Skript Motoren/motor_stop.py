#!/usr/bin/env python3
import RPi.GPIO as GPIO                                  # Bibliothek zur Steuerung der GPIO-Pins des Raspberry Pi
import time                                              # Bibliothek für Zeitfunktionen                      

                                                         # Motor 1 Pins
DIR1, STEP1 = 20, 21
M1_M0, M1_M1, M1_M2 = 13, 19, 26                         # Microstepping-Pins für Motor 1
EN1 = 5                                                  # ENABLE Motor 1 (LOW=an, HIGH=aus)

                                                         # Motor 2 Pins
DIR2, STEP2 = 22, 24
M2_M0, M2_M1, M2_M2 = 14, 15, 18                         # Microstepping-Pins für Motor 2
EN2 = 6                                                  # ENABLE Motor 2

def motors_stop():                                       # Motoren stoppen & stromlos schalten (EN mit Pull-Up)
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

                                                         # alle relevanten Pins als Output initialisieren
    for pin in (DIR1, STEP1, DIR2, STEP2,
                M1_M0, M1_M1, M1_M2,
                M2_M0, M2_M1, M2_M2,
                EN1, EN2):
        GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)

   
    GPIO.output(EN1, GPIO.HIGH)                          # Motoren deaktivieren
    GPIO.output(EN2, GPIO.HIGH)

 
    for pin in (DIR1, STEP1, DIR2, STEP2,                # alle anderen Leitungen LOW (sicherer Zustand)
                M1_M0, M1_M1, M1_M2,
                M2_M0, M2_M1, M2_M2):
        GPIO.output(pin, GPIO.LOW)

    
    GPIO.setup(EN1, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # EN-Pins gegen Float absichern: als INPUT mit Pull-Up hinterlassen
    GPIO.setup(EN2, GPIO.IN, pull_up_down=GPIO.PUD_UP)      

    print("Motoren gestoppt & stromlos (EN mit Pull-Up).")  

if __name__ == "__main__":                                  # Direktaufruf: Motoren stoppen
    try:
        motors_stop()                                       # Motoren stoppen & stromlos schalten
        time.sleep(0.1)
    finally:
                                                            # KEIN cleanup(): Pull-Ups an EN sollen erhalten bleiben
        pass

    
