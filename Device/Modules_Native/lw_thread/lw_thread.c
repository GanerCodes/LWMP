// bruh

#include "driver/gpio.h"
#include "driver/rmt_rx.h"
#include "driver/rmt_tx.h"
#include "esp_heap_caps.h"
#include "esp_intr_alloc.h"
#include "esp_rom_gpio.h"
#include "esp_log.h"
#include "esp_system.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/portmacro.h"
#include "freertos/task.h"
#include "py/runtime.h"
#include "rtc_wdt.h"
#include <stdlib.h>
#include <stdio.h>

extern BaseType_t xTaskCreatePinnedToCore(TaskFunction_t, const char * const,
                                          const uint32_t, void * const,
                                          UBaseType_t, TaskHandle_t * const,
                                          const BaseType_t); // why aren't we defined already

typedef struct { void (*f)(void *); void *arg; } lw_task_ctx_t;
static void lw_thread_task_entry(void *arg) {
  lw_task_ctx_t *ctx = (lw_task_ctx_t *)arg;
  ctx->f(ctx->arg);
  free(ctx);
  vTaskDelete(NULL); }

static mp_obj_t lw_thread_run_on_core(mp_obj_t f_obj, mp_obj_t arg_obj, mp_obj_t core_obj) {
  lw_task_ctx_t *ctx = malloc(sizeof(lw_task_ctx_t));
  ctx->f   = (void (*)(void *))(uintptr_t)mp_obj_get_int(f_obj);
  ctx->arg = (void *)(uintptr_t)mp_obj_get_int(arg_obj);
  // xTaskCreatePinnedToCore(lw_thread_task_entry,"lw_task",4096,ctx,10,NULL,mp_obj_get_int(core_obj));
  xTaskCreatePinnedToCore(lw_thread_task_entry,"lw_task",4096,ctx,25,NULL,mp_obj_get_int(core_obj));
  return mp_const_none; }
MP_DEFINE_CONST_FUN_OBJ_3(lw_thread_run_on_core_obj, lw_thread_run_on_core);

static void lw_thread_print    (const char *s ) { printf                ("%s",s); }
static void lw_portInterrupts_N(              ) { portDISABLE_INTERRUPTS(      ); }
static void lw_portInterrupts_Y(              ) { portENABLE_INTERRUPTS (      ); }
static void lw_taskCritical_Y  (portMUX_TYPE m) { taskENTER_CRITICAL    (&m    ); }
static void lw_taskCritical_N  (portMUX_TYPE m) { taskEXIT_CRITICAL     (&m    ); }

