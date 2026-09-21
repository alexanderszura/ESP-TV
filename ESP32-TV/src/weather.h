#include "network.h"

enum Weather {
    SUNNY,
    PARTIAL_CLOUD,
    CLOUD,
    DRIZZLE,
    RAINY,
    STORM,
    SNOW,

    UNKNOWN
};

struct WeatherData {
    Weather weather;

    const char* time;

    float temperature;
    float apparent_temperature;
    uint8_t humidity;

    bool is_day;

    uint8_t precipitation;
    
    float wind_speed;
    float wind_gusts;
};

WeatherData* fetch_current_weather();