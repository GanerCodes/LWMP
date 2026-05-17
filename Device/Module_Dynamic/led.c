#define LATCH_D   100
#define CLOCK_DIV 2

static rmt_channel_handle_t tx_chan;
static rmt_encoder_handle_t bytes_encoder;

static void led_init(LedConf *ℭ) {
  if(ℭ->𝔇 == NULL) ℭ->𝔇 = ℭ->𝔇α;
  u32 hz  = APB_CLK_FREQ / CLOCK_DIV;
  u32 khz = hz / 1000;
  rmt_tx_channel_config_t    c_𝔠 = { .mem_block_symbols = SOC_RMT_MEM_WORDS_PER_CHANNEL,
                                     .clk_src           = SOC_MOD_CLK_APB,
                                     .gpio_num          = ℭ->p,
                                     .resolution_hz     = hz,
                                     .trans_queue_depth = 1 };
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

static u32 led_write_dur(LedConf *ℭ) {
  u32 b0 = (ℭ->t>>48&0xFFFF)+(ℭ->t>>32&0xFFFF),
      b1 = (ℭ->t>>16&0xFFFF)+(ℭ->t>> 0&0xFFFF);
  ret (b1>b0 ?b1: b0)*3*8/1000*ℭ->n + LATCH_D; }
static void led_show(LedConf *ℭ) {
  rmt_transmit_config_t t_𝔠 = { .loop_count      = 0,
                                .flags.eot_level = 0 };
  ESP_CHK(rmt_encoder_reset,bytes_encoder);
  ESP_CHK(rmt_transmit,tx_chan,bytes_encoder,ℭ->𝔇,3*ℭ->n,&t_𝔠);
  ℭ->write_finish_μ = micros()+led_write_dur(ℭ);
  ℭ->𝔇 = ℭ->𝔇==ℭ->𝔇α ?ℭ->𝔇β: ℭ->𝔇α; }
static void led_flush(LedConf *ℭ) {
  if(!tx_chan) return;
  // ESP_CHK(rmt_tx_wait_all_done,tx_chan,1000);
  loop { BAR;
         if(micros()>=ℭ->write_finish_μ) break; } }

static void led_flow(LedConf *ℭ) { led_flush(ℭ); led_show(ℭ); }