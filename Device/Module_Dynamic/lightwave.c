int *__errno(void) { static int e; return &e; } // LOL

#include "py/dynruntime.h"
#include "py/obj.h"
#include "py/runtime.h"
#include "py/builtin.h"
#include "py/objarray.h"
#include <stdlib.h>
#include <stdint.h>
#include <math.h>

#define f32    float
#define u32 uint32_t
#define u16 uint16_t
#define i32  int32_t
#define i16  int16_t
#define u8   uint8_t
#define i8    int8_t

#pragma push_macro("ret")
#define fast static __attribute__((optimize("O3")))
#define el else
#define ef el if
#define ret return

typedef struct { u8 r,g,b; } RGB;
typedef struct { i32 σ,Σ,d,m; f32 r0,rΔ; } Seg;
  /*
   * r0: rotation start offset
   * rΔ: rotation speed
   * σ : LED offset
   * Σ : length in LED count, negative for reversed
   * d : Move around the stack
   * m : mode; 0 ⇒ has subchildren, >0 atom
   */
typedef struct { f32 r; i32 σ,Σ; } StackEntry;
typedef struct { u8 r,g,b;                               } Static;
typedef struct { f32 segs; u8 s,v;                       } Rainbow;
typedef struct { u16 clrN; u16 idx; f32 speed,sharp;     } Fade;
typedef struct { u8 brightness, mode;
                 union { Static S; Rainbow R; Fade F; }; } Atom;

fast inline f32      mod(f32 a, f32 b       ) { a = a - (f32)((i32)(a/b))*b;
                                                ret a<0 ?a+b: a; }
fast inline f32    flerp(f32 a, f32 b, f32 x) { ret a+x*(b-a); }
fast inline u8     ulerp( u8 a,  u8 b,  u8 x) { ret a+(x*(b-a+1)+1 >> 8); }
fast inline u8    uscale( u8 a,         u8 x) { ret x*(a+1)+1 >> 8; }
fast inline RGB  RGBlerp(RGB a, RGB b,  u8 x) { ret (RGB) { ulerp(a.r,b.r,x),
                                                            ulerp(a.g,b.g,x),
                                                            ulerp(a.b,b.b,x) }; }
fast inline RGB RGBscale(RGB x,  u8 y       ) { u32 z = y+1;
                                                ret (RGB) { z*x.r >> 8,
                                                            z*x.g >> 8,
                                                            z*x.b >> 8 }; };
fast inline f32 fmulmodpartial(f32 x, f32 y, u32 m) {
  ret x*mod(y,1.) + truncf(y)*mod(x,1.) + ((u32)y)*((u32)x)%m; }

