// Copyright (c) 2024 FHNW University of Applied Sciences and Arts Northwestern Switzerland
// See LICENSE

// Based on:
// https://github.com/tamberg/fhnw-iot/blob/master/05/Arduino/nRF52840_UartBleCentral/nRF52840_UartBleCentral.ino
// https://github.com/adafruit/Adafruit_VS1053_Library/blob/master/examples/feather_player/feather_player.ino

#include "Adafruit_TinyUSB.h"
#include <bluefruit.h>
#include <ArduinoJson.h>
#include <SPI.h>
#include <SD.h>
#include <Adafruit_VS1053.h>

#define VS1053_RESET    -1
#define VS1053_CS        6
#define VS1053_DCS      10
#define CARDCS           5
#define VS1053_DREQ      9

#define BUTTON_PIN      11

#define NONE_DETECTED    0
#define LINE_DETECTED    1
#define CODE_CLOSE       2
#define CODE_BELOW       3

#define TIMEOUT       3000 // ms


char DIRECTIONS[] = {'N', 'O', 'S', 'W'};


uint16_t mtu;

unsigned long stoppedAt;

JsonDocument json;
JsonArray data;

DeserializationError error;

int i;
int state;
String code;
String track;
String message;

volatile bool stateReadyToProcess;

BLEClientUart uartServiceClient;

Adafruit_VS1053_FilePlayer musicPlayer = Adafruit_VS1053_FilePlayer(
  VS1053_RESET, VS1053_CS, VS1053_DCS, VS1053_DREQ, CARDCS);


void scanCallback(ble_gap_evt_adv_report_t* report) {
  if (Bluefruit.Scanner.checkReportForService(report, uartServiceClient)) {
    Serial.print("UART service detected. Connecting... ");
    Bluefruit.Central.connect(report);
  } else {
    Bluefruit.Scanner.resume();
  }
}

void connectCallback(uint16_t handle) {
  Serial.println("Connected");
  Serial.println("Discovering UART service...");
  if (uartServiceClient.discover(handle)) {
    uartServiceClient.enableTXD();
    uartServiceClient.write(1); // ready
    Serial.println("Ready");
  } else {
    Serial.print("Not found. Disconnecting... ");
    Bluefruit.disconnect(handle);
  }
}

void disconnectCallback(uint16_t handle, uint8_t reason) {
  Serial.print("Disconnected, reason = ");
  Serial.println(reason);
}

void onNoneDetected() {
  // do nothing
}

void onLineDetected() {
  musicPlayer.playFullFile("/beep-1.mp3");
}

void onCodeClose() {
  musicPlayer.playFullFile("/beep-2.mp3");
}

void onCodeBelow() {
  musicPlayer.playFullFile("/beep-3.mp3");

  if (!data.isNull()) {
    code = data[0].as<String>();
    i    = data[1].as<int>();

    track = (code.toInt() < 100)
      ? "/" + code + "_" + DIRECTIONS[i] + ".mp3"
      : "/" + code + ".mp3";
    
    if (millis() - stoppedAt > TIMEOUT) {
      Serial.print("Playing track ");
      Serial.println(track);

      musicPlayer.startPlayingFile(track.c_str());
    }
  }
}

void rxCallback(BLEClientUart &uartService) {
  message = uartService.readStringUntil('\r');
  error   = deserializeJson(json, message);

  Serial.print("Message: ");
  Serial.println(message);

  if (error) {
    Serial.println("JSON deserialization failed");
  } else {
    state = json[0];
    data  = json[1];

    switch (state) {
      case NONE_DETECTED: {
        onNoneDetected();
        break;
      }
      case LINE_DETECTED: {
        onLineDetected();
        break;
      }
      case CODE_CLOSE: {
        onCodeClose();
        break;
      }
      case CODE_BELOW: {
        onCodeBelow();
        break;
      }
    }
  }

  stateReadyToProcess = true;
}

void setup() {
  Serial.begin(115200);

  Serial.println("Setup");

  if (!musicPlayer.begin()) {
    Serial.println("VS1053 failed");
    while (1);
  }

  if (!SD.begin(CARDCS)) {
    Serial.println("SD failed");
    while (1);
  }

  musicPlayer.setVolume(8, 8); // lower => louder
  musicPlayer.useInterrupt(VS1053_FILEPLAYER_PIN_INT);

  Bluefruit.begin(0, 1);
  Bluefruit.setName("nRF52840");
  Bluefruit.setConnLedInterval(250); // ms

  uartServiceClient.begin();
  uartServiceClient.setRxCallback(rxCallback);

  Bluefruit.Central.setConnectCallback(connectCallback);
  Bluefruit.Central.setDisconnectCallback(disconnectCallback);

  mtu = Bluefruit.getMaxMtu(BLE_GAP_ROLE_CENTRAL);

  Bluefruit.Scanner.setRxCallback(scanCallback);
  Bluefruit.Scanner.restartOnDisconnect(true);
  Bluefruit.Scanner.setInterval(160, 80);
  Bluefruit.Scanner.useActiveScan(false);
  Bluefruit.Scanner.start(0);

  pinMode(BUTTON_PIN, INPUT);
}

void loop() {
  if (stateReadyToProcess) {
    if (musicPlayer.playingMusic) {
      if (digitalRead(BUTTON_PIN)) {
        Serial.println("Button pressed");
        musicPlayer.stopPlaying();
        stoppedAt = millis();
      }
    } else {
      // no audio => state processed
      Serial.println("State processed");
      stateReadyToProcess = false;
      uartServiceClient.write(1);
    }
  }
}
