# Copyright (c) 2024 FHNW University of Applied Sciences and Arts Northwestern Switzerland
# See LICENSE

# Based on:
# https://github.com/openmv/openmv/blob/master/scripts/examples/05-Feature-Detection/find_lines.py

import sensor
import time
from pyb import Pin

sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.skip_frames(time=2000)

LENS_CORR_ENABLED = False  # enable for 2.8mm lens

RED = (255, 0, 0)

MAX_ANGLE_DIFF = 2
MIN_DISTANCE_DIFF = 20

BUZZ_DURATION = 250  # in ms

buzzer_pin = Pin("D0", Pin.OUT_PP)

last_buzz = -1

clock = time.clock()

while True:
    clock.tick()

    img = sensor.snapshot()

    if LENS_CORR_ENABLED: img.lens_corr(1.8)

    lines = img.find_lines(threshold=1000, theta_margin=25, rho_margin=25)

    tape_detected = False  # tape := two parallel lines not too close

    for i, line1 in enumerate(lines):
        for _, line2 in enumerate(lines[i + 1:]):

            distance_diff = abs(line1.rho() - line2.rho())

            angle_diff = abs(line1.theta() - line2.theta())
            angle_diff = min(angle_diff, 180 - angle_diff)

            if distance_diff >= MIN_DISTANCE_DIFF and angle_diff <= MAX_ANGLE_DIFF:

                img.draw_line(line1.line(), color=RED)
                img.draw_line(line2.line(), color=RED)

                last_buzz = time.ticks_ms()
                buzzer_pin.high()

                tape_detected = True
                break

        if tape_detected: break

    if not tape_detected and time.ticks_ms() - last_buzz > BUZZ_DURATION: buzzer_pin.low()

    print("FPS:", int(clock.fps()), "\t", "Tape detected?", "Yes" if tape_detected else "No")