fast inline RGB lightwave_hsv_to_rgb(u8 h, u8 s, u8 v) {
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

fast inline RGB lightwave_atom_rainbow(f32 i, f32 n, f32 segN, u8 s, u8 v) {
    ret lightwave_hsv_to_rgb((u8)(i*segN/n*0xFF),s,v); }

// https://www.desmos.com/calculator/yli6q8tc25?nobranding=&nokeypad=
fast inline RGB compute_fade(Atom atom, u8* fades, f32 t) {
  f32 p = fmulmodpartial(atom.F.speed,t,1<<16);
  return RGBlerp(*(RGB*)(fades + atom.F.idx + 3 + 3*(((u16)(p    ))%atom.F.clrN)),
                 *(RGB*)(fades + atom.F.idx + 3 + 3*(((u16)(p+1.f))%atom.F.clrN)),
                 (u8)(255*powf(mod(p,1.),1+255.f*powf(atom.F.sharp,5.f)))); }

fast void precompute_fades(Atom *atoms, u32 atoms_len, u8 *fades, f32 t) {
  for(int i=0; i<atoms_len; i++) {
    Atom atom = atoms[i];
    if(atom.mode != 2) continue;
    RGB c = compute_fade(atom,fades,t);
    int j = atom.F.idx;
    fades[j  ] = c.r;
    fades[j+1] = c.g;
    fades[j+2] = c.b; } }

fast mp_obj_t lightwave_assign_leds(size_t n_args, const mp_obj_t *args) {
  u8 *𝔸 = (u8*)mp_obj_get_int(args[0]);
  Seg        *S           = *(Seg        **)(𝔸+ 0);
  u32         S_len       = *(u32         *)(𝔸+ 4);
  Atom       *atoms       = *(Atom       **)(𝔸+ 8);
  u32         atoms_len   = *(u32         *)(𝔸+12);
  u8         *fades       = *(u8         **)(𝔸+16);
  StackEntry *stk         = *(StackEntry **)(𝔸+20);
  u8         *leds        = *(u8         **)(𝔸+24);
  u32         RGB_OFFS    = *(u32         *)(𝔸+28);
  u32         REVERSE     = *(u32         *)(𝔸+32);
  u32         l           = *(u32         *)(𝔸+36);
  u32         h           = *(u32         *)(𝔸+40);
  f32         t           = mp_obj_get_float(args[1]);
  u8 OFF_R = ((RGB_OFFS >> 16) & 0xFF);
  u8 OFF_G = ((RGB_OFFS >>  8) & 0xFF);
  u8 OFF_B = ((RGB_OFFS >>  0) & 0xFF);
  
  precompute_fades(atoms,atoms_len,fades,t);
  
  // 500000
  for(i32 i=0,p=0,d=0; i<S_len; i++) {
    Seg s = S[i];
    if(s.d<d) p += s.d-d;
    d = s.d;
    i32 AΣS = abs(s.Σ);
    // stk[p] = (StackEntry){s.r0 + s.rΔ*t,s.σ,s.Σ};
    // stk[p] = (StackEntry){mod(s.r0 + s.rΔ*t, s.Σ),s.σ,s.Σ};
    stk[p] = (StackEntry){mod(s.r0 + fmulmodpartial(s.rΔ,t,AΣS), AΣS), s.σ, s.Σ};
    
    if(!s.m) { p++; continue; }
    
    Atom atom = atoms[s.m-1]; // mode_id is s.m-1
    for(i32 o=0; o<AΣS; o++) {
      f32 n=o;
      u8 reverse = (u8)REVERSE;
      for(i32 q=p; q>=0; q--) { // apply stack of transformation
          StackEntry e = stk[q];
          i32 AΣE = abs(e.Σ);
          n = mod(n+e.r,AΣE);
          if(e.Σ<0) { n = AΣE-1.0-n; // negative length ⇒ reversed
                      reverse = !reverse; } // 󰤱[optional?] optimize out reverse thing to only happen for o=0
          n += e.σ; }
      
      u32 N = (u32)(reverse ?n+0.995: n);
      if(N<l || N>=h) continue;
      
      RGB c;
      switch(atom.mode) {
        case 0: {
          c = *(RGB*)&atom.S;
        } break;
        case 1: {
          if(atom.R.segs == 0) { // 󰤱[optional?] optimize
            c = lightwave_hsv_to_rgb(mod(s.r0 + 5.0*fmulmodpartial(s.rΔ,t,0xFF), 0xFF), atom.R.s, atom.R.v);
            break; }
          f32 f = atom.R.segs*255.0/AΣS;
          c = lightwave_hsv_to_rgb(f*(o+(reverse ?n-N+1: N-n+1.0)), atom.R.s, atom.R.v);
        } break;
        case 2: {
          c = *(RGB*)(fades + atom.F.idx);
        } break;
        default: __builtin_unreachable(); }
      c = RGBscale(c,atom.brightness);
      
      N = 3*(REVERSE ?h-1-N: N-l);
      leds[N+OFF_R] = c.r;
      leds[N+OFF_G] = c.g;
      leds[N+OFF_B] = c.b; } }
  
  ret mp_const_none; }
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(lightwave_assign_leds_obj,2,2,lightwave_assign_leds);

mp_obj_t mpy_init(mp_obj_fun_bc_t *self, size_t n_args, size_t n_kw, mp_obj_t *args) {
    // This must be first, it sets up the globals dict and other things
    MP_DYNRUNTIME_INIT_ENTRY

    // Make the function available in the module's namespace
    mp_store_global(MP_QSTR_assign_leds, MP_OBJ_FROM_PTR(&lightwave_assign_leds_obj));

    // This must be last, it restores the globals dict
    MP_DYNRUNTIME_INIT_EXIT
}

// static const mp_rom_map_elem_t lightwave_module_globals_table[] = {
//     { MP_ROM_QSTR(MP_QSTR___name__   ), MP_ROM_QSTR(MP_QSTR_lightwave)         },
//     { MP_ROM_QSTR(MP_QSTR_assign_leds), MP_ROM_PTR(&lightwave_assign_leds_obj) } };
// static MP_DEFINE_CONST_DICT(lightwave_module_globals, lightwave_module_globals_table);

// const mp_obj_module_t lightwave_user_cmodule = { .base    = { &mp_type_module },
//                                                  .globals = (mp_obj_dict_t*)&lightwave_module_globals };

// MP_REGISTER_MODULE(MP_QSTR_lightwave, lightwave_user_cmodule);

#pragma pop_macro("ret")