#include <functional>

void initControls();

void check_encoder(std::function<void(void)> onClockwise, std::function<void(void)> onCounterClockwise);

bool button_pressed();

bool rotary_pressed();