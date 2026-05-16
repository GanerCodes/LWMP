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