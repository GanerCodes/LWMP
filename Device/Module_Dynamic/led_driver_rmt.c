static rmt_channel_handle_t tx_chan;
static rmt_encoder_handle_t bytes_encoder;

#define CLOCK_DIV 16

fast inline u8* get_led_buf(LedConf *ℭ) { ret ℭ->i ?ℭ->𝔇_β: ℭ->𝔇_α; }

static void driver_init(LedConf *ℭ) {
  u8* 𝔇 = get_led_buf(ℭ);
  u32 hz  = APB_CLK_FREQ / CLOCK_DIV;
  u32 khz = hz / 1000;
  rmt_tx_channel_config_t    c_𝔠 = { .mem_block_symbols = 8*SOC_RMT_MEM_WORDS_PER_CHANNEL,
                                     .clk_src           = SOC_MOD_CLK_APB,
                                     .gpio_num          = ℭ->p,
                                     .resolution_hz     = hz,
                                     .trans_queue_depth = 1,
                                     .intr_priority     = 3,
                                     .flags = { .invert_out   = 0,
                                                .with_dma     = 0, // not supported on original esp32
                                                .io_loop_back = 0,
                                                .io_od_mode   = 0,
                                                .allow_pd     = 0 } };
  rmt_bytes_encoder_config_t e_𝔠 = { .bit0 = { .level0=1, .duration0=khz*(ℭ->t>>48 & 0xFFFF)/1e6,
                                               .level1=0, .duration1=khz*(ℭ->t>>32 & 0xFFFF)/1e6 },
                                     .bit1 = { .level0=1, .duration0=khz*(ℭ->t>>16 & 0xFFFF)/1e6,
                                               .level1=0, .duration1=khz*(ℭ->t>> 0 & 0xFFFF)/1e6 },
                                     .flags.msb_first = 1 };
  if(tx_chan) { ESP_CHK(rmt_disable    ,tx_chan);
                ESP_CHK(rmt_del_channel,tx_chan); }
  if(bytes_encoder) ESP_CHK(rmt_del_encoder,bytes_encoder);
  ESP_CHK(rmt_new_tx_channel,&c_𝔠,&tx_chan);
  ESP_CHK(rmt_enable,tx_chan);
  ESP_CHK(rmt_new_bytes_encoder,&e_𝔠,&bytes_encoder); }
static void driver_write(LedConf *ℭ) {
  rmt_transmit_config_t t_𝔠 = { .loop_count      = 0,
                                .flags.eot_level = 0 };
  ESP_CHK(rmt_encoder_reset,bytes_encoder);
  ESP_CHK(rmt_transmit,tx_chan,bytes_encoder,get_led_buf(ℭ),3*ℭ->n,&t_𝔠); }

/* // inside lw_thread.c
typedef struct { rmt_encoder_t basis;
                 rmt_encoder_t *bytes_encoder, *copy_encoder;
                 int state;
                 rmt_symbol_word_t reset_code; } rmt_led_strip_encoder_t;
IRAM_ATTR static size_t rmt_encode_led_strip(rmt_encoder_t *encoder, rmt_channel_handle_t channel, const void *primary_data, size_t data_size, rmt_encode_state_t *ret_state) {
  rmt_led_strip_encoder_t *led_encoder = __containerof(encoder, rmt_led_strip_encoder_t, basis);
  rmt_encoder_handle_t bytes_encoder = led_encoder->bytes_encoder;
  rmt_encoder_handle_t  copy_encoder = led_encoder-> copy_encoder;
  rmt_encode_state_t   session_state = RMT_ENCODING_RESET;
  rmt_encode_state_t   state         = RMT_ENCODING_RESET;
  size_t encoded_symbols = 0;
  switch(led_encoder->state) {
    case 0: // RGB data
      encoded_symbols += bytes_encoder->encode(bytes_encoder, channel, primary_data, data_size, &session_state);
      if(session_state & RMT_ENCODING_COMPLETE)
        led_encoder->state = 1; // switch to next state when current encoding session finished
      if(session_state & RMT_ENCODING_MEM_FULL) {
        state |= RMT_ENCODING_MEM_FULL;
        goto OUT; // yield if there's no free space for encoding artifacts
        }
    case 1: // reset code
      encoded_symbols += copy_encoder->encode(copy_encoder, channel, &led_encoder->reset_code,
                                              sizeof(led_encoder->reset_code), &session_state);
      if(session_state & RMT_ENCODING_COMPLETE) {
        led_encoder->state = RMT_ENCODING_RESET; // back to the initial encoding session
        state |= RMT_ENCODING_COMPLETE; }
      if(session_state & RMT_ENCODING_MEM_FULL) {
        state |= RMT_ENCODING_MEM_FULL;
        goto OUT; // yield if there's no free space for encoding artifacts
        } }
  OUT: *ret_state = state;
       return encoded_symbols; }
IRAM_ATTR static esp_err_t rmt_led_strip_encoder_reset(rmt_encoder_t *encoder) {
    rmt_led_strip_encoder_t *led_encoder = __containerof(encoder, rmt_led_strip_encoder_t, basis);
    rmt_encoder_reset(led_encoder->bytes_encoder);
    rmt_encoder_reset(led_encoder->copy_encoder);
    led_encoder->state = RMT_ENCODING_RESET;
    return ESP_OK; } */

