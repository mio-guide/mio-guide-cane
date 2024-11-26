# Copyright (c) 2024 FHNW University of Applied Sciences and Arts Northwestern Switzerland
# See LICENSE

import sensor, image, time

from pyb import Pin

sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.skip_frames(time = 2000)

clock = time.clock()

buzzer_pin = Pin("D0", Pin.OUT_PP)


def tone(freq):
    full_period = int(1e6 / freq)
    half_period = int(full_period / 2)

    buzzer_pin.high(); time.sleep_us(half_period)
    buzzer_pin.low();  time.sleep_us(half_period)


start = time.ticks_ms()

while (time.ticks_ms() - start < 500): tone(20)


while(True):
    clock.tick()
    img = sensor.snapshot()
    print(clock.fps())
