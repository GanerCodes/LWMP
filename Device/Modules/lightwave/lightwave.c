#include "py/obj.h"
#include "py/runtime.h"
#include "py/builtin.h"
#include "py/objarray.h"
#include <math.h>
#include <stdint.h>

#define f32    float
#define u32 uint32_t
#define u16 uint16_t
#define i32  int32_t
#define i16  int16_t
#define u8   uint8_t
#define i8    int8_t

#pragma push_macro("ret")
#define el else
#define ef el if
#define ret return

#define OFFSET_R ((RGB_OFFS >>  0) & 0xFF)
#define OFFSET_G ((RGB_OFFS >>  8) & 0xFF)
#define OFFSET_B ((RGB_OFFS >> 16) & 0xFF)
typedef struct { u8 r,g,b; } RGB;
typedef struct { i32 σ,Σ,d,m; f32 r0,rΔ; } Seg;
  // r0: rotation start offset
  // rΔ: rotation speed
  // σ : 
  // Σ : length in LED count
  // d : 
  // m : mode; 0 ⇒ has subchildren
typedef struct { f32 r; i32 σ,Σ; } StackEntry;
typedef struct { u8 r,g,b;                              } Static;
typedef struct { f32 segs; u8 s,v;                      } Rainbow;
typedef struct { u8 clrN; RGB *colors; f32 speed,sharp; } Fade;
typedef struct { u8 brightness;
                 u8 mode; // RxxxxMMM  R is for reversed, M determines which of the following union
                 union { Static; Rainbow; Fade; } data; } Atom;

/*

// https://www.desmos.com/calculator/yli6q8tc25?nobranding=&nokeypad=
compute_fades(t)

Atom *atoms = (StackEntry *)mp_obj_get_uint(args[…]);
for(let i = 0; i<atoms_len; i++) {
  Atom atom = atoms[i];
  if(atom.mode & 0b111 == 2) {
    float p = atom.speed*t;
    RGB clr = RGBlerp(
      atom.colors[((u32)(p   )) % atom.clrN)],
      atom.colors[((u32)(p+1f)) % atom.clrN)],
      (u8)(255*powf(mod(p,1.0),1+255f*powf(sharp,5))));
    atoms[i] = Static(clr.r,clr.g,clr.b);
  }
  
}


*/

static inline f32 mod(f32 a, f32 b) { a = fmodf(a,b);
                                      ret a<0 ?a+b: a; }

// static inline f32    lerp(f32 a, f32 b, f32 x) { ret (1.0-x)*a + x*b; }
static inline f32    lerp(f32 a, f32 b, f32 x) { ret a + x*(b-a); }
static inline u8    ulerp( u8 a,  u8 b,  u8 x) { ret a+(x*(b-a+1)+1 >> 8); }
static inline RGB RGBlerp(RGB a, RGB b,  u8 x) { ret (RGB) { ulerp(a.r,b.r,x),
                                                             ulerp(a.g,b.g,x),
                                                             ulerp(a.b,b.b,x) }; }
static inline RGB lightwave_hsv_to_rgb(u8 h, u8 s, u8 v) {
    if(!s) ret (RGB){v,v,v};
    u8 reg = h/43;
    u8 r = (h - reg*43) * 6;
    u8 p = ((u16)v * (255 - s)) >> 8;
    u8 q = ((u16)v * (255 - (((u16)s*r) >> 8))) >> 8;
    u8 t = ((u16)v * (255 - (((u16)s*(255-r)) >> 8))) >> 8;
    switch(reg) { case  0: ret (RGB){v,t,p}; break;
                  case  1: ret (RGB){q,v,p}; break;
                  case  2: ret (RGB){p,v,t}; break;
                  case  3: ret (RGB){p,q,v}; break;
                  case  4: ret (RGB){t,p,v}; break;
                  default: ret (RGB){v,p,q}; break; } }

static inline RGB lightwave_atom_rainbow(f32 i, f32 n, f32 segN, u8 s, u8 v) {
    ret lightwave_hsv_to_rgb((u8)(i*segN/n*0xFF), s, v); }

static mp_obj_t lightwave_assign_leds(size_t n_args, const mp_obj_t *args) {
    Seg        *S        = (Seg        *)mp_obj_get_uint (args[0]);
    u32         S_len    =               mp_obj_get_int  (args[1]);
    StackEntry *stk      = (StackEntry *)mp_obj_get_uint (args[2]);
    u8         *leds     = (u8         *)mp_obj_get_uint (args[3]);
    f32         t        =               mp_obj_get_float(args[4]);
    u32         RGB_OFFS =               mp_obj_get_int  (args[5]);
    u8 OFF_R = OFFSET_R;
    u8 OFF_G = OFFSET_G;
    u8 OFF_B = OFFSET_B;
    for(i32 i=0,p=0,d=0; i<S_len; i++) {
        Seg s = S[i];
        if(s.d<d) p += s.d - d;
        d = s.d;
        stk[p] = (StackEntry){s.r0 + s.rΔ*t,s.σ,s.Σ};

        if(!s.m) { p++;
                   continue; }
        i32 mode_id = s.m-1;
        for(i32 o=0; o<s.Σ; o++) {
            f32 n=o;
            for(i32 q=p; q>=0; q--) { // apply stack of transformation
                StackEntry e = stk[q];
                n = mod(n+e.r,e.Σ) + e.σ; }
            RGB c1;
            RGB c2;
            if(mode_id == 0) {
              c1 = lightwave_atom_rainbow(o             , s.Σ, 3.0, 0xFF, 0x15);
              c2 = lightwave_atom_rainbow(o==0?s.Σ-1:o-1, s.Σ, 3.0, 0xFF, 0x15); }
            ef(mode_id == 1) {
              c1 = (RGB){0x44,0x00,0x00}; // ...so whats the mode_id of the LED next to us lol
              c2 = (RGB){0x44,0x00,0x00}; }
            ef(mode_id == 2) {
              c1 = (RGB){0x00,0x44,0x00};
              c2 = (RGB){0x00,0x44,0x00}; }
            el{
              c1 = lightwave_atom_rainbow(o             , s.Σ, 3.0, 0xFF, 0x44);
              c2 = lightwave_atom_rainbow(o==0?s.Σ-1:o-1, s.Σ, 3.0, 0xFF, 0x44);
            }
            u8 prop = 0xFF*(n - (u32)n);
            leds[3*(u32)n+OFF_R] = ulerp(c1.r,c2.r,prop);
            leds[3*(u32)n+OFF_G] = ulerp(c1.g,c2.g,prop);
            leds[3*(u32)n+OFF_B] = ulerp(c1.b,c2.b,prop); } }
    
    ret mp_const_none; }
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(lightwave_assign_leds_obj,6,6,lightwave_assign_leds);

static const mp_rom_map_elem_t lightwave_module_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__   ), MP_ROM_QSTR(MP_QSTR_lightwave)         },
    { MP_ROM_QSTR(MP_QSTR_assign_leds), MP_ROM_PTR(&lightwave_assign_leds_obj) } };
static MP_DEFINE_CONST_DICT(lightwave_module_globals, lightwave_module_globals_table);

const mp_obj_module_t lightwave_user_cmodule = { .base    = { &mp_type_module },
                                                 .globals = (mp_obj_dict_t*)&lightwave_module_globals };

MP_REGISTER_MODULE(MP_QSTR_lightwave, lightwave_user_cmodule);

#pragma pop_macro("ret")