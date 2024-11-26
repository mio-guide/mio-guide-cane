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

#define VS1053_RESET -1
#define VS1053_CS     6
#define VS1053_DCS   10
#define CARDCS        5
#define VS1053_DREQ   9

JsonDocument doc;

uint16_t mtu; // Maximum Transmission Unit
BLEClientUart uartServiceClient;

String DIRECTIONS[] = {"UP", "RIGHT", "DOWN", "LEFT"};

Adafruit_VS1053_FilePlayer musicPlayer = Adafruit_VS1053_FilePlayer(VS1053_RESET, VS1053_CS, VS1053_DCS, VS1053_DREQ, CARDCS);

void scanCallback(ble_gap_evt_adv_report_t* report) {
  if (Bluefruit.Scanner.checkReportForService(report, uartServiceClient)) {
    Serial.printBufferReverse(report->peer_addr.addr, 6, ':');
    Serial.println();
    Serial.print("UART service detected. Connecting ... ");
    Bluefruit.Central.connect(report);
  } else {
    Bluefruit.Scanner.resume();
  }
}

void connectCallback(uint16_t handle) {
  Serial.println("Connected");

  Serial.println("Discovering UART service... ");
  if (uartServiceClient.discover(handle)) {
    uartServiceClient.enableTXD();
    Serial.println("Ready to receive from peripheral");
  } else {
    Serial.println("Not found. Disconnecting...");
    Bluefruit.disconnect(handle);
  }  
}

void disconnectCallback(uint16_t handle, uint8_t reason) {
  Serial.print("Disconnected, reason = ");
  Serial.println(reason);
}

void setup() {
  Serial.begin(9600);

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

  Bluefruit.Central.setConnectCallback(connectCallback);
  Bluefruit.Central.setDisconnectCallback(disconnectCallback);

  mtu = Bluefruit.getMaxMtu(BLE_GAP_ROLE_CENTRAL);

  Bluefruit.Scanner.setRxCallback(scanCallback);
  Bluefruit.Scanner.restartOnDisconnect(true);
  Bluefruit.Scanner.setInterval(160, 80);
  Bluefruit.Scanner.useActiveScan(false);
  Bluefruit.Scanner.start(0);
}

void loop() {
  if (Bluefruit.Central.connected()) {
    if (uartServiceClient.discovered()) {
      if (uartServiceClient.available()) {
        String data = uartServiceClient.readString();
        DeserializationError error = deserializeJson(doc, data);

        if (error) {
          Serial.println("JSON deserialization failed...");
        } else {
          String code = doc[0];
          int direction = doc[1];

          String track = "/" + code + "_" + direction + ".mp3";

          Serial.print("Code facing ");
          Serial.print(DIRECTIONS[direction]);
          Serial.print(", Playing track ");
          Serial.println(track);

          musicPlayer.playFullFile(track.c_str());
        }
      }
    }
  }
}
