#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

bool isConnected() {
    return WiFi.status() == WL_CONNECTED;
}

bool connect(const char* ssid, const char* password) {
    WiFi.begin(ssid, password);

    for (int i = 0; i < 20; i++) {
        delay(500);
        if (isConnected())
            return true;
    }

    return false;
}

JsonDocument* request(const char* api_url) {
    if (!isConnected()) {
        Serial.print("Error making request... WiFi Status: ");
        Serial.println(WiFi.status());
        return NULL;
    }

    HTTPClient client;
    
    client.begin(api_url);

    int status_code = client.GET();

    // WiFi disconnected
    if (status_code <= 0) {
        Serial.print("Error code: ");
        Serial.println(status_code);
        return NULL;
    }

    String payload = client.getString();

    JsonDocument* doc = (JsonDocument*) malloc(sizeof(JsonDocument));
    if (doc == NULL) {
        Serial.println("Failed to allocate memory for a the json doc");
        return NULL;
    }

    DeserializationError error = deserializeJson(*doc, payload);

    if (error) {
        Serial.print("deserializeJson() failed: ");
        Serial.println(error.c_str());
        return NULL;
    }

    return doc;
}