int *__errno(void) { static int e; return &e; } // LOL

#include "py/dynruntime.h"
#include "py/obj.h"
#include "py/runtime.h"
#include "py/builtin.h"
#include "py/objarray.h"
#include <stdlib.h>
#include <stdint.h>
#include <math.h>
#include "stubs.c"
#include "lw_types.c"
#include "led.c"
#include "lw_math.c"
#include "lw_frame.c"
#include "lw_animation.c"
#pragma pop_macro("base")
#pragma pop_macro("ret")

static mp_obj_t lightwave_get_loop_ptr(void) { return mp_obj_new_int((uintptr_t)&lightwave_led_loop); }
static MP_DEFINE_CONST_FUN_OBJ_0(lightwave_get_loop_ptr_obj, lightwave_get_loop_ptr);

mp_obj_t mpy_init(mp_obj_fun_bc_t *self, size_t n_args, size_t n_kw, mp_obj_t *args) {
  MP_DYNRUNTIME_INIT_ENTRY
  mp_store_global(MP_QSTR_get_loop_ptr, MP_OBJ_FROM_PTR(&lightwave_get_loop_ptr_obj));
  MP_DYNRUNTIME_INIT_EXIT }