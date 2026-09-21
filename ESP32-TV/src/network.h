#include <ArduinoJson.h>

bool isConnected();
bool connect(const char* ssid, const char* password);

JsonDocument* request(const char* api_url);