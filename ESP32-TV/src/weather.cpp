#include <ArduinoJson.h>
#include "network.h"
#include "weather.h"

// https://open-meteo.com/en/docs
const char* WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast?latitude=44.2298&longitude=-76.481&current=temperature_2m,apparent_temperature,is_day,weather_code,relative_humidity_2m,precipitation,wind_speed_10m,wind_gusts_10m&timezone=auto&forecast_days=1";

Weather WMO_to_Weather(int code) {
    switch (code) {
        // Clear
        case 0:
            return SUNNY;

        // Mainly clear, partly cloudy, overcast
        case 1:
        case 2:
            return PARTIAL_CLOUD;

        case 3:
            return CLOUD;

        // Drizzle
        case 51:
        case 53:
        case 55:
        case 56:
        case 57:
            return DRIZZLE;

        // Rain
        case 61:
        case 63:
        case 65:
        case 66:
        case 67:
            return RAINY;

        // Snow
        case 71:
        case 73:
        case 75:
        case 77:
        case 85:
        case 86:
            return SNOW;

        // Thunderstorms
        case 95:
        case 96:
        case 99:
            return STORM;

        default:
            return UNKNOWN;
    }
}

WeatherData* fetch_current_weather() {
    JsonDocument* payload = request(WEATHER_API_URL);

    if (payload == NULL)
        return NULL;

    JsonObject api_data = (*payload)["data"].as<JsonObject>();

    WeatherData* data = (WeatherData*) malloc(sizeof(WeatherData));

    if (data == NULL) {
        Serial.println("Failed to allocate memory for weather");
        return NULL;
    }

    data->weather = WMO_to_Weather(api_data["weather_code"]);
    
    data->time = api_data["time"];

    data->temperature = api_data["temperature_2m"];
    data->apparent_temperature = api_data["apparent_temperature"];

    data->is_day = api_data["is_day"];
    
    data->precipitation = api_data["precipitation"];

    data->wind_speed = api_data["wind_speed_10m"];
    data->wind_gusts = api_data["wind_gusts_10m"];

    free(payload);

    return data;
}