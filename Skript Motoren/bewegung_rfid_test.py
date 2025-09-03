#!/usr/bin/env python3
# DRV8825: Leiser Lauf (S-Kurven), 1/32 Microstepping, Offset-Start, stromlos am Ende
# Speed steuerbar per --speed (1..100 %)
import RPi.GPIO as GPIO
import time
import math
import random
import argparse

# --- Motor 1 Pins (wie bei dir) ---
DIR1, STEP1 = 20, 21
M1_M0, M1_M1, M1_M2 = 13, 19, 26
EN1 = 5   # Enable M1 (LOW=an, HIGH=aus)

# --- Motor 2 Pins ---
DIR2, STEP2 = 22, 24
M2_M0, M2_M1, M2_M2 = 14, 15, 18
EN2 = 6   # Enable M2

CW, CCW = GPIO.HIGH, GPIO.LOW
BASE_SPR = 200  # Vollschritte/Umdrehung

# ======= Defaults (per CLI änderbar) =======
DEFAULT_MICROSTEP_MODE = 32
DEFAULT_DEGREES       = 90
DEFAULT_OFFSET_SEC    = 0.5
DEFAULT_SPEED_PERCENT = 40
DEFAULT_DITHER        = 0.0
DEFAULT_ACCEL_STEPS   = 220
DEFAULT_DIR1          = "CW"
DEFAULT_DIR2          = "CCW"

# Speed-Mapping (1..100% -> Delays)
SLOW_START_DELAY = 0.014
SLOW_MIN_DELAY   = 0.0075
FAST_START_DELAY = 0.0060
FAST_MIN_DELAY   = 0.0035

def map_speed_to_delays(speed_percent: int):
    sp = max(1, min(100, int(speed_percent)))
    t = (sp - 1) / 99.0  # 0..1
    start_delay = SLOW_START_DELAY + (FAST_START_DELAY - SLOW_START_DELAY) * t
    min_delay   = SLOW_MIN_DELAY   + (FAST_MIN_DELAY   - SLOW_MIN_DELAY)   * t
    return start_delay, min_delay

# ============== GPIO / Helpers ==============
def gpio_setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    for pin in (DIR1, STEP1, DIR2, STEP2,
                M1_M0, M1_M1, M1_M2,
                M2_M0, M2_M1, M2_M2,
                EN1, EN2):
        GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)
    # EN initial stromlos lassen bis motors_on()
    GPIO.output(EN1, GPIO.HIGH)
    GPIO.output(EN2, GPIO.HIGH)

def set_microstep_drv8825(m0, m1, m2, mode):
    """
    DRV8825 Microstep:
      1: L L L | 2: H L L | 4: L H L | 8: H H L | 16: L L H | 32: H L H
    """
    tbl = {1:(0,0,0), 2:(1,0,0), 4:(0,1,0), 8:(1,1,0), 16:(0,0,1), 32:(1,0,1)}
    if mode not in tbl:
        raise ValueError("Ungültiger Microstep-Mode (1,2,4,8,16,32)")
    GPIO.output([m0, m1, m2], tbl[mode])

def motors_on():
    GPIO.output(EN1, GPIO.LOW)   # aktiv
    GPIO.output(EN2, GPIO.LOW)

def motors_off():
    GPIO.output(EN1, GPIO.HIGH)  # stromlos
    GPIO.output(EN2, GPIO.HIGH)

def leave_en_pulled_up():
    """EN als Input mit Pull-Up hinterlassen (verhindert Floating nach Script-Ende)."""
    GPIO.setup(EN1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(EN2, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# ============== Bewegungsprofil (S-Kurve) ==============
def ease_delay(i, total, start_delay, min_delay, accel_steps):
    if total <= 0:
        return start_delay
    if i < accel_steps:
        t = i / max(1, accel_steps)
        return min_delay + (start_delay - min_delay) * 0.5 * (1 + math.cos(math.pi * t))
    if i >= total - accel_steps:
        t = (total - 1 - i) / max(1, accel_steps)
        return min_delay + (start_delay - min_delay) * 0.5 * (1 + math.cos(math.pi * t))
    return min_delay

def move_with_offset_quiet(steps, dir1, dir2, start_delay, min_delay, accel_steps, offset_sec, dither):
    """
    Leiser Lauf:
      - Motor2 startet sofort, Motor1 nach offset_sec
      - S-Kurven-Rampen + optionaler Dither
    """
    motors_on()
    GPIO.output(DIR1, dir1)
    GPIO.output(DIR2, dir2)

    t0 = time.perf_counter()
    for i in range(steps):
        base_d = ease_delay(i, steps, start_delay, min_delay, accel_steps)
        if dither:
            base_d += random.uniform(-dither, dither)

        GPIO.output(STEP2, GPIO.HIGH)
        if (time.perf_counter() - t0) >= offset_sec:
            GPIO.output(STEP1, GPIO.HIGH)
        time.sleep(base_d)

        GPIO.output(STEP2, GPIO.LOW)
        if (time.perf_counter() - t0) >= offset_sec:
            GPIO.output(STEP1, GPIO.LOW)
        time.sleep(base_d)

# ============== CLI & Main ==============
def parse_args():
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

if __name__ == "__main__":
    args = parse_args()

    dir1_level = CW if args.dir1 == "CW" else CCW
    dir2_level = CW if args.dir2 == "CW" else CCW
    START_DELAY, MIN_DELAY = map_speed_to_delays(args.speed)

    gpio_setup()
    try:
        set_microstep_drv8825(M1_M0, M1_M1, M1_M2, args.microstep)
        set_microstep_drv8825(M2_M0, M2_M1, M2_M2, args.microstep)

        steps_per_rev = BASE_SPR * args.microstep
        steps = int(round((args.degrees / 360.0) * steps_per_rev))
        if steps > 0:
            move_with_offset_quiet(
                steps=steps,
                dir1=dir1_level, dir2=dir2_level,
                start_delay=START_DELAY, min_delay=MIN_DELAY,
                accel_steps=args.accel, offset_sec=args.offset, dither=args.dither
            )

        # sicher stromlos + Pull-Ups an EN behalten
        motors_off()
        leave_en_pulled_up()

    except KeyboardInterrupt:
        print("Abbruch durch Benutzer.")
        try:
            motors_off()
            leave_en_pulled_up()
        except Exception:
            pass
    finally:
        # KEIN GPIO.cleanup(): sonst verschwinden die Pull-Ups an EN wieder
        pass
