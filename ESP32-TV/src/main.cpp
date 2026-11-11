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

    uint32_t frame = 0;
    StormState storm;
    uint32_t start_time = millis();

    while (millis() - start_time < REFRESH_MIN * 60 * 1000UL) {
      switch (weather_data->weather) {
        case SUNNY:
          playAnimation(0, 0, ANIM_SUNNY, &frame);
          break;
        case PARTIAL_CLOUD:
          playAnimation(0, 0, ANIM_PARTIAL_CLOUD, &frame);
          break;
        case CLOUD:
          playAnimation(0, 0, ANIM_CLOUD, &frame);
          break;
        case DRIZZLE:
          playAnimation(0, 0, ANIM_DRIZZLE, &frame);
          break;
        case RAINY:
          playAnimation(0, 0, ANIM_RAIN, &frame);
          break;
        case STORM:
          playThunder(0, 0, ANIM_THUNDER, &storm);
          break;
        case SNOW:
          playAnimation(0, 0, ANIM_SNOW, &frame);
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
