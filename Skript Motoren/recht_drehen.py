import RPi.GPIO as GPIO
import time

DIR1, STEP1 = 20, 21
M1_M0, M1_M1, M1_M2 = 13, 19, 26
EN1 = 5  # ENABLE Motor 1

# --- Motor 2 Pins ---
DIR2, STEP2 = 22, 24
M2_M0, M2_M1, M2_M2 = 14, 15, 18
EN2 = 6  # ENABLE Motor 2


CW, CCW = GPIO.HIGH, GPIO.LOW
BASE_SPR = 200  # Vollschritte pro Umdrehung

# --- Geschwindigkeitseinstellung ---
speed_factor = 1.0   # 1.0 = normal, >1.0 schneller, <1.0 langsamer
base_start_delay = 0.006
base_min_delay = 0.002

# --- GPIO Setup ---
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
for pin in (DIR1, STEP1, DIR2, STEP2,
            M1_M0, M1_M1, M1_M2,
            M2_M0, M2_M1, M2_M2,
            EN1, EN2):
    GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)


# --- Microstepping setzen ---
def set_microstep(m0, m1, m2, mode):
    if mode == 1:      GPIO.output([m0, m1, m2], (0, 0, 0))
    elif mode == 2:    GPIO.output([m0, m1, m2], (1, 0, 0))
    elif mode == 4:    GPIO.output([m0, m1, m2], (0, 1, 0))
    elif mode == 8:    GPIO.output([m0, m1, m2], (1, 1, 0))
    elif mode == 16:   GPIO.output([m0, m1, m2], (0, 0, 1))
    elif mode == 32:   GPIO.output([m0, m1, m2], (1, 0, 1))



# --- Motorstrom an/aus ---
def motors_on():
    GPIO.output(EN1, GPIO.LOW)  # LOW = Treiber aktiv
    GPIO.output(EN2, GPIO.LOW)

def motors_off():
    GPIO.output(EN1, GPIO.HIGH) # HIGH = Treiber aus
    GPIO.output(EN2, GPIO.HIGH)


# --- Beide Motoren synchron ---
def move_both_sync(steps, dir1=CW, dir2=CW, start_delay=0.006, min_delay=0.002, accel_steps=60):
    motors_on()  # Motoren aktivieren

    GPIO.output(DIR1, dir1)
    GPIO.output(DIR2, dir2)
    d = start_delay
    dec_start = max(0, steps - accel_steps)

    for i in range(steps):
        # STEP HIGH
        GPIO.output(STEP1, GPIO.HIGH)
        GPIO.output(STEP2, GPIO.HIGH)
        time.sleep(d)
        # STEP LOW
        GPIO.output(STEP1, GPIO.LOW)
        GPIO.output(STEP2, GPIO.LOW)
        time.sleep(d)

        # Beschleunigen
        if i < accel_steps and d > min_delay:
            d -= (start_delay - min_delay) / accel_steps
        # Abbremsen
        if i >= dec_start and d < start_delay:
            d += (start_delay - min_delay) / accel_steps

    motors_off()  # Motoren abschalten nach Bewegung

try:
    # Microstepping-Modus wählen (1, 2, 4, 8, 16, 32)
    mode = 8
    set_microstep(M1_M0, M1_M1, M1_M2, mode)
    set_microstep(M2_M0, M2_M1, M2_M2, mode)

    steps_per_rev = BASE_SPR * mode

    # Delay-Werte aus speed_factor berechnen
    start_delay = base_start_delay / speed_factor
    min_delay = base_min_delay / speed_factor

    # Beispiel: beide Motoren 2 Umdrehungen CW
    move_both_sync(steps_per_rev * 2, dir1=CW, dir2=CCW,
                   start_delay=start_delay, min_delay=min_delay, accel_steps=80)
except KeyboardInterrupt:
    print("Abbruch durch Benutzer.")
finally:
    GPIO.cleanup()