// Copyright (c) 2024 FHNW University of Applied Sciences and Arts Northwestern Switzerland
// See LICENSE

// Based on:
// https://github.com/tamberg/fhnw-iot/blob/master/05/Arduino/nRF52840_UartBlePeripheral/nRF52840_UartBlePeripheral.ino

#include "Adafruit_TinyUSB.h"
#include <bluefruit.h>

uint8_t const uartServiceUUID[]      = { 0x9E, 0xCA, 0xDC, 0x24, 0x0E, 0xE5, 0xA9, 0xE0, 0x93, 0xF3, 0xA3, 0xB5, 0x01, 0x00, 0x40, 0x6E };
uint8_t const rxCharacteristicUUID[] = { 0x9E, 0xCA, 0xDC, 0x24, 0x0E, 0xE5, 0xA9, 0xE0, 0x93, 0xF3, 0xA3, 0xB5, 0x02, 0x00, 0x40, 0x6E };
uint8_t const txCharacteristicUUID[] = { 0x9E, 0xCA, 0xDC, 0x24, 0x0E, 0xE5, 0xA9, 0xE0, 0x93, 0xF3, 0xA3, 0xB5, 0x03, 0x00, 0x40, 0x6E };

uint16_t mtu; // Maximum Transmission Unit
BLEService uartService = BLEService(uartServiceUUID);
BLECharacteristic rxCharacteristic = BLECharacteristic(rxCharacteristicUUID);
BLECharacteristic txCharacteristic = BLECharacteristic(txCharacteristicUUID);

void connectCallback(uint16_t handle) {
  char centralName[32] = { 0 };
  BLEConnection *connection = Bluefruit.Connection(handle);
  connection->getPeerName(centralName, sizeof(centralName));
  Serial.print(handle);
  Serial.print(", connected to ");
  Serial.print(centralName);
  Serial.println();
}

void disconnectCallback(uint16_t handle, uint8_t reason) {
  Serial.print(handle);
  Serial.print(" disconnected, reason = ");
  Serial.println(reason);
  Serial.println("Advertising ...");
}

void cccdCallback(uint16_t handle, BLECharacteristic* characteristic, uint16_t cccdValue) {
  if (characteristic->uuid == txCharacteristic.uuid) {
    Serial.print("UART 'Notify', ");
    if (characteristic->notifyEnabled()) {
      Serial.println("enabled");
    } else {
      Serial.println("disabled");
    }
  }
}

void writeCallback(uint16_t handle, BLECharacteristic* characteristic, uint8_t* rxData, uint16_t len) {
  if (characteristic->uuid == rxCharacteristic.uuid) {
    Serial.print("rx: ");
    int i = 0;
    while (i < len) {
      Serial.print((char) rxData[i]);
      i++;
    }
    Serial.print("\n");
  }
}

void setupUartService() {
  uartService.begin();

  txCharacteristic.setProperties(CHR_PROPS_NOTIFY);
  txCharacteristic.setPermission(SECMODE_OPEN, SECMODE_NO_ACCESS);
  txCharacteristic.setMaxLen(mtu);
  txCharacteristic.setCccdWriteCallback(cccdCallback);
  txCharacteristic.begin();

  rxCharacteristic.setProperties(CHR_PROPS_WRITE | CHR_PROPS_WRITE_WO_RESP);
  rxCharacteristic.setPermission(SECMODE_NO_ACCESS, SECMODE_OPEN);
  rxCharacteristic.setMaxLen(mtu);
  rxCharacteristic.setWriteCallback(writeCallback, true);
  rxCharacteristic.begin();
}

void startAdvertising() {
  Bluefruit.Advertising.addFlags(BLE_GAP_ADV_FLAGS_LE_ONLY_GENERAL_DISC_MODE);
  Bluefruit.Advertising.addTxPower();
  Bluefruit.Advertising.addService(uartService);
  Bluefruit.Advertising.addName();

  const int fastModeInterval = 32;  // * 0.625 ms = 20 ms
  const int slowModeInterval = 244; // * 0.625 ms = 152.5 ms
  const int fastModeTimeout = 30;   // s
  Bluefruit.Advertising.restartOnDisconnect(true);
  Bluefruit.Advertising.setInterval(fastModeInterval, slowModeInterval);
  Bluefruit.Advertising.setFastTimeout(fastModeTimeout);

  Bluefruit.Advertising.start(0);
  Serial.println("Advertising ...");
}

void setup() {
  Serial.begin(9600);
  Serial1.begin(9600);

  Serial.println("Setup");
  
  Bluefruit.begin();
  Bluefruit.setName("nRF52840");
  Bluefruit.Periph.setConnectCallback(connectCallback);
  Bluefruit.Periph.setDisconnectCallback(disconnectCallback);

  mtu = Bluefruit.getMaxMtu(BLE_GAP_ROLE_PERIPH);

  setupUartService();
  startAdvertising();
}

void loop() {
  if (Bluefruit.connected()) {
    if (Serial1.available()) {
      String msg = Serial1.readStringUntil('\r');
      if (txCharacteristic.notify(msg.c_str())) {
        Serial.print("tx: ");
        Serial.println(msg);
      } else {
        Serial.println("tx: Notify error.");
      }
    }
  }
  delay(200); // ms
}