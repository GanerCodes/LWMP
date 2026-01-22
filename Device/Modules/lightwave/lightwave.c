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
#define fast static __attribute__((optimize("O3")))
#define el else
#define ef el if
#define ret return

#define OFFSET_R ((RGB_OFFS >>  0) & 0xFF)
#define OFFSET_G ((RGB_OFFS >>  8) & 0xFF)
#define OFFSET_B ((RGB_OFFS >> 16) & 0xFF)

typedef struct { u8 r,g,b; } RGB;
fast inline f32     mod(f32 a, f32 b       ) { a = fmodf(a,b);
                                               ret a<0 ?a+b: a; }
// fast inline f32     mod(f32 a, f32 b       ) { ret a-b*(u32)(a/b); }
fast inline f32    flerp(f32 a, f32 b, f32 x) { ret a+x*(b-a); }
fast inline u8     ulerp( u8 a,  u8 b,  u8 x) { ret a+(x*(b-a+1)+1 >> 8); }
fast inline u8    uscale( u8 a,         u8 x) { ret x*(a+1)+1 >> 8; }
fast inline RGB  RGBlerp(RGB a, RGB b,  u8 x) { ret (RGB) { ulerp(a.r,b.r,x),
                                                            ulerp(a.g,b.g,x),
                                                            ulerp(a.b,b.b,x) }; }
fast inline RGB RGBscale(RGB x,  u8 y       ) { u32 z = y+1;
                                                ret (RGB) { y*x.r+z >> 8,
                                                            y*x.g+z >> 8,
                                                            y*x.b+z >> 8 }; };

typedef struct { i32 σ,Σ,d,m; f32 r0,rΔ; } Seg;
  // r0: rotation start offset
  // rΔ: rotation speed
  // σ : LED offset
  // Σ : length in LED count
  // d : 
  // m : mode; 0 ⇒ has subchildren
typedef struct { f32 r; i32 σ,Σ; } StackEntry;
typedef struct { u8 r,g,b;                               } Static;
typedef struct { f32 segs; u8 s,v;                       } Rainbow;
typedef struct { u8 clrN; RGB *colors; f32 speed,sharp;  } Fade;
typedef struct { u8 brightness, mode;
                 union { Static S; Rainbow R; Fade F; }; } Atom;
// mode: RxxxxMMM  R is for reversed, M determines which of the following union

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

// https://www.desmos.com/calculator/yli6q8tc25?nobranding=&nokeypad=
static void compute_fades(Atom *atoms, u32 atoms_len, f32 t) {
  for(u32 i=0; i<atoms_len; i++) {
    Atom atom = atoms[i];
    if((atom.mode & 0b111) == 2) {
      float p = atom.F.speed*t;
      RGB clr = RGBlerp(atom.F.colors[((u32)(p   )) % atom.F.clrN],
                        atom.F.colors[((u32)(p+1.)) % atom.F.clrN],
                        (u8)(255*powf(mod(p,1.),1+255.*powf(atom.F.sharp,5))));
      atoms[i] = (Atom){ atom.mode & 0b1111000, atom.brightness,
                         .S = {clr.r,clr.g,clr.b} };
    }
  }
}

fast inline RGB lightwave_atom_rainbow(f32 i, f32 n, f32 segN, u8 s, u8 v) {
    ret lightwave_hsv_to_rgb((u8)(i*segN/n*0xFF), s, v); }

fast mp_obj_t lightwave_assign_leds(size_t n_args, const mp_obj_t *args) {
    Seg        *S        = (Seg        *)mp_obj_get_uint (args[0]);
    u32         S_len    =               mp_obj_get_int  (args[1]);
    Atom       *atoms    = (Atom       *)mp_obj_get_int  (args[2]);
    StackEntry *stk      = (StackEntry *)mp_obj_get_uint (args[3]);
    u8         *leds     = (u8         *)mp_obj_get_uint (args[4]);
    f32         t        =               mp_obj_get_float(args[5]);
    u32         RGB_OFFS =               mp_obj_get_int  (args[6]);
    u8 OFF_R = OFFSET_R;
    u8 OFF_G = OFFSET_G;
    u8 OFF_B = OFFSET_B;
    
    for(i32 i=0,p=0,d=0; i<S_len; i++) {
        Seg s = S[i];
        if(s.d<d) p += s.d - d;
        d = s.d;
        stk[p] = (StackEntry){s.r0 + s.rΔ*t,s.σ,s.Σ};
        if(!s.m) { p++; continue; }
        
        Atom atom = atoms[s.m-1>1 ?1: s.m-1]; // mode_id is s.m-1
        for(i32 o=0; o<s.Σ; o++) {
            f32 n=o;
            for(i32 q=p; q>=0; q--) { // apply stack of transformation
                StackEntry e = stk[q];
                n = mod(n+e.r,e.Σ) + e.σ; } // 󰤱 negative Σ
            
            RGB c;
            switch(atom.mode) {
              case 0: {
                // c = (RGB){atom.S.r, atom.S.g, atom.S.b};
                c = *(RGB*)&atom.S;
              } break;
              case 1: {
                RGB c1 = lightwave_atom_rainbow(o             , s.Σ, atom.R.segs, atom.R.s, atom.R.v);
                RGB c2 = lightwave_atom_rainbow(o==0?s.Σ-1:o-1, s.Σ, atom.R.segs, atom.R.s, atom.R.v);
                c = RGBlerp(c1,c2,0xFF*(n-(u32)n));
              } break;
              case 2: {
                // 󰤱
              } break;
              default: __builtin_unreachable(); }
            c = RGBscale(c,atom.brightness);
            u32 off = 3*(u32)n;
            leds[off+OFF_R] = c.r;
            leds[off+OFF_G] = c.g;
            leds[off+OFF_B] = c.b;
          } }
    
    ret mp_const_none; }
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(lightwave_assign_leds_obj,7,7,lightwave_assign_leds);

static const mp_rom_map_elem_t lightwave_module_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__   ), MP_ROM_QSTR(MP_QSTR_lightwave)         },
    { MP_ROM_QSTR(MP_QSTR_assign_leds), MP_ROM_PTR(&lightwave_assign_leds_obj) } };
static MP_DEFINE_CONST_DICT(lightwave_module_globals, lightwave_module_globals_table);

const mp_obj_module_t lightwave_user_cmodule = { .base    = { &mp_type_module },
                                                 .globals = (mp_obj_dict_t*)&lightwave_module_globals };

MP_REGISTER_MODULE(MP_QSTR_lightwave, lightwave_user_cmodule);

#pragma pop_macro("ret")