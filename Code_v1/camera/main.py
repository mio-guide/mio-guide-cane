# Copyright (c) 2024 FHNW University of Applied Sciences and Arts Northwestern Switzerland
# See LICENSE

# Based on:
# https://github.com/openmv/openmv/blob/master/scripts/examples/04-Barcodes/find_datamatrices.py
# https://github.com/openmv/openmv/blob/master/scripts/examples/05-Feature-Detection/find_lines.py

import sensor
import time
import math
import json
from pyb import UART, Pin

sensor.reset()
sensor.set_pixformat(sensor.GRAYSCALE)
sensor.set_framesize(sensor.QVGA)
sensor.skip_frames(time=2000)

clock = time.clock()

uart = UART("LP1", 9600)

buzzer_pin = Pin("D0", Pin.OUT_PP)

last_time_code = 0   # in ms
last_time_tape = 0   # in ms

CODE_TIMEOUT = 2000  # in ms
TAPE_TIMEOUT = 750   # in ms

SHORT_BEEP = 0.05    # in s
LONG_BEEP  = 0.2     # in s

MAX_ANGLE_DIFF    = 2
MIN_DISTANCE_DIFF = 20

UP, RIGHT, DOWN, LEFT = range(4)

RED = (255, 0, 0)


def to_json(string):
    try:
        return json.loads(string)
    except ValueError:
        return None


def to_degrees(rad):
    return (180 * rad) / math.pi


def to_direction(angle):
    if angle >= 315 or angle < 45:
        return UP
    elif 315 > angle >= 255:
        return RIGHT
    elif 225 > angle >= 135:
        return DOWN
    elif 135 > angle >= 45:
        return LEFT


def buzzer_beep(duration):
    buzzer_pin.high()
    time.sleep(duration)
    buzzer_pin.low()


def short_buzzer_beep():
    buzzer_beep(SHORT_BEEP)


def long_buzzer_beep():
    buzzer_beep(LONG_BEEP)


def code_buzzer_beep():
    short_buzzer_beep()
    time.sleep(SHORT_BEEP)
    short_buzzer_beep()


def tape_buzzer_beep():
    long_buzzer_beep()


def scan_for_code(img):
    matrices = img.find_datamatrices(effort=240)

    if (len(matrices) > 0):
        matrix = matrices[0]

        img.draw_rectangle(matrix.rect(), color=RED)

        rotation = matrix.rotation()
        payload  = matrix.payload()

        direction = to_direction(to_degrees(rotation))

        json_data = json.dumps([payload, direction])

        return json_data


def scan_for_tape(img):
    lines = img.find_lines(threshold=1000, theta_margin=25, rho_margin=25)

    for i, line1 in enumerate(lines):
        for _, line2 in enumerate(lines[i + 1:]):

            distance_diff = abs(line1.rho() - line2.rho())

            angle_diff = abs(line1.theta() - line2.theta())
            angle_diff = min(angle_diff, 180 - angle_diff)

            if distance_diff >= MIN_DISTANCE_DIFF and angle_diff <= MAX_ANGLE_DIFF:

                img.draw_line(line1.line(), color=RED)
                img.draw_line(line2.line(), color=RED)

                return True


def is_code_timeout_over():
    return time.ticks_ms() - last_time_code > CODE_TIMEOUT


def is_tape_timeout_over():
    return time.ticks_ms() - last_time_code > TAPE_TIMEOUT + CODE_TIMEOUT \
       and time.ticks_ms() - last_time_tape > TAPE_TIMEOUT


while True:
    clock.tick()

    img = sensor.snapshot()

    if is_code_timeout_over():
        result = scan_for_code(img)

        if result:
            code_buzzer_beep()
            uart.write(result + "\r")
            last_time_code = time.ticks_ms()

        elif is_tape_timeout_over():
            result = scan_for_tape(img)

            if result:
                tape_buzzer_beep()
                last_time_tape = time.ticks_ms()

    print(clock.fps())

    buzzer_pin.low()
