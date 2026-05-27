// 󰤱 this dont work

static i2s_chan_handle_t ws_i2s_chan;

static void i2s_translate(u8 *𝔇, u8 *𝔅, LedConf *ℭ) { // 󰤱 prob just use a lut lol
  𝔅[0] = 0;
  for(u32 i=0; i<3*ℭ->n; i++) {
    u8 𝔡 = 𝔇[i];
    u32 b = 3*(i<<3);
    for(u8 o=0; o<8; o++) {
      u8 𝔢 = (𝔡>>(7-o))&1 ?0b110: 0b100;
      u32 p = (b+3*o)>>3;
      switch(o) { case 0: 𝔅[p  ] |= 𝔢<<5;
                          𝔅[p+1]  = 𝔅[p+2] = 0;
                  base 1: 𝔅[p  ] |= 𝔢<<2;
                  base 2: 𝔅[p  ] |= 𝔢>>1;
                          𝔅[p+1] |= (𝔢&1)<<7;
                  base 3: 𝔅[p  ] |= 𝔢<<4;
                  base 4: 𝔅[p  ] |= 𝔢<<1;
                  base 5: 𝔅[p  ] |= 𝔢>>2;
                          𝔅[p+1] |= (𝔢&3)<<6;
                  base 6: 𝔅[p  ] |= 𝔢<<3;
                  base 7: 𝔅[p  ] |= 𝔢<<0; } } } }

static void driver_init(LedConf *ℭ) {
  i2s_chan_config_t chan_cfg = { .id            = 0,
                                 .role          = I2S_ROLE_MASTER,
                                 .dma_desc_num  = 4,
                                 .dma_frame_num = 3*3*ℭ->n,
                                 .auto_clear    = true };
  ESP_CHK(i2s_new_channel, &chan_cfg, &ws_i2s_chan, NULL);
  /* i2s_std_config_t std_cfg = {
    .clk_cfg  = { .sample_rate_hz = 75000,
                  .clk_src        = I2S_CLK_SRC_DEFAULT,
                  .mclk_multiple  = I2S_MCLK_MULTIPLE_256 },
    .slot_cfg = { .data_bit_width = I2S_DATA_BIT_WIDTH_16BIT,
                  .slot_bit_width = I2S_SLOT_BIT_WIDTH_16BIT,
                  .slot_mode      = I2S_SLOT_MODE_STEREO,
                  .slot_mask      = I2S_STD_SLOT_BOTH,
                  .ws_width       = 16,
                  .ws_pol         = false,
                  .bit_shift      = true },
    // .slot_cfg = { .data_bit_width = I2S_DATA_BIT_WIDTH_8BIT,
    //               .slot_bit_width = I2S_SLOT_BIT_WIDTH_8BIT,
    //               .slot_mode      = I2S_SLOT_MODE_MONO,
    //               .slot_mask      = I2S_STD_SLOT_LEFT,
    //               .ws_width       = 8,
    //               .ws_pol         = false,
    //               .bit_shift      = false },
    .gpio_cfg = { .mclk         = I2S_GPIO_UNUSED,
                  .bclk         = I2S_GPIO_UNUSED,
                  .ws           = I2S_GPIO_UNUSED,
                  .dout         = ℭ->p,
                  .din          = I2S_GPIO_UNUSED,
                  .invert_flags = { .mclk_inv = false,
                                    .bclk_inv = false,
                                    .ws_inv   = false } } };
  i2s_chan_config_t chan_cfg = { .id            = 0,
                                 .role          = I2S_ROLE_MASTER,
                                 .dma_desc_num  = 8,
                                 .dma_frame_num = 512,
                                 .auto_clear    = true }; */
  i2s_std_config_t std_cfg =
    { .clk_cfg  = { .sample_rate_hz = 75000,
                    .clk_src        = I2S_CLK_SRC_DEFAULT,
                    .mclk_multiple  = I2S_MCLK_MULTIPLE_256 },
      .slot_cfg = { .data_bit_width = I2S_DATA_BIT_WIDTH_8BIT,
                    .slot_bit_width = I2S_SLOT_BIT_WIDTH_8BIT,
                    .slot_mode      = I2S_SLOT_MODE_MONO,
                    .slot_mask      = I2S_STD_SLOT_LEFT,
                    .ws_width       = 8,
                    .ws_pol         = false,
                    .bit_shift      = false,
                    .msb_right      = false },
      .gpio_cfg = { .mclk = I2S_GPIO_UNUSED,
                    .bclk = I2S_GPIO_UNUSED,
                    .ws   = I2S_GPIO_UNUSED,
                    .dout = ℭ->p,
                    .din  = I2S_GPIO_UNUSED,
                    .invert_flags = { .mclk_inv = false,
                                      .bclk_inv = false,
                                      .ws_inv   = false } } };
  ESP_CHK(i2s_channel_init_std_mode, ws_i2s_chan, &std_cfg);
  ESP_CHK(i2s_channel_enable, ws_i2s_chan); }
static void driver_write(LedConf *ℭ) {
  size_t written;
  ESP_CHK(i2s_channel_write, ws_i2s_chan, ℭ->i ?ℭ->𝔅_β: ℭ->𝔅_α, 3*3*ℭ->n, &written, 1000); }