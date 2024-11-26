# Copyright (c) 2024 FHNW University of Applied Sciences and Arts Northwestern Switzerland
# See LICENSE

# Based on:
# https://github.com/openmv/openmv/blob/master/scripts/examples/04-Barcodes/find_datamatrices.py

import sensor
import time
import math
import json

sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.skip_frames(time=2000)

clock = time.clock()

UP, RIGHT, DOWN, LEFT = range(4)

LENS_CORR_ENABLED = False  # enable for 2.8mm lens

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


while True:
    clock.tick()

    img = sensor.snapshot()

    if LENS_CORR_ENABLED: img.lens_corr(1.8)

    matrices = img.find_datamatrices()

    if (len(matrices) > 0):
        matrix = matrices[0]

        img.draw_rectangle(matrix.rect(), color=RED)

        rotation = matrix.rotation()
        payload = matrix.payload()

        direction = to_direction(to_degrees(rotation))

        json_data = json.dumps([payload, direction])

        print(json_data)
