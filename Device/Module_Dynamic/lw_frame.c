fast inline RGB compute_fade(Atom atom, u8* fades, f32 t) { // https://www.desmos.com/calculator/yli6q8tc25
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

fast void lightwave_prerender(Atom *atoms, u32 atoms_len, u8 *fades, f32 t) {
  precompute_fades(atoms,atoms_len,fades,t); }

fast void lightwave_render(Seg *S, u32 S_len, Atom *atoms, u32 atoms_len,
                           u8 *fades, StackEntry *stk, u8 *leds,
                           u8 RGB_OFFS, u8 REVERSE, u32 l, u32 h, f32 t) {
  // u8 OFF_R = ((RGB_OFFS >> 16) & 0xFF);
  // u8 OFF_G = ((RGB_OFFS >>  8) & 0xFF);
  // u8 OFF_B = ((RGB_OFFS >>  0) & 0xFF);
  u8 OFF_R = (RGB_OFFS >> 4) & 0b11;
  u8 OFF_G = (RGB_OFFS >> 2) & 0b11;
  u8 OFF_B = (RGB_OFFS >> 0) & 0b11;
  // precompute_fades(atoms,atoms_len,fades,t);
  
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
                      reverse ^= 1; } // 󰤱[optional?] optimize out reverse thing to only happen for o=0
          n += e.σ; }
      
      // u32 N = (u32)(reverse ?n+0.995: n);
      u32 N = (u32)(n) + (mod(n,1.0)>=0.995 ?1: 0);
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
          // c = lightwave_hsv_to_rgb(f*(o+(reverse ?n-N+1: N-n+1.0)), atom.R.s, atom.R.v);
          c = lightwave_hsv_to_rgb(f*(o+(REVERSE^reverse ?n-N+1.0: N-n+1.0)), atom.R.s, atom.R.v);
          // 󰤱          why does xor fix jitter ↑
        } break;
        case 2: {
          c = *(RGB*)(fades + atom.F.idx);
        } break;
        default: __builtin_unreachable(); }
      c = RGBscale(c,atom.brightness);
      
      N = 3*(REVERSE ?h-1-N: N-l);
      leds[N+OFF_R] = c.r;
      leds[N+OFF_G] = c.g;
      leds[N+OFF_B] = c.b; } } }