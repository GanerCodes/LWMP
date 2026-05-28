#define PAUSE_DUR_μ 2500

// #include "led_driver_bitbang.c"
// #include "led_driver_i2s.c" // incomplete
#include "led_driver_rmt.c"

static u8 _led_state = 0;
static void led_init(LedConf *ℭ) {
  // ESP_CHK(esp_wifi_set_promiscuous,false);
  if(ℭ->i > 1) ℭ->i = 0;
  driver_init(ℭ);
  _led_state |= 1; }
static void led_show(LedConf *ℭ) {
  if(!_led_state) led_init(ℭ);
  _led_state |= 2;
  ℭ->write_finish_μ = 𝝁+led_write_dur_μ(ℭ);
  driver_write(ℭ);
  ℭ->i ^= 1; }
static void led_flush(LedConf *ℭ) {
  if(_led_state < 3) ret;
  while(𝝁<=ℭ->write_finish_μ) sleep(1);
  u64 unpause_μ = 𝝁 + PAUSE_DUR_μ;
  while(𝝁<=unpause_μ) sleep(1);
  _led_state &= ~2; }
static void led_flow(LedConf *ℭ) {
  led_flush(ℭ);
  led_show(ℭ); }