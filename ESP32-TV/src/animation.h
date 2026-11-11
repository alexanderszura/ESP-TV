#pragma once

#include <Arduino.h>

// A palette + run-length compressed animation (see image_convert.py for the format)
struct Animation {
    uint16_t width;
    uint16_t height;
    uint8_t frame_count;
    uint16_t frame_ms;          // how long each frame stays on screen
    uint8_t index_bytes;        // 1 if palette <= 256 colours, otherwise 2

    const uint16_t* palette;    // RGB565 colours
    const uint8_t* data;        // compressed frames, back to back
    const uint32_t* offsets;    // start of each frame inside data
};