static mp_obj_t lw_thread_get_ptrs(void) { mp_obj_t D = mp_obj_new_dict(0); mp_obj_dict_store(D,mp_obj_new_str("P",1),mp_obj_new_int((uintptr_t)&lw_thread_print)); mp_obj_dict_store(D,mp_obj_new_str("sleep",5),mp_obj_new_int((uintptr_t)&vTaskDelay)); mp_obj_dict_store(D,mp_obj_new_str("portInterrupts_N",16),mp_obj_new_int((uintptr_t)&lw_portInterrupts_N)); mp_obj_dict_store(D,mp_obj_new_str("portInterrupts_Y",16),mp_obj_new_int((uintptr_t)&lw_portInterrupts_Y)); mp_obj_dict_store(D,mp_obj_new_str("taskCritical_Y",14),mp_obj_new_int((uintptr_t)&lw_taskCritical_Y)); mp_obj_dict_store(D,mp_obj_new_str("taskCritical_N",14),mp_obj_new_int((uintptr_t)&lw_taskCritical_N)); mp_obj_dict_store(D,mp_obj_new_str("f_malloc",8),mp_obj_new_int((uintptr_t)&malloc)); mp_obj_dict_store(D,mp_obj_new_str("f_free",6),mp_obj_new_int((uintptr_t)&free)); mp_obj_dict_store(D,mp_obj_new_str("micros",6),mp_obj_new_int((uintptr_t)&esp_timer_get_time)); mp_obj_dict_store(D,mp_obj_new_str("xPortGetCoreID",14),mp_obj_new_int((uintptr_t)&xPortGetCoreID)); mp_obj_dict_store(D,mp_obj_new_str("rmt_disable",11),mp_obj_new_int((uintptr_t)&rmt_disable)); mp_obj_dict_store(D,mp_obj_new_str("rmt_enable",10),mp_obj_new_int((uintptr_t)&rmt_enable)); mp_obj_dict_store(D,mp_obj_new_str("rmt_encoder_reset",17),mp_obj_new_int((uintptr_t)&rmt_encoder_reset)); mp_obj_dict_store(D,mp_obj_new_str("rmt_new_bytes_encoder",21),mp_obj_new_int((uintptr_t)&rmt_new_bytes_encoder)); mp_obj_dict_store(D,mp_obj_new_str("rmt_new_tx_channel",18),mp_obj_new_int((uintptr_t)&rmt_new_tx_channel)); mp_obj_dict_store(D,mp_obj_new_str("rmt_transmit",12),mp_obj_new_int((uintptr_t)&rmt_transmit)); mp_obj_dict_store(D,mp_obj_new_str("rmt_tx_wait_all_done",20),mp_obj_new_int((uintptr_t)&rmt_tx_wait_all_done)); mp_obj_dict_store(D,mp_obj_new_str("f_calloc",8),mp_obj_new_int((uintptr_t)&calloc)); mp_obj_dict_store(D,mp_obj_new_str("f_realloc",9),mp_obj_new_int((uintptr_t)&realloc)); mp_obj_dict_store(D,mp_obj_new_str("esp_random",10),mp_obj_new_int((uintptr_t)&esp_random)); mp_obj_dict_store(D,mp_obj_new_str("esp_log_write",13),mp_obj_new_int((uintptr_t)&esp_log_write)); mp_obj_dict_store(D,mp_obj_new_str("esp_system_abort",16),mp_obj_new_int((uintptr_t)&esp_system_abort)); mp_obj_dict_store(D,mp_obj_new_str("esp_restart",11),mp_obj_new_int((uintptr_t)&esp_restart)); mp_obj_dict_store(D,mp_obj_new_str("heap_caps_malloc",16),mp_obj_new_int((uintptr_t)&heap_caps_malloc)); mp_obj_dict_store(D,mp_obj_new_str("heap_caps_free",14),mp_obj_new_int((uintptr_t)&heap_caps_free)); mp_obj_dict_store(D,mp_obj_new_str("esp_get_free_heap_size",22),mp_obj_new_int((uintptr_t)&esp_get_free_heap_size)); mp_obj_dict_store(D,mp_obj_new_str("esp_get_minimum_free_heap_size",30),mp_obj_new_int((uintptr_t)&esp_get_minimum_free_heap_size)); mp_obj_dict_store(D,mp_obj_new_str("rmt_alloc_encoder_mem",21),mp_obj_new_int((uintptr_t)&rmt_alloc_encoder_mem)); mp_obj_dict_store(D,mp_obj_new_str("rmt_apply_carrier",17),mp_obj_new_int((uintptr_t)&rmt_apply_carrier)); mp_obj_dict_store(D,mp_obj_new_str("rmt_bytes_encoder_update_config",31),mp_obj_new_int((uintptr_t)&rmt_bytes_encoder_update_config)); mp_obj_dict_store(D,mp_obj_new_str("rmt_del_channel",15),mp_obj_new_int((uintptr_t)&rmt_del_channel)); mp_obj_dict_store(D,mp_obj_new_str("rmt_del_encoder",15),mp_obj_new_int((uintptr_t)&rmt_del_encoder)); mp_obj_dict_store(D,mp_obj_new_str("rmt_del_sync_manager",20),mp_obj_new_int((uintptr_t)&rmt_del_sync_manager)); mp_obj_dict_store(D,mp_obj_new_str("rmt_new_copy_encoder",20),mp_obj_new_int((uintptr_t)&rmt_new_copy_encoder)); mp_obj_dict_store(D,mp_obj_new_str("rmt_new_rx_channel",18),mp_obj_new_int((uintptr_t)&rmt_new_rx_channel)); mp_obj_dict_store(D,mp_obj_new_str("rmt_new_simple_encoder",22),mp_obj_new_int((uintptr_t)&rmt_new_simple_encoder)); mp_obj_dict_store(D,mp_obj_new_str("rmt_new_sync_manager",20),mp_obj_new_int((uintptr_t)&rmt_new_sync_manager)); mp_obj_dict_store(D,mp_obj_new_str("rmt_receive",11),mp_obj_new_int((uintptr_t)&rmt_receive)); mp_obj_dict_store(D,mp_obj_new_str("rmt_rx_register_event_callbacks",31),mp_obj_new_int((uintptr_t)&rmt_rx_register_event_callbacks)); mp_obj_dict_store(D,mp_obj_new_str("rmt_sync_reset",14),mp_obj_new_int((uintptr_t)&rmt_sync_reset)); mp_obj_dict_store(D,mp_obj_new_str("rmt_tx_register_event_callbacks",31),mp_obj_new_int((uintptr_t)&rmt_tx_register_event_callbacks)); mp_obj_dict_store(D,mp_obj_new_str("rmt_tx_switch_gpio",18),mp_obj_new_int((uintptr_t)&rmt_tx_switch_gpio)); mp_obj_dict_store(D,mp_obj_new_str("gpio_set_level",14),mp_obj_new_int((uintptr_t)&gpio_set_level)); mp_obj_dict_store(D,mp_obj_new_str("gpio_get_level",14),mp_obj_new_int((uintptr_t)&gpio_get_level)); mp_obj_dict_store(D,mp_obj_new_str("gpio_set_direction",18),mp_obj_new_int((uintptr_t)&gpio_set_direction)); mp_obj_dict_store(D,mp_obj_new_str("esp_rom_gpio_connect_out_signal",31),mp_obj_new_int((uintptr_t)&esp_rom_gpio_connect_out_signal)); mp_obj_dict_store(D,mp_obj_new_str("esp_intr_alloc",14),mp_obj_new_int((uintptr_t)&esp_intr_alloc)); mp_obj_dict_store(D,mp_obj_new_str("esp_intr_disable",16),mp_obj_new_int((uintptr_t)&esp_intr_disable)); mp_obj_dict_store(D,mp_obj_new_str("esp_intr_enable",15),mp_obj_new_int((uintptr_t)&esp_intr_enable)); mp_obj_dict_store(D,mp_obj_new_str("rtc_wdt_set_time",16),mp_obj_new_int((uintptr_t)&rtc_wdt_set_time)); mp_obj_dict_store(D,mp_obj_new_str("rtc_wdt_set_stage",17),mp_obj_new_int((uintptr_t)&rtc_wdt_set_stage)); mp_obj_dict_store(D,mp_obj_new_str("rtc_wdt_set_length_of_reset_signal",34),mp_obj_new_int((uintptr_t)&rtc_wdt_set_length_of_reset_signal)); mp_obj_dict_store(D,mp_obj_new_str("rtc_wdt_feed",12),mp_obj_new_int((uintptr_t)&rtc_wdt_feed)); mp_obj_dict_store(D,mp_obj_new_str("rtc_wdt_protect_off",19),mp_obj_new_int((uintptr_t)&rtc_wdt_protect_off)); mp_obj_dict_store(D,mp_obj_new_str("rtc_wdt_disable",15),mp_obj_new_int((uintptr_t)&rtc_wdt_disable)); mp_obj_dict_store(D,mp_obj_new_str("xTaskGetTickCount",17),mp_obj_new_int((uintptr_t)&xTaskGetTickCount)); mp_obj_dict_store(D,mp_obj_new_str("xTaskGetTickCountFromISR",24),mp_obj_new_int((uintptr_t)&xTaskGetTickCountFromISR)); mp_obj_dict_store(D,mp_obj_new_str("xTaskDelayUntil",15),mp_obj_new_int((uintptr_t)&xTaskDelayUntil)); mp_obj_dict_store(D,mp_obj_new_str("xTaskGetCurrentTaskHandle",25),mp_obj_new_int((uintptr_t)&xTaskGetCurrentTaskHandle)); mp_obj_dict_store(D,mp_obj_new_str("vTaskSuspend",12),mp_obj_new_int((uintptr_t)&vTaskSuspend)); mp_obj_dict_store(D,mp_obj_new_str("vTaskResume",11),mp_obj_new_int((uintptr_t)&vTaskResume)); return D; }
static MP_DEFINE_CONST_FUN_OBJ_0(lw_thread_get_ptrs_obj,lw_thread_get_ptrs);

