# Copyright (c) 2024 FHNW University of Applied Sciences and Arts Northwestern Switzerland
# See LICENSE

# Based on:
# https://github.com/openmv/openmv/blob/master/scripts/examples/10-Bluetooth/ble_temperature.py

import bluetooth
import struct
import sensor
import time
import math
import json

from ble_advertising import advertising_payload
from micropython import const
from machine import LED
from pyb import Pin


sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.set_windowing((240, 240))
sensor.skip_frames(time=2000)

clock = time.clock()


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

        self.led = LED("LED_BLUE")

        self.set_ready(False)

        self.advertise()

    def irq(self, event, data):
        if event == IRQ_CENTRAL_CONNECT:
            conn_handle, _, _ = data
            self.led.on()
        elif event == IRQ_CENTRAL_DISCONNECT:
            conn_handle, _, _ = data
            self.led.off()
            self.advertise()

    def advertise(self, inverval_us=500_000):
        self.ble.gap_advertise(inverval_us, adv_data=self.payload)

    def send_data(self, data):
        data = (json.dumps(data) + "\r").encode("utf-8")
        self.ble.gatts_write(self.tx, data, True)

    def on_notify(self, data):
        if self.is_ready():
            self.send_data(data)
            self.set_ready(False)

    def set_ready(self, ready):
        ready = struct.pack("b", ready)
        self.ble.gatts_write(self.rx, ready)

    def is_ready(self):
        ready = self.ble.gatts_read(self.rx)
        ready, *_ = struct.unpack("b", ready)
        return bool(ready)


ble    = bluetooth.BLE()
sender = Sender(ble)

total = 0
count = 0

min = float("inf")
max = float("-inf")


while True:
    clock.tick()

    time_start = time.ticks_ms()

    sender.set_ready(False)
    sender.send_data([0, None])
    while (not sender.is_ready()): pass

    time_stop = time.ticks_ms()

    delta = time_stop - time_start

    total += delta
    count += 1

    avg = total / count

    min = delta if delta < min else min
    max = delta if delta > max else max

    print("time for roundtrip: ",
          int(avg), "ms (avg),\t",
          int(min), "ms (min),\t",
          int(max), "ms (max)")
