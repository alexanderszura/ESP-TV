#include <Adafruit_GFX.h>
#include <Adafruit_ST7789.h>
#include <SPI.h>
#include "display.h"

#define SCLK_PIN 22
#define MOSI_PIN 21
#define RES_PIN 32
#define DC_PIN 14
#define CS_PIN 5
#define BACK_LIGHT_PIN 13

#define WIDTH_RES 240
#define HEIGHT_RES 320

#define IMAGE_WIDTH 40
#define IMAGE_HEIGHT 40

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

// One decoded (and scaled) row of pixels. Only this row lives in RAM, never a full frame.
static uint16_t line_buffer[HEIGHT_RES > WIDTH_RES ? HEIGHT_RES : WIDTH_RES];

static inline uint16_t readIndex(const uint8_t*& data, uint8_t index_bytes) {
    uint16_t index = data[0];
    if (index_bytes == 2)
        index |= (uint16_t) data[1] << 8;
    data += index_bytes;
    return index;
}

void drawAnimationFrame(int16_t x, int16_t y, const Animation& animation, uint32_t frame, uint8_t scale) {
    if (animation.frame_count == 0 || scale == 0)
        return;

    const uint16_t width = animation.width;
    const uint16_t scaled_width = width * scale;

    if (scaled_width > sizeof(line_buffer) / sizeof(line_buffer[0]))
        return;

    const uint8_t* data = animation.data + animation.offsets[frame % animation.frame_count];
    const uint32_t total = (uint32_t) width * animation.height;

    // PackBits state: pixels left in the current run/literal block
    uint8_t remaining = 0;
    bool is_run = false;
    uint16_t run_color = 0;

    display.startWrite();
    display.setAddrWindow(x, y, scaled_width, animation.height * scale);

    uint16_t column = 0;
    for (uint32_t i = 0; i < total; i++) {
        if (remaining == 0) {
            uint8_t header = *data++;
            is_run = header < 0x80;
            remaining = is_run ? header + 1 : header - 0x7F;
            if (is_run)
                run_color = animation.palette[readIndex(data, animation.index_bytes)];
        }

        uint16_t pixel = is_run ? run_color : animation.palette[readIndex(data, animation.index_bytes)];
        remaining--;

        for (uint8_t s = 0; s < scale; s++)
            line_buffer[column * scale + s] = pixel;

        if (++column == width) {
            for (uint8_t s = 0; s < scale; s++)
                display.writePixels(line_buffer, scaled_width);
            column = 0;
        }
    }

    display.endWrite();
}

void playAnimation(int16_t x, int16_t y, const Animation& animation, uint32_t* frame, uint8_t scale) {
    if (!frame)
        return;

    drawAnimationFrame(x, y, animation, *frame, scale);
    (*frame)++;

    delay(animation.frame_ms);
}

// Must match thunder() in generate_weather_art.py:
// frame = rain_phase * THUNDER_STATES + state
//   state 0 = no lightning, then per bolt b: 1 + 3b flash, 2 + 3b bolt, 3 + 3b fading bolt
#define THUNDER_RAIN_PHASES 4
#define THUNDER_BOLTS 3
#define THUNDER_STATES (1 + 3 * THUNDER_BOLTS)

// Frames of calm between strikes (random in this range)
#define THUNDER_MIN_GAP 8
#define THUNDER_MAX_GAP 45

void playThunder(int16_t x, int16_t y, const Animation& animation, StormState* storm, uint8_t scale) {
    if (!storm)
        return;

    // Different frame layout (e.g. hand made art), just loop it
    if (animation.frame_count != THUNDER_RAIN_PHASES * THUNDER_STATES) {
        playAnimation(x, y, animation, &storm->tick, scale);
        return;
    }

    uint8_t state = 0;

    if (storm->bolt < 0 && storm->tick >= storm->next_strike) {
        storm->bolt = random(THUNDER_BOLTS);
        storm->step = 0;
        storm->flickers = random(3);  // 0-2 extra flashes, like real lightning
    }

    if (storm->bolt >= 0) {
        uint8_t base = 1 + 3 * storm->bolt;

        switch (storm->step) {
            case 0:  // flash, cloud lights up
                state = base;
                storm->step = 1;
                break;
            case 1:  // bolt
                state = base + 1;
                storm->step = storm->flickers > 0 ? 2 : 3;
                break;
            case 2:  // short dark gap before flickering again
                state = 0;
                storm->flickers--;
                storm->step = 0;
                break;
            default:  // fade out, then wait for the next strike
                state = base + 2;
                storm->bolt = -1;
                storm->next_strike = storm->tick + random(THUNDER_MIN_GAP, THUNDER_MAX_GAP + 1);
                break;
        }
    }

    uint8_t rain_phase = storm->tick % THUNDER_RAIN_PHASES;
    drawAnimationFrame(x, y, animation, rain_phase * THUNDER_STATES + state, scale);
    storm->tick++;

    delay(animation.frame_ms);
}