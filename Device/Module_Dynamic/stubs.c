#include "IMPORT_GLOBALS.c"

#pragma push_macro("ret")
#pragma push_macro("base")
#define ret return
#define base break;case
#define bade break;default
#define loop while(1)
#define el else
#define ef el if
#define 𝝁 micros()

#define BAR __asm__ __volatile__ ("");
#define fast static __attribute__((optimize("O3")))
#define f_ASM(NAME,INSTRS) __attribute__((always_inline)) static inline void NAME() {__asm__ __volatile__(INSTRS);}

typedef   int8_t i8 ;
typedef  int16_t i16;
typedef  int32_t i32;
typedef  int64_t i64;
typedef  uint8_t u8 ;
typedef uint16_t u16;
typedef uint32_t u32;
typedef uint64_t u64;
typedef    float f32;
typedef   double f64;
typedef u64 u64a4 __attribute__((aligned(4)));

/********************** ESP lib **********************/
// general
#define BIT(n) (1UL<<(n))
typedef i32 esp_err_t;
typedef i32 gpio_num_t;

/* idk if the following even work in a dynamic module */
#define SECTION(name, description)
#define _SECTION_ATTR_IMPL(SECTION, COUNTER) __attribute__((section(SECTION "." _COUNTER_STRINGIFY(COUNTER))))
#define _SECTION_FORCE_ATTR_IMPL(SECTION, COUNTER) __attribute__((noinline, section(SECTION "." _COUNTER_STRINGIFY(COUNTER))))
#define _COUNTER_STRINGIFY(COUNTER) #COUNTER
#define IRAM_ATTR _SECTION_ATTR_IMPL(".iram1", __COUNTER__)

// clocks
#define APB_CLK_FREQ (80*1000000)
typedef enum { SOC_MOD_CLK_CPU          = 1,
               SOC_MOD_CLK_RTC_FAST        ,
               SOC_MOD_CLK_RTC_SLOW        ,
               SOC_MOD_CLK_APB             ,
               SOC_MOD_CLK_PLL_D2          ,
               SOC_MOD_CLK_PLL_F160M       ,
               SOC_MOD_CLK_XTAL32K         ,
               SOC_MOD_CLK_RC_FAST         ,
               SOC_MOD_CLK_RC_FAST_D256    ,
               SOC_MOD_CLK_XTAL            ,
               SOC_MOD_CLK_REF_TICK        ,
               SOC_MOD_CLK_APLL            ,
               SOC_MOD_CLK_INVALID } soc_module_clk_t;
typedef enum { RMT_CLK_SRC_APB      = SOC_MOD_CLK_APB,
               RMT_CLK_SRC_REF_TICK = SOC_MOD_CLK_REF_TICK,
               RMT_CLK_SRC_DEFAULT  = SOC_MOD_CLK_APB } soc_periph_rmt_clk_src_t;

// GPIO
#define DR_REG_GPIO_BASE     0x3ff44000
#define GPIO_OUT_W1TS_REG    (DR_REG_GPIO_BASE + 0x8 )
#define GPIO_OUT_W1TC_REG    (DR_REG_GPIO_BASE + 0xc )
#define GPIO_ENABLE_W1TS_REG (DR_REG_GPIO_BASE + 0x24)
#define GPIO_MODE_DEF_DISABLE         0x0
#define GPIO_MODE_DEF_INPUT           0x1
#define GPIO_MODE_DEF_OUTPUT          0x2
#define GPIO_MODE_DEF_OD              0x4
#define GPIO_NUM_NC -1
#define GPIO (*(volatile gpio_dev_t *)DR_REG_GPIO_BASE)
typedef enum { GPIO_MODE_DISABLE         = GPIO_MODE_DEF_DISABLE,
               GPIO_MODE_INPUT           = GPIO_MODE_DEF_INPUT,
               GPIO_MODE_OUTPUT          = GPIO_MODE_DEF_OUTPUT,
               GPIO_MODE_OUTPUT_OD       = GPIO_MODE_DEF_OUTPUT|GPIO_MODE_DEF_OD,
               GPIO_MODE_INPUT_OUTPUT_OD = GPIO_MODE_DEF_INPUT|GPIO_MODE_DEF_OUTPUT|GPIO_MODE_DEF_OD,
               GPIO_MODE_INPUT_OUTPUT    = GPIO_MODE_DEF_INPUT|GPIO_MODE_DEF_OUTPUT } gpio_mode_t;
