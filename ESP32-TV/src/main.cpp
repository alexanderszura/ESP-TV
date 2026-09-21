#include <Arduino.h>
#include "display.h"

void setup() {
  Serial.begin(115200);
  Serial.println("Starting display...");
  initDisplay();
}

void loop() {
  delay(1000);
}
