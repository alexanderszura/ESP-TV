#include <Arduino.h>
#include "display.h"
#include "constrols.h"
#include "network.h"
#include "secrets.h"
#include "weather.h"
#include "bitmaps.h"

#define REFRESH_MIN 15

void setup() {
  Serial.begin(115200);
  Serial.println("Starting display...");

  initControls();
  initDisplay();
}

void loop() {
  connect(WIFI_SSID, WIFI_PASSWORD);

  start:
  while (isConnected()) {
    WeatherData* weather_data = fetch_current_weather();

    if (weather_data == NULL) {
      Serial.println("Error fetching weather data");
      delay(500);
      continue;
    }

    uint64_t frame = 0;
    u_int64_t start_time = millis();

    while (millis() - start_time < REFRESH_MIN * 60 * 1000) {
      switch (weather_data->weather) {
        case SUNNY:
          break;
        case PARTIAL_CLOUD:
          break;
        case CLOUD:
          break;
        case DRIZZLE:
          break;
        case RAINY:
          break;
        case STORM:
          playAnimation(0, 0, &frame, THUNDER, 2, 150);
          break;
        case SNOW:
          break;

        case UNKNOWN:
        default:
          Serial.println("Unknown weather pattern...");
          free(weather_data);
          
          goto start;
      }
    }

    free(weather_data);
  }

  Serial.println("Disconnected...");
}