typedef enum { GPIO_PULLUP_DISABLE   = 0,
               GPIO_PULLUP_ENABLE    = 1 } gpio_pullup_t;
typedef enum { GPIO_PULLDOWN_DISABLE = 0,
               GPIO_PULLDOWN_ENABLE  = 1 } gpio_pulldown_t;
typedef enum { GPIO_INTR_DISABLE    = 0,
               GPIO_INTR_POSEDGE    = 1,
               GPIO_INTR_NEGEDGE    = 2,
               GPIO_INTR_ANYEDGE    = 3,
               GPIO_INTR_LOW_LEVEL  = 4,
               GPIO_INTR_HIGH_LEVEL = 5,
               GPIO_INTR_MAX        = 6 } gpio_int_type_t;
typedef struct { u64 pin_bit_mask;
                 gpio_mode_t mode;
                 gpio_pullup_t pull_up_en;
                 gpio_pulldown_t pull_down_en;
                 gpio_int_type_t intr_type; } gpio_config_t;
typedef volatile struct gpio_dev_s {
 u32 bt_select,out,out_w1ts,out_w1tc;
 union { struct { u32 data     :  8;
                  u32 reserved8: 24; };
         u32 val; } out1;
 union { struct { u32 data     :  8;
                  u32 reserved8: 24; };
         u32 val; } out1_w1ts;
 union { struct { u32 data     :  8;
                  u32 reserved8: 24; };
         u32 val; } out1_w1tc;
 union { struct { u32 sel      :  8;
                  u32 reserved8: 24; };
         u32 val; } sdio_select;
 u32 enable,enable_w1ts,enable_w1tc;
 union { struct { u32 data     :  8;
                  u32 reserved8: 24; };
         u32 val; } enable1;
 union { struct { u32 data     :  8;
                  u32 reserved8: 24; };
         u32 val; } enable1_w1ts;
 union { struct { u32 data     :  8;
                  u32 reserved8: 24; };
         u32 val; } enable1_w1tc;
 union { struct { u32 strapping : 16;
                  u32 reserved16: 16; };
         u32 val; } strap;
 u32 in;
 union { struct { u32 data     :  8;
                  u32 reserved8: 24; };
         u32 val; } in1;
 u32 status,status_w1ts,status_w1tc;
 union { struct { u32 intr_st  :  8;
                  u32 reserved8: 24; };
         u32 val; } status1;
 union { struct { u32 intr_st  :  8;
                  u32 reserved8: 24; };
         u32 val; } status1_w1ts;
 union { struct { u32 intr_st  :  8;
                  u32 reserved8: 24; };
         u32 val; } status1_w1tc;
 u32 reserved_5c,acpu_int,acpu_nmi_int,pcpu_int,pcpu_nmi_int,cpusdio_int;
 union { struct { u32 intr     :  8;
                  u32 reserved8: 24; };
         u32 val; } acpu_int1;
 union { struct { u32 intr     :  8;
                  u32 reserved8: 24; };
         u32 val; } acpu_nmi_int1;
 union { struct { u32 intr     :  8;
                  u32 reserved8: 24; };
         u32 val; } pcpu_int1;
 union { struct { u32 intr     :  8;
                  u32 reserved8: 24; };
         u32 val; } pcpu_nmi_int1;
 union { struct { u32 intr     :  8;
                  u32 reserved8: 24; };
         u32 val; } cpusdio_int1;
 union { struct { u32 reserved0    :  2;
                  u32 pad_driver   :  1;
                  u32 reserved3    :  4;
                  u32 int_type     :  3;
                  u32 wakeup_enable:  1;
                  u32 config       :  2;
                  u32 int_ena      :  5;
                  u32 reserved18   : 14; };
         u32 val; } pin[40];
 union { struct { u32 rtc_max   : 10;
                  u32 reserved10: 21;
                  u32 start     :  1; };
         u32 val; } cali_conf;
 union { struct { u32 value_sync2: 20;
                  u32 reserved20 : 10;
                  u32 rdy_real   :  1;
                  u32 rdy_sync2  :  1; };
         u32 val; } cali_data;
 union { struct { u32 func_sel  :  6;
                  u32 sig_in_inv:  1;
                  u32 sig_in_sel:  1;
                  u32 reserved8 : 24; };
         u32 val; } func_in_sel_cfg[256];
 union { struct { u32 func_sel   :  9;
                  u32 inv_sel    :  1;
                  u32 oen_sel    :  1;
                  u32 oen_inv_sel:  1;
                  u32 reserved12 : 20; };
         u32 val; } func_out_sel_cfg[40]; } gpio_dev_t;

