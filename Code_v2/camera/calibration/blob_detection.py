import sensor
import time

sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.skip_frames(time=2000)
sensor.set_auto_whitebal(False)

clock = time.clock()

BLUE = (10, 60, 0, 30, -75, -30)

KW_ARGS = {
   "pixels_threshold": 2_000,
   "area_threshold": 4_000,
   "merge": False,
}

while True:
    clock.tick()

    img = sensor.snapshot()

    for blob in img.find_blobs([BLUE], **KW_ARGS):
        img.draw_rectangle(blob.rect())

    print(clock.fps())
