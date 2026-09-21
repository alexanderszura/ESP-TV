uint16_t color(uint8_t red, uint8_t green, uint8_t blue);

void initDisplay();

void brightness(uint8_t brightness);

void playAnimation(uint8_t* x, uint8_t* y, uint64_t* animation_frame, const uint16_t* const bitmaps[], uint8_t bitmap_length, uint32_t wait_time_ms);