// I2S
#define I2S_GPIO_UNUSED GPIO_NUM_NC
#define I2S_CHANNEL_DEFAULT_CONFIG(i2s_num, i2s_role) { \
    .id                   = i2s_num , \
    .role                 = i2s_role, \
    .dma_desc_num         = 6       , \
    .dma_frame_num        = 240     , \
    .auto_clear_after_cb  = false   , \
    .auto_clear_before_cb = false   , \
    .allow_pd             = false   , \
    .intr_priority        = 0 }
#define I2S_STD_CLK_DEFAULT_CONFIG(rate) { \
    .sample_rate_hz = rate                 , \
    .clk_src        = I2S_CLK_SRC_DEFAULT  , \
    .mclk_multiple  = I2S_MCLK_MULTIPLE_256, \
    .bclk_div       = 8 }
#define I2S_STD_MSB_SLOT_DEFAULT_CONFIG(bits_per_sample, mono_or_stereo) { \
    .data_bit_width = bits_per_sample        , \
    .slot_bit_width = I2S_SLOT_BIT_WIDTH_AUTO, \
    .slot_mode      = mono_or_stereo                                                            , \
    .slot_mask      = mono_or_stereo == I2S_SLOT_MODE_MONO ?I2S_STD_SLOT_LEFT: I2S_STD_SLOT_BOTH, \
    .ws_width       = bits_per_sample                                                           , \
    .ws_pol         = false                                                                     , \
    .bit_shift      = false                                                                     , \
    .msb_right      = (bits_per_sample <= I2S_DATA_BIT_WIDTH_16BIT) ?true: false }
typedef struct i2s_channel_obj_t *i2s_chan_handle_t;
typedef enum { I2S_NUM_0 = 0 } i2s_port_t;
typedef enum { I2S_CLK_SRC_DEFAULT  = SOC_MOD_CLK_PLL_F160M,
               I2S_CLK_SRC_PLL_160M = SOC_MOD_CLK_PLL_F160M,
               I2S_CLK_SRC_APLL     = SOC_MOD_CLK_APLL } soc_periph_i2s_clk_src_t;
typedef soc_periph_i2s_clk_src_t i2s_clock_src_t;
typedef enum { I2S_SLOT_MODE_MONO   = 1,
               I2S_SLOT_MODE_STEREO = 2 } i2s_slot_mode_t;
typedef enum { I2S_STD_SLOT_LEFT  = BIT(0),
               I2S_STD_SLOT_RIGHT = BIT(1),
               I2S_STD_SLOT_BOTH  = BIT(0) | BIT(1) } i2s_std_slot_mask_t;
