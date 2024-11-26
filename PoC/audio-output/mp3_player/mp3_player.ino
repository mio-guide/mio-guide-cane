// Copyright (c) 2024 FHNW University of Applied Sciences and Arts Northwestern Switzerland
// See LICENSE

// Based on:
// https://github.com/adafruit/Adafruit_VS1053_Library/blob/master/examples/feather_player/feather_player.ino

#include <SPI.h>
#include <SD.h>
#include <Adafruit_VS1053.h>

#define VS1053_RESET -1
#define VS1053_CS     6
#define VS1053_DCS   10
#define CARDCS        5
#define VS1053_DREQ   9

Adafruit_VS1053_FilePlayer musicPlayer = Adafruit_VS1053_FilePlayer(VS1053_RESET, VS1053_CS, VS1053_DCS, VS1053_DREQ, CARDCS);

void setup() {
  Serial.begin(115200);

  while (!Serial) { delay(1); }
  delay(500);

  if (!musicPlayer.begin()) {
    Serial.println("Couldn't find VS1053, do you have the right pins defined?");
    while (1);
  }

  Serial.println("VS1053 found");

  if (!SD.begin(CARDCS)) {
    Serial.println("SD failed, or not present");
    while (1);
  }

  Serial.println("SD OK!");

  musicPlayer.setVolume(10, 10); // lower => louder

  musicPlayer.useInterrupt(VS1053_FILEPLAYER_PIN_INT);
}

// intersection:
/*

  |
  |---
  |

*/

String DIRECTIONS[] = {"UP", "RIGHT", "DOWN", "LEFT"};

String data = "track1";

void loop() {
  for (int direction = 0; direction <= 3; direction++) {
    String track = "/" + data + "_" + direction + ".mp3";

    Serial.print("Playing track for code facing ");
    Serial.print(DIRECTIONS[direction]);
    Serial.println();

    musicPlayer.playFullFile(track.c_str());

    delay(1000);
  }

  delay(1000);
}
