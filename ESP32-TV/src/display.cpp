#include <Adafruit_GFX.h>
#include <Adafruit_ST7789.h>
#include <SPI.h>
#include "bitmaps.h"

#define SCLK_PIN 22
#define MOSI_PIN 21
#define RES_PIN 32
#define DC_PIN 14
#define CS_PIN 5
#define BACK_LIGHT_PIN 13

#define WIDTH_RES 240
#define HEIGHT_RES 320

Adafruit_ST7789 display = Adafruit_ST7789(CS_PIN, DC_PIN, RES_PIN);

void brightness(uint8_t brightness);

uint16_t color(uint8_t red, uint8_t green, uint8_t blue) {
    // Truncate bits, then scale
    return ((red >> 3) << 11) | ((green >> 2) << 5) | (blue >> 3);
}

void initDisplay() {
    SPI.begin(SCLK_PIN, -1, MOSI_PIN, CS_PIN);
    display.init(WIDTH_RES, HEIGHT_RES, SPI_MODE0);
}

void brightness(uint8_t brightness) {
    analogWrite(BACK_LIGHT_PIN, brightness);
}

void playAnimation(uint8_t* x, uint8_t* y, uint64_t* animation_frame, uint16_t* bitmaps[], uint8_t bitmap_length, uint32_t wait_time_ms) {
    if (!x || !y || !animation_frame || !bitmaps)
        return;

    display.drawRGBBitmap(*x, *y, bitmaps[*animation_frame % bitmap_length], IMAGE_WIDTH * SCALE_FACTOR, IMAGE_HEIGHT * SCALE_FACTOR);

    delay(wait_time_ms);
}