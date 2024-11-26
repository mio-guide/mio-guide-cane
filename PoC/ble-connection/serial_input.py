# Copyright (c) 2024 FHNW University of Applied Sciences and Arts Northwestern Switzerland
# See LICENSE

import time
import json
import random
from pyb import UART

uart = UART("LP1", 9600)

while True:
    msg = json.dumps(["track1", random.randint(0, 3)])
    uart.write(msg + "\r")
    time.sleep_ms(1000)