/* #define ESP_OK 0

#define RMT_LED_STRIP_RESOLUTION_HZ 10000000 // 10MHz resolution, 1 tick = 0.1us (led strip needs a high resolution)

typedef struct { rmt_encoder_t basis;
                 rmt_encoder_t *bytes_encoder, *copy_encoder;
                 i32 state;
                 rmt_symbol_word_t reset_code; } rmt_led_strip_encoder_t;
typedef struct { u32 resolution; } led_strip_encoder_config_t;

static rmt_channel_handle_t led_chan;
static rmt_encoder_handle_t led_encoder;

static esp_err_t rmt_del_led_strip_encoder(rmt_encoder_t *encoder) {
    rmt_led_strip_encoder_t *led_encoder = __containerof(encoder, rmt_led_strip_encoder_t, basis);
    rmt_del_encoder(led_encoder->bytes_encoder);
    rmt_del_encoder(led_encoder->copy_encoder);
    f_free(led_encoder);
    return ESP_OK; }

static esp_err_t rmt_new_led_strip_encoder(const led_strip_encoder_config_t *config, rmt_encoder_handle_t *ret_encoder) {
    esp_err_t res = ESP_OK;
    rmt_led_strip_encoder_t *led_encoder = NULL;
    if(!(config && ret_encoder)) return 1;
    led_encoder = rmt_alloc_encoder_mem(sizeof(rmt_led_strip_encoder_t));
    if(!(led_encoder)) return 1;
    led_encoder->basis.encode = rmt_encode_led_strip;
    led_encoder->basis.del    = rmt_del_led_strip_encoder;
    led_encoder->basis.reset  = rmt_led_strip_encoder_reset;
    rmt_bytes_encoder_config_t bytes_encoder_config = {
        .bit0 = { .level0    = 1                                 ,
                  .duration0 = 0.3 * config->resolution / 1000000,
                  .level1    = 0                                 ,
                  .duration1 = 0.9 * config->resolution / 1000000  },
        .bit1 = { .level0    = 1                                 ,
                  .duration0 = 0.9 * config->resolution / 1000000,
                  .level1    = 0                                 ,
                  .duration1 = 0.3 * config->resolution / 1000000  },
        .flags.msb_first = 1 };
    ESP_CHK(rmt_new_bytes_encoder, &bytes_encoder_config, &led_encoder->bytes_encoder);
    rmt_copy_encoder_config_t copy_encoder_config = {};
    ESP_CHK(rmt_new_copy_encoder, &copy_encoder_config, &led_encoder->copy_encoder);

    u32 reset_ticks = config->resolution / 1000000 * 50 / 2; // reset code duration defaults to 50us
    led_encoder->reset_code = (rmt_symbol_word_t) {
        .level0    = 0          ,
        .duration0 = reset_ticks,
        .level1    = 0          ,
        .duration1 = reset_ticks };
    *ret_encoder = &led_encoder->basis;
    return ESP_OK;
err:
    if(led_encoder) {
      if(led_encoder->bytes_encoder) rmt_del_encoder(led_encoder->bytes_encoder);
      if(led_encoder-> copy_encoder) rmt_del_encoder(led_encoder-> copy_encoder);
      f_free(led_encoder); }
    return res; }

static void driver_init(LedConf *ℭ) {
  u32 hz  = APB_CLK_FREQ / CLOCK_DIV;
  u32 khz = hz / 1000;
  
  rmt_tx_channel_config_t tx_chan_config = {
      .clk_src = RMT_CLK_SRC_DEFAULT, // select source clock
      .gpio_num = ℭ->p,
      .mem_block_symbols = 64, // increase the block size can make the LED less flickering
      .resolution_hz = RMT_LED_STRIP_RESOLUTION_HZ,
      .trans_queue_depth = 1, // set the number of transactions that can be pending in the background
  };
  ESP_CHK(rmt_new_tx_channel, &tx_chan_config, &led_chan);
  led_strip_encoder_config_t encoder_config = { .resolution = RMT_LED_STRIP_RESOLUTION_HZ };
  ESP_CHK(rmt_new_led_strip_encoder, &encoder_config, &led_encoder);
  ESP_CHK(rmt_enable, led_chan); }
static void driver_write(LedConf *ℭ) {
  rmt_transmit_config_t tx_config = { .loop_count = 0 };
  rmt_transmit(led_chan, led_encoder, get_led_buf(ℭ), 3*ℭ->n, &tx_config); } */