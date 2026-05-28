static rmt_channel_handle_t tx_chan;
static rmt_encoder_handle_t bytes_encoder;

#define CLOCK_DIV 10

fast inline u8* get_led_buf(LedConf *ℭ) {
  ret ℭ->i ?ℭ->𝔇_β: ℭ->𝔇_α; }
static u32 led_write_dur_μ(LedConf *ℭ) { // 󰤱 timing math doesn't respect truncation to frequencies but it works fine
  u32 w0 = (ℭ->t>>48&0xFFFF)+(ℭ->t>>32&0xFFFF),
      w1 = (ℭ->t>>16&0xFFFF)+(ℭ->t>> 0&0xFFFF);
  ret ((u64)(w0>w1 ?w0: w1)*8*3*ℭ->n + ℭ->lch)/1000; }

static void driver_init(LedConf *ℭ) {
  u8* 𝔇 = get_led_buf(ℭ);
  u32 hz  = APB_CLK_FREQ/CLOCK_DIV;
  u32 khz = APB_CLK_FREQ/(1000*CLOCK_DIV);
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