static mp_obj_t lw_thread_xPortGetCoreID() { return mp_obj_new_int(xPortGetCoreID()); }
MP_DEFINE_CONST_FUN_OBJ_0(lw_thread_xPortGetCoreID_obj, lw_thread_xPortGetCoreID);

static mp_obj_t lw_thread_RMT_CLK_SRC_DEFAULT() { return mp_obj_new_int(RMT_CLK_SRC_DEFAULT); }
MP_DEFINE_CONST_FUN_OBJ_0(lw_thread_RMT_CLK_SRC_DEFAULT_obj, lw_thread_RMT_CLK_SRC_DEFAULT);

static const mp_rom_map_elem_t lw_thread_module_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__           ), MP_ROM_QSTR( MP_QSTR_lw_thread                ) },
    { MP_ROM_QSTR(MP_QSTR_get_ptrs           ), MP_ROM_PTR (&lw_thread_get_ptrs_obj           ) },
    { MP_ROM_QSTR(MP_QSTR_run_on_core        ), MP_ROM_PTR (&lw_thread_run_on_core_obj        ) },
    { MP_ROM_QSTR(MP_QSTR_xPortGetCoreID     ), MP_ROM_PTR (&lw_thread_xPortGetCoreID_obj     ) },
    { MP_ROM_QSTR(MP_QSTR_RMT_CLK_SRC_DEFAULT), MP_ROM_PTR (&lw_thread_RMT_CLK_SRC_DEFAULT_obj) } };
static MP_DEFINE_CONST_DICT(lw_thread_module_globals, lw_thread_module_globals_table);
const mp_obj_module_t lw_thread_user_c_module = {
    .base    = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&lw_thread_module_globals };
MP_REGISTER_MODULE(MP_QSTR_lw_thread, lw_thread_user_c_module);