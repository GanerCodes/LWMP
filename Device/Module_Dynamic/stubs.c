#pragma push_macro("ret")
#pragma push_macro("base")
#define ret return
#define base break;case
#define bade break;default
#define loop while(1)
#define el else
#define ef el if

#define fast static __attribute__((optimize("O3")))

typedef  uint8_t u8 ;
typedef uint16_t u16;
typedef uint32_t u32;
typedef uint64_t u64;
typedef   int8_t i8 ;
typedef  int16_t i16;
typedef  int32_t i32;
typedef  int64_t i64;
typedef    float f32;
typedef   double f64;

#define APB_CLK_FREQ (80*1000000)
#define SOC_RMT_MEM_WORDS_PER_CHANNEL 64

#define ESP_CHK(f,...) do{ i32 e=f(__VA_ARGS__);\
                           if(!e) break;\
                           P(#f " is not ESP_OK: ");P_i64(e);P("\n"); }while(0);

typedef i32 esp_err_t;
typedef i32 gpio_num_t;

// bro im getting trolled why is it 4
#define SOC_MOD_CLK_APB      4
#define SOC_MOD_CLK_REF_TICK 4

typedef enum { RMT_CLK_SRC_APB      = SOC_MOD_CLK_APB,
               RMT_CLK_SRC_REF_TICK = SOC_MOD_CLK_REF_TICK,
               RMT_CLK_SRC_DEFAULT  = SOC_MOD_CLK_APB } soc_periph_rmt_clk_src_t;
typedef soc_periph_rmt_clk_src_t rmt_clock_source_t;

typedef enum { RMT_ENCODING_RESET    = 0   ,
               RMT_ENCODING_COMPLETE = 1<<0,
               RMT_ENCODING_MEM_FULL = 1<<1,
               RMT_ENCODING_WITH_EOF = 1<<2 } rmt_encode_state_t;

typedef struct rmt_encoder_t *rmt_encoder_handle_t;
typedef struct rmt_channel_t *rmt_channel_handle_t;
typedef struct rmt_encoder_t rmt_encoder_t;
struct rmt_encoder_t { size_t    (*encode) (rmt_encoder_t *encoder, rmt_channel_handle_t tx_channel,
                                            const void *primary_data, size_t data_size,
                                            rmt_encode_state_t *ret_state);
                       esp_err_t (*reset ) (rmt_encoder_t *encoder);
                       esp_err_t (*del   ) (rmt_encoder_t *encoder); };

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

static void (*P)(const char *); static void (*sleep)(u32); static void (*portInterrupts_N)(void); static void (*portInterrupts_Y)(void); static void (*taskCritical_Y)(void); static void (*taskCritical_N)(void); static void* (*f_malloc)(size_t s); static void (*f_free)(void *p); static i64 (*micros)(void); static i32 (*xPortGetCoreID)(void); static esp_err_t (*rmt_disable)(rmt_channel_handle_t channel); static esp_err_t (*rmt_enable)(rmt_channel_handle_t channel); static esp_err_t (*rmt_encoder_reset)(rmt_encoder_handle_t encoder); static esp_err_t (*rmt_new_bytes_encoder)(const rmt_bytes_encoder_config_t *config, rmt_encoder_handle_t *ret_encoder); static esp_err_t (*rmt_new_tx_channel)(const rmt_tx_channel_config_t *config, rmt_channel_handle_t *ret_chan); static esp_err_t (*rmt_transmit)(rmt_channel_handle_t tx_channel, rmt_encoder_handle_t encoder, const void *payload, size_t payload_bytes, const rmt_transmit_config_t *config); static esp_err_t (*rmt_tx_wait_all_done)(rmt_channel_handle_t channel, i32 timeout_ms); static esp_err_t (*rmt_del_channel)(rmt_channel_handle_t channel); static esp_err_t (*rmt_del_encoder)(rmt_encoder_handle_t encoder);
typedef struct {void (*P)(const char *); void (*sleep)(u32); void (*portInterrupts_N)(void); void (*portInterrupts_Y)(void); void (*taskCritical_Y)(void); void (*taskCritical_N)(void); void* (*f_malloc)(size_t s); void (*f_free)(void *p); i64 (*micros)(void); i32 (*xPortGetCoreID)(void); esp_err_t (*rmt_disable)(rmt_channel_handle_t channel); esp_err_t (*rmt_enable)(rmt_channel_handle_t channel); esp_err_t (*rmt_encoder_reset)(rmt_encoder_handle_t encoder); esp_err_t (*rmt_new_bytes_encoder)(const rmt_bytes_encoder_config_t *config, rmt_encoder_handle_t *ret_encoder); esp_err_t (*rmt_new_tx_channel)(const rmt_tx_channel_config_t *config, rmt_channel_handle_t *ret_chan); esp_err_t (*rmt_transmit)(rmt_channel_handle_t tx_channel, rmt_encoder_handle_t encoder, const void *payload, size_t payload_bytes, const rmt_transmit_config_t *config); esp_err_t (*rmt_tx_wait_all_done)(rmt_channel_handle_t channel, i32 timeout_ms); esp_err_t (*rmt_del_channel)(rmt_channel_handle_t channel); esp_err_t (*rmt_del_encoder)(rmt_encoder_handle_t encoder);} passed_ptrs_t;
static void globals_from_ptrs(passed_ptrs_t* A) {P=A->P; sleep=A->sleep; portInterrupts_N=A->portInterrupts_N; portInterrupts_Y=A->portInterrupts_Y; taskCritical_Y=A->taskCritical_Y; taskCritical_N=A->taskCritical_N; f_malloc=A->f_malloc; f_free=A->f_free; micros=A->micros; xPortGetCoreID=A->xPortGetCoreID; rmt_disable=A->rmt_disable; rmt_enable=A->rmt_enable; rmt_encoder_reset=A->rmt_encoder_reset; rmt_new_bytes_encoder=A->rmt_new_bytes_encoder; rmt_new_tx_channel=A->rmt_new_tx_channel; rmt_transmit=A->rmt_transmit; rmt_tx_wait_all_done=A->rmt_tx_wait_all_done; rmt_del_channel=A->rmt_del_channel; rmt_del_encoder=A->rmt_del_encoder;}

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

#define BAR __asm__ __volatile__ ("");