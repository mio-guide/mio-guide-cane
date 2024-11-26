# Copyright (c) 2024 FHNW University of Applied Sciences and Arts Northwestern Switzerland
# See LICENSE

# Based on:
# https://github.com/openmv/openmv/blob/master/scripts/examples/02-Image-Processing/02-Color-Tracking/single_color_rgb565_blob_tracking.py
# https://github.com/openmv/openmv/blob/master/scripts/examples/04-Barcodes/find_datamatrices.py
# https://github.com/openmv/openmv/blob/master/scripts/examples/10-Bluetooth/ble_temperature.py

import bluetooth
import struct
import sensor
import time
import math
import json

from ble_advertising import advertising_payload
from micropython import const


sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.set_windowing((240, 240))
sensor.skip_frames(time=2000)
sensor.set_auto_whitebal(False)  # important !

clock = time.clock()


# environment

PROD = False


# directions

UP, RIGHT, DOWN, LEFT = range(4)


# colors

RED    = (255,   0,   0)
GREEN  = (0,   255,   0)
BLUE   = (0,     0, 255)


# states

NONE_DETECTED, \
LINE_DETECTED, \
CODE_CLOSE,    \
CODE_BELOW     = range(4)


# line detection

RED_THRESHOLDS  = (5, 35,  10, 60, -10,  40)
BLUE_THRESHOLDS = (5, 35, -15, 50, -80, -20)

LINE_KW_PARAMS = {
    "pixels_threshold": 2_000,
    "area_threshold":   4_000,
    "merge":            True
}


# marker detection

GREEN_THRESHOLDS = (40, 100, -70, -15, 10, 65)
MARKER_DENSITY   = 0.4

MARKER_KW_PARAMS = {
    "pixels_threshold": 100,
    "area_threshold":   100,
    "merge":            False
}


# code detection

EFFORT = 240


# bluetooth

IRQ_CENTRAL_CONNECT    = const(1)
IRQ_CENTRAL_DISCONNECT = const(2)

UART_UUID = bluetooth.UUID('6E400001-B5A3-F393-E0A9-E50E24DCCA9E')

UART_TX = (
    bluetooth.UUID('6E400003-B5A3-F393-E0A9-E50E24DCCA9E'),
    bluetooth.FLAG_READ | bluetooth.FLAG_NOTIFY
)
UART_RX = (
    bluetooth.UUID('6E400002-B5A3-F393-E0A9-E50E24DCCA9E'),
    bluetooth.FLAG_WRITE
)

UART_SERVICE = (UART_UUID, (UART_TX, UART_RX))


class Sender:
    def __init__(self, ble, name="camera"):
        self.ble = ble
        self.ble.active(True)
        self.ble.irq(self.irq)

        ((self.tx, self.rx),) = self.ble.gatts_register_services([UART_SERVICE])
        self.payload = advertising_payload(name=name, services=[UART_UUID])

        self.conn_handle = None
        self.set_ready(False)
        self.advertise()

    def irq(self, event, data):
        if event == IRQ_CENTRAL_CONNECT:
            self.conn_handle, _, _ = data
        elif event == IRQ_CENTRAL_DISCONNECT:
            self.conn_handle = None
            self.advertise()

    def advertise(self, inverval_us=125_000):
        self.ble.gap_advertise(inverval_us, adv_data=self.payload)

    def send_data(self, data):
        data = (json.dumps(data) + "\r").encode("utf-8")
        self.ble.gatts_write(self.tx, data)

    def send_notify(self):
        self.ble.gatts_notify(self.conn_handle, self.tx)

    def on_notify(self, data):
        if self.is_ready():
            self.set_ready(False)
            self.send_data(data)
            self.send_notify()

    def set_ready(self, ready):
        ready = struct.pack("b", ready)
        self.ble.gatts_write(self.rx, ready)

    def is_ready(self):
        ready = self.ble.gatts_read(self.rx)
        ready, *_ = struct.unpack("b", ready)
        return bool(ready)

    def is_connected(self):
        return bool(self.conn_handle)


class State:
    def __init__(self, state=NONE_DETECTED, data=None):
        self.state     = state
        self.data      = data
        self.listeners = []

    def __str__(self):
        return "{ state: " + str(self.state) + ", data: " + str(self.data) + " }"

    def subscribe(self, listener):
        self.listeners.append(listener)

    def update(self, state, data=None):
        self.state = state
        self.data  = data
        self.notify()

    def notify(self):
        for listener in self.listeners:
            listener.on_notify([self.state, self.data])


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


def to_roi(markers):
    xs = list(map(lambda m: m.x(), markers))
    ys = list(map(lambda m: m.y(), markers))

    x1, y1 = min(xs), min(ys)
    x2, y2 = max(xs), max(ys)

    return x1, y1, (x2 - x1), (y2 - y1)


def find_lines(img):
    blue_lines = []
    red_lines  = []

    for blob in img.find_blobs(
        [
            BLUE_THRESHOLDS,
            RED_THRESHOLDS
        ],
        **LINE_KW_PARAMS
    ):
        if blob.code() == 1: blue_lines.append(blob)
        if blob.code() >= 2: red_lines.append(blob)

        if not PROD: img.draw_rectangle(blob.rect(), color=GREEN)

    return red_lines, blue_lines


def line_below(lines, markers):
    red_lines, blue_lines = lines
    return len(blue_lines) > 0


def find_markers(img):
    markers = []

    for blob in img.find_blobs(
        [GREEN_THRESHOLDS],
        **MARKER_KW_PARAMS
    ):
        if blob.density() > MARKER_DENSITY:
            markers.append(blob)

            if not PROD: img.draw_rectangle(blob.rect(), color=RED)

    return markers


def code_close(lines, markers):
    red_lines, blue_lines = lines
    return len(red_lines) > 0 \
        or len(markers)   > 0


def code_below(lines, markers):
    return len(markers) >= 4


def find_code(img, roi):
    for angle in range(0, 360, 90):
        img = img.rotation_corr(z_rotation=angle)
        codes = img.find_datamatrices(effort=EFFORT, roi=roi)

        if codes:
            code, *_ = codes

            if not PROD: img.draw_rectangle(code.rect(), color=BLUE)

            payload  = code.payload()
            rotation = code.rotation()
            rotation = to_degrees(rotation)
            rotation = (rotation + angle) % 360

            direction = to_direction(rotation)

            return [payload, direction]


def code_below_routine(img, roi):
    data = find_code(img, roi)
    data = data if data else state.data
    state.update(CODE_BELOW, data)


def code_close_routine(img):
    state.update(CODE_CLOSE)


def line_routine(img):
    state.update(LINE_DETECTED)


def none_routine(img):
    state.update(NONE_DETECTED)


ble    = bluetooth.BLE()
sender = Sender(ble)
state  = State()

state.subscribe(sender)


while True:

    if PROD and not sender.is_connected():
        time.sleep_ms(100)
        continue

    clock.tick()

    img = sensor.snapshot()

    lines   = find_lines(img)
    markers = find_markers(img)

    if   code_below(lines, markers): code_below_routine(img, to_roi(markers))
    elif code_close(lines, markers): code_close_routine(img)
    elif line_below(lines, markers): line_routine(img)
    else:                            none_routine(img)

    print("fps:", int(clock.fps()), "state:", state)