typedef enum { I2S_MCLK_MULTIPLE_128  =  128,
               I2S_MCLK_MULTIPLE_192  =  192,
               I2S_MCLK_MULTIPLE_256  =  256,
               I2S_MCLK_MULTIPLE_384  =  384,
               I2S_MCLK_MULTIPLE_512  =  512,
               I2S_MCLK_MULTIPLE_576  =  576,
               I2S_MCLK_MULTIPLE_768  =  768,
               I2S_MCLK_MULTIPLE_1024 = 1024,
               I2S_MCLK_MULTIPLE_1152 = 1152 } i2s_mclk_multiple_t;
typedef enum { I2S_ROLE_MASTER,
               I2S_ROLE_SLAVE } i2s_role_t;
typedef enum { I2S_DATA_BIT_WIDTH_8BIT  =  8,
               I2S_DATA_BIT_WIDTH_16BIT = 16,
               I2S_DATA_BIT_WIDTH_24BIT = 24,
               I2S_DATA_BIT_WIDTH_32BIT = 32, } i2s_data_bit_width_t;
typedef enum { I2S_SLOT_BIT_WIDTH_AUTO  =  0,
               I2S_SLOT_BIT_WIDTH_8BIT  =  8,
               I2S_SLOT_BIT_WIDTH_16BIT = 16,
               I2S_SLOT_BIT_WIDTH_24BIT = 24,
               I2S_SLOT_BIT_WIDTH_32BIT = 32, } i2s_slot_bit_width_t;
typedef struct { i2s_port_t id;
                 i2s_role_t role;
                 u32        dma_desc_num,dma_frame_num;
                 union { bool auto_clear, auto_clear_after_cb; };
                 bool       auto_clear_before_cb, allow_pd;
                 i32        intr_priority; } i2s_chan_config_t;
typedef struct { u32                 sample_rate_hz;
                 i2s_clock_src_t     clk_src;
                 i2s_mclk_multiple_t mclk_multiple;
                 u32                 bclk_div; } i2s_std_clk_config_t;
typedef struct { i2s_data_bit_width_t data_bit_width;
                 i2s_slot_bit_width_t slot_bit_width;
                 i2s_slot_mode_t      slot_mode;
                 i2s_std_slot_mask_t  slot_mask;
                 u32                  ws_width;
                 bool                 ws_pol,bit_shift,msb_right; } i2s_std_slot_config_t;
typedef struct { gpio_num_t mclk,bclk,ws,dout,din;
                 struct { u32   mclk_inv: 1;
                          u32   bclk_inv: 1;
                          u32     ws_inv: 1; } invert_flags; } i2s_std_gpio_config_t;
typedef struct { i2s_std_clk_config_t   clk_cfg;
                 i2s_std_slot_config_t slot_cfg;
                 i2s_std_gpio_config_t gpio_cfg; } i2s_std_config_t;

// RMT
#define SOC_RMT_MEM_WORDS_PER_CHANNEL 64
typedef soc_periph_rmt_clk_src_t rmt_clock_source_t;
typedef struct rmt_encoder_t rmt_encoder_t;
typedef struct rmt_encoder_t *rmt_encoder_handle_t;
typedef struct rmt_channel_t *rmt_channel_handle_t;
typedef enum { RMT_ENCODING_RESET    = 0   ,
               RMT_ENCODING_COMPLETE = 1<<0,
               RMT_ENCODING_MEM_FULL = 1<<1,
               RMT_ENCODING_WITH_EOF = 1<<2 } rmt_encode_state_t;
struct rmt_encoder_t { size_t    (*encode) (rmt_encoder_t *encoder, rmt_channel_handle_t tx_channel,
                                            const void *primary_data, size_t data_size,
                                            rmt_encode_state_t *ret_state);
                       esp_err_t (*reset ) (rmt_encoder_t *encoder);
                       esp_err_t (*del   ) (rmt_encoder_t *encoder); };
typedef struct {} rmt_copy_encoder_config_t;
typedef struct { gpio_num_t gpio_num;
                 rmt_clock_source_t clk_src;
                 u32 resolution_hz;
                 size_t mem_block_symbols,trans_queue_depth;
                 i32 intr_priority;
                 struct { u32 invert_out  : 1;
                          u32 with_dma    : 1;
                          u32 io_loop_back: 1;
                          u32 io_od_mode  : 1;
                          u32 allow_pd    : 1; } flags; } rmt_tx_channel_config_t;
