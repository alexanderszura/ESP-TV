#pragma once

#include "animation.h"

uint16_t color(uint8_t red, uint8_t green, uint8_t blue);

void initDisplay();

void brightness(uint8_t brightness);

// Draws one frame (frame % frame_count) of a compressed animation at (x, y).
// scale draws every pixel as a scale x scale block (1 = original size).
void drawAnimationFrame(int16_t x, int16_t y, const Animation& animation, uint32_t frame, uint8_t scale = 1);

// Draws the frame, waits animation.frame_ms, then advances *frame.
void playAnimation(int16_t x, int16_t y, const Animation& animation, uint32_t* frame, uint8_t scale = 1);

// Keeps track of the lightning between calls to playThunder
struct StormState {
    uint32_t tick = 0;          // frames drawn so far (drives the rain)
    uint32_t next_strike = 0;   // tick when the next strike starts
    int8_t bolt = -1;           // bolt currently striking, -1 = none
    uint8_t step = 0;           // position inside the current strike
    uint8_t flickers = 0;       // extra flashes left in the current strike
};

// Like playAnimation, but lightning strikes at random times, with a random bolt and random flicker.
// Expects the frame layout made by thunder() in generate_weather_art.py.
void playThunder(int16_t x, int16_t y, const Animation& animation, StormState* storm, uint8_t scale = 1);
