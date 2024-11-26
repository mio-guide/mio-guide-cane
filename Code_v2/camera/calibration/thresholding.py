import sensor
import time

sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.skip_frames(time=2000)
sensor.set_auto_whitebal(False)

clock = time.clock()

BLUE = (10, 60, 0, 30, -75, -30)

while True:
    clock.tick()

    img = sensor.snapshot()
    img.binary([BLUE])

    print(clock.fps())