typedef union { struct { u16 duration0: 15;
                         u16 level0   :  1;
                         u16 duration1: 15;
                         u16 level1   :  1; };
                u32 val; } rmt_symbol_word_t;
typedef struct { rmt_symbol_word_t bit0,bit1;
                 struct { u32 msb_first: 1; } flags; } rmt_bytes_encoder_config_t;
typedef struct { i32 loop_count;
                 struct { u32 eot_level        : 1;        
                          u32 queue_nonblocking: 1; } flags; } rmt_transmit_config_t;

typedef size_t (*rmt_encode_simple_cb_t)(const void *data, size_t data_size,
                                         size_t symbols_written, size_t symbols_free,
                                         rmt_symbol_word_t *symbols, bool *done, void *arg);
typedef struct {
    rmt_encode_simple_cb_t callback;  /*!< Callback to call for encoding data into RMT items */
    void *arg;                        /*!< Opaque user-supplied argument for callback */
    size_t min_chunk_size;            /*!< Minimum amount of free space, in RMT symbols, the
                                           encoder needs in order to guarantee it always
                                           returns non-zero. Defaults
                                           to 64 if zero / not given. */
} rmt_simple_encoder_config_t;

IMPORT_GLOBALS

/********************** Our stuff again **********************/

char* itoa(i64 v, char* out, i32 b) { // https://stackoverflow.com/a/23840699/14501641
  char *ptr=out, *ptr1=out;
  i64 prev;
  do { prev = v;
       v /= b;
       *ptr++ = "zyxwvutsrqponmlkjihgfedcba9876543210123456789abcdefghijklmnopqrstuvwxyz"[35 + (prev - v*b)];
  } while(v);
  if(prev<0) *ptr++ = '-';
  *ptr-- = '\0';
  while(ptr1 < ptr) { char t = *ptr;
                      *ptr--= *ptr1;
                      *ptr1++ = t; }
  ret out; }
char* ftoa(f32 v, char* out, i32 p) { // chatGPT
  char *ptr=out, *ptr1=out, *ptr2;
  i64 prev, ip;
  if(p<0) p = 6;
  if(v<0) { *ptr++ = '-';
            v = -v;
            ptr1++; }
  ip = (i64)v;
  do { prev = ip;
       ip /= 10;
       *ptr++ = "0123456789"[prev - 10*ip];
  } while(ip);
  ptr2 = ptr-1;
  while(ptr1<ptr2) { char t = *ptr2;
                     *ptr2-- = *ptr1;
                     *ptr1++ = t; }
  if(p) *ptr++ = '.';
  double frac = v - (i64)v;
  while(p--) { frac *= 10.0;
               i32 d = (i32)frac;
               *ptr++ = '0' + d;
               frac -= d; }
  *ptr = '\0';
  ret out; }

fast inline u64 millis() { ret micros()/1000; }

void P_i64(i64 v) { char buf[21]; itoa(v,buf,10); P(buf); }
void P_f64(f64 v) { char buf[32]; ftoa(v,buf,5 ); P(buf); }
void show_val(i64 v) { P_i64(v); P("\n"); }
#define ƿs(x) P((x));
#define ƿn(x) P_i64((x));
#define ƿf(x) P_f64((x));
#define ƿe P("\n");

#define ESP_CHK(f,...) do{ i32 e=f(__VA_ARGS__);\
                           if(!e) break;\
                           ƿs(#f " gave ")ƿs((void*)esp_err_to_name(e))ƿs(" (")ƿn(e)ƿs(")!")ƿe }while(0);

// 󰤱 prob just add this to the imported sigs block
void *memcpy(void *d, const void *s, unsigned n) { u8 *D = d;
                                                   const u8 *S = s;
                                                   while(n--) *D++ = *S++;
                                                   return d; }