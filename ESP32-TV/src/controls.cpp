#include <Arduino.h>
#include <functional>

// Push button
#define BUTTON_PIN -1

// Rotary Encoder
#define TRACK_A -1
#define TRACK_B -1
#define ROTARY_PUSH_PIN -1

volatile int encoderPos = 0;
int lastReportedPos = 0;

void _read_encoder();

void initControls() {
    pinMode(BUTTON_PIN, INPUT_PULLUP);

    pinMode(TRACK_A, INPUT_PULLUP);
    pinMode(TRACK_B, INPUT_PULLUP);
    pinMode(ROTARY_PUSH_PIN, INPUT_PULLUP);

    attachInterrupt(digitalPinToInterrupt(TRACK_A), _read_encoder, CHANGE);
    attachInterrupt(digitalPinToInterrupt(TRACK_B), _read_encoder, CHANGE);
}

void check_encoder(std::function<void(void)> onClockwise, std::function<void(void)> onCounterClockwise) {
    if (encoderPos != lastReportedPos) {
    
        if (encoderPos > lastReportedPos) {
            onClockwise();
        } else {
            onCounterClockwise();
        }
        
        lastReportedPos = encoderPos;
    }
}

bool button_pressed() {
    return digitalRead(BUTTON_PIN);
}

bool rotary_pressed() {
    return digitalRead(ROTARY_PUSH_PIN);
}

void _read_encoder() {
    static uint8_t old_AB = 0;

    old_AB <<= 2;
    old_AB |= (digitalRead(TRACK_A) << 1) | digitalRead(TRACK_B);
    
    switch (old_AB & 0x0F) {
        case 0x01: case 0x07: case 0x08: case 0x0E: encoderPos++; break;
        case 0x02: case 0x04: case 0x0B: case 0x0D: encoderPos--; break;
    }
}