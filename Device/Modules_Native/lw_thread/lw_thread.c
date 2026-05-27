#include "EXPORT_GLOBALS.c"

// #include "driver/rmt_rx.h"
// #include "driver/i2s_std.h"
#include "driver/gpio.h"
#include "driver/rmt_tx.h"
#include "esp_heap_caps.h"
#include "esp_intr_alloc.h"
#include "esp_log.h"
#include "esp_rom_gpio.h"
#include "esp_system.h"
#include "esp_timer.h"
#include "esp_wifi.h"
#include "freertos/FreeRTOS.h"
#include "freertos/portmacro.h"
#include "freertos/task.h"
#include "py/runtime.h"
#include "py/objarray.h"
#include "py/mphal.h"
#include "rtc_wdt.h"
#include <stdlib.h>
#include <stdio.h>

extern BaseType_t xTaskCreatePinnedToCore(TaskFunction_t, const char * const,
                                          const uint32_t, void * const,
                                          UBaseType_t, TaskHandle_t * const,
                                          const BaseType_t); // why aren't we defined already
typedef struct { void (*f)(void *); void *arg; } lw_task_ctx_t;
static void lw_thread_task_entry(void *arg) { lw_task_ctx_t *ctx = (lw_task_ctx_t *)arg;
                                              ctx->f(ctx->arg);
                                              free(ctx);
                                              vTaskDelete(NULL); }
static mp_obj_t lw_thread_run_on_core(size_t n_args, const mp_obj_t *args) {
  lw_task_ctx_t *ctx = malloc(sizeof(lw_task_ctx_t));
  ctx->f   = (void (*)(void *))(uintptr_t)mp_obj_get_int(args[0]);
  ctx->arg =          (void *) (uintptr_t)mp_obj_get_int(args[1]);
  xTaskCreatePinnedToCore(lw_thread_task_entry,"lw_task",4096,ctx,
                          mp_obj_get_int(args[3]),NULL,mp_obj_get_int(args[2]));
  return mp_const_none; }
MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(lw_thread_run_on_core_obj,4,4,lw_thread_run_on_core);

static void     lw_thread_print    (const char *s ) { printf                ("%s",s); }
static void     lw_portInterrupts_Y(              ) { portENABLE_INTERRUPTS (      ); }
static void     lw_portInterrupts_N(              ) { portDISABLE_INTERRUPTS(      ); }
static void     lw_taskCritical_Y  (portMUX_TYPE m) { taskENTER_CRITICAL    (&m    ); }
static void     lw_taskCritical_N  (portMUX_TYPE m) { taskEXIT_CRITICAL     (&m    ); }
static void     lw_mp_GIL_Y        (              ) { MP_THREAD_GIL_ENTER   (      ); }
static void     lw_mp_GIL_N        (              ) { MP_THREAD_GIL_EXIT    (      ); }
static unsigned lw_hal_timing_Y    (              ) { return mp_hal_quiet_timing_enter( ); }
static void     lw_hal_timing_N    (unsigned r    ) {        mp_hal_quiet_timing_exit (r); }

static mp_obj_t lw_thread_get_ptrs(void) {
  static uintptr_t ptrs[] = EXPORT_GLOBALS;
  return mp_obj_new_bytearray_by_ref(sizeof(ptrs),ptrs); }
static MP_DEFINE_CONST_FUN_OBJ_0(lw_thread_get_ptrs_obj,lw_thread_get_ptrs);

static mp_obj_t lw_thread_xPortGetCoreID      () { return mp_obj_new_int(xPortGetCoreID()    ); } MP_DEFINE_CONST_FUN_OBJ_0(lw_thread_xPortGetCoreID_obj      , lw_thread_xPortGetCoreID      );
static mp_obj_t lw_thread_RMT_CLK_SRC_DEFAULT () { return mp_obj_new_int(RMT_CLK_SRC_DEFAULT ); } MP_DEFINE_CONST_FUN_OBJ_0(lw_thread_RMT_CLK_SRC_DEFAULT_obj , lw_thread_RMT_CLK_SRC_DEFAULT );
static mp_obj_t lw_thread_RMT_CLK_SRC_REF_TICK() { return mp_obj_new_int(RMT_CLK_SRC_REF_TICK); } MP_DEFINE_CONST_FUN_OBJ_0(lw_thread_RMT_CLK_SRC_REF_TICK_obj, lw_thread_RMT_CLK_SRC_REF_TICK);

static const mp_rom_map_elem_t lw_thread_module_globals_table[] = {
  { MP_ROM_QSTR(MP_QSTR___name__            ), MP_ROM_QSTR( MP_QSTR_lw_thread                 ) },
  { MP_ROM_QSTR(MP_QSTR_get_ptrs            ), MP_ROM_PTR (&lw_thread_get_ptrs_obj            ) },
  { MP_ROM_QSTR(MP_QSTR_run_on_core         ), MP_ROM_PTR (&lw_thread_run_on_core_obj         ) },
  { MP_ROM_QSTR(MP_QSTR_xPortGetCoreID      ), MP_ROM_PTR (&lw_thread_xPortGetCoreID_obj      ) },
  { MP_ROM_QSTR(MP_QSTR_RMT_CLK_SRC_DEFAULT ), MP_ROM_PTR (&lw_thread_RMT_CLK_SRC_DEFAULT_obj ) },
  { MP_ROM_QSTR(MP_QSTR_RMT_CLK_SRC_REF_TICK), MP_ROM_PTR (&lw_thread_RMT_CLK_SRC_REF_TICK_obj) } };
static MP_DEFINE_CONST_DICT(lw_thread_module_globals, lw_thread_module_globals_table);
const mp_obj_module_t lw_thread_user_c_module = {
    .base    = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&lw_thread_module_globals };
MP_REGISTER_MODULE(MP_QSTR_lw_thread, lw_thread_user_c_module);