// Copyright (c) 2024 FHNW University of Applied Sciences and Arts Northwestern Switzerland
// See LICENSE

// Based on:
// https://github.com/tamberg/fhnw-iot/blob/master/05/Arduino/nRF52840_UartBleCentral/nRF52840_UartBleCentral.ino

#include "Adafruit_TinyUSB.h"
#include <bluefruit.h>
#include <ArduinoJson.h>

uint16_t mtu; // Maximum Transmission Unit
BLEClientUart uartServiceClient;

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

void rxCallback(BLEClientUart &uartService) {
  Serial.print("rx: ");
  if (uartService.available()) {
    String data = uartService.readString();

    JsonDocument doc;

    DeserializationError error = deserializeJson(doc, data);

    if (error) {
      Serial.print("deserialization failed...");
    } else {
      const char *code = doc[0];
      int direction = doc[1];

      Serial.print("code: ");
      Serial.print(code);
      Serial.print(", direction: ");
      Serial.print(direction);
    }
  }
  Serial.println();
}

void setup() {
  Serial.begin(9600);
  while (!Serial) { delay(10); } // only if usb connected

  Serial.println("Setup");

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
}

void loop() {}
