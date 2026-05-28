#define STATE_LOOP_NONE       0
#define STATE_LOOP            1
#define STATE_SET_DEV         2
#define STATE_SET_MODE        3
#define STATE_UPDATE_Δ        4
#define STATE_ARGS_SET        5
#define STATE_INIT            6
#define STATE_CLEAR           7
#define STATE_DEAD          254
#define STATE_SPIN          255

#define LOG_INTRV_μ (30*1000000)

#define READ(x)  BAR; x=𝔖->𝔪  ; BAR;
#define WRITE(x) BAR; 𝔖->𝔪=(x); BAR;
static void lightwave_led_loop(void* volatile arg) {
  volatile LW_Loop_Args* volatile 𝔄 = (LW_Loop_Args*)arg;
  globals_from_ptrs(𝔄->globals);
  
  volatile LW_State* 𝔖 = 𝔄->state;
  volatile u8 𝔪;
  LedConf   𝔏 = { .n=300, .p=17, .t=400LL<<48 | 850LL<<32 | 800LL<<16 | 450LL, .lch=50000 };
  LW_Device 𝼥;
  LW_Mode   𝔐;
  i32 prevΔ=0,Δ=0,targΔ=0,δ_Δ=0,ΔΔ=0;
  u32 fcount=0;
  u64 tsΔ=0;
  
  WRITE(STATE_INIT);
  loop {
    READ(𝔪);
    if(!𝔪) break;
    if(𝔪 == STATE_LOOP) goto LOOP;
    switch(𝔪) {
      base STATE_UPDATE_Δ:
        prevΔ = Δ;
        tsΔ = 𝝁/1000;
        BAR; targΔ = 𝔖->Δ; BAR;
        WRITE(STATE_ARGS_SET);
      base STATE_SET_DEV:
        𝼥 = *((LW_Device*)(𝔄->val));
        BAR;
        // 𝔏.t=𝼥.t; 𝔏.p=𝼥.p; 𝔏.𝔇=𝼥.𝔇; 𝔏.𝔅_α=𝼥.𝔅_α; 𝔏.𝔅_β=𝼥.𝔅_β;
        𝔏.t=𝼥.t; 𝔏.p=𝼥.p; 𝔏.𝔇_α=𝼥.𝔇_α; 𝔏.𝔇_β=𝼥.𝔇_β;
        BAR;
        led_init(&𝔏);
        WRITE(STATE_ARGS_SET)
      base STATE_SET_MODE:
        𝔐 = *((LW_Mode *)(𝔄->val));
        BAR;
        if(𝔐.h-𝔐.l > 𝼥.n) 𝔐.h = 𝔐.l+𝼥.n; // bound range to dev range
        𝔏.n = 𝔐.h-𝔐.l; // num leds we actually write
        prevΔ = Δ = targΔ = 𝔖->Δ;
        WRITE(STATE_ARGS_SET);
      base STATE_CLEAR:
        u32 restore = 𝔏.n;
        BAR; 𝔏.n = (u32)(𝔄->val); BAR;
        u8* 𝔇 = get_led_buf(&𝔏);
        for(u32 i=0; i<3*𝔏.n; i++) 𝔇[i] = 0;
        led_flow(&𝔏);
        𝔏.n = restore;
        WRITE(STATE_ARGS_SET);
      bade:
        sleep(1); }
    
    BAR; continue;
    
    LOOP:
      fcount = 0;
      u64 μ = 𝝁;
      u64 t_log = μ + LOG_INTRV_μ;
      loop {
        u64 ms = (μ=𝝁)/1000;
        if(ΔΔ = targΔ-Δ) { // experp Δ from prevΔ to targΔ over ms-tsΔ ms (assuming nondrastic change)
          if(-10000<=ΔΔ && ΔΔ<10000 && (δ_Δ=ms-tsΔ)<1000) { // https://www.desmos.com/calculator/hexqqffwi9?nobranding=&nokeypad=
            f32 l = δ_Δ<0 ?0: δ_Δ>1000 ?1: 0.001f*δ_Δ;
            const f32 div = expf(2.f)-1.f;
            Δ = prevΔ+ceilf((targΔ-prevΔ)*((expf(2.f*l)-1.)/div)); }
          el
            Δ = targΔ; }
        
        u32 t_ms = ms+Δ; // 󰤱􊽨 this wraps?
        f32 t = (t_ms/1000)+0.001f*(t_ms%1000);
        u8* 𝔇 = get_led_buf(&𝔏);
        lightwave_prerender(𝔐.atoms, 𝔐.atoms_len, 𝔐.fades, t);
        lightwave_render   (𝔐.S, 𝔐.S_len, 𝔐.atoms, 𝔐.atoms_len,
                            𝔐.fades, 𝔐.stk, 𝔇, 𝼥.rgb_offs,
                            𝼥.reverse, 𝔐.l, 𝔐.h, t);
        led_flow(&𝔏);
        fcount++;
        
        READ(𝔪);
        if(𝔪 != STATE_LOOP) break   ;
        if(μ <  t_log     ) continue;
        
        f32 fps     = (f32)fcount / (0.000001f*LOG_INTRV_μ);
        u32 dur_μ   = led_write_dur_μ(&𝔏);
        if(!dur_μ) continue;
        f32 max_fps = 1000000.f/dur_μ;
        f32 eff     = fps/max_fps*100;
        ƿs("[LW]")
        ƿs(" FPS: "  )ƿf(fps    )
        ƿs(" / "     )ƿf(max_fps)
        ƿs(" = "     )ƿf(eff    )ƿs("% efficiency")
        ƿs(" (frame=")ƿn(dur_μ)ƿs("μ)")
        ƿe ƿs("    ")
        ƿs(" ms="      )ƿn(ms)
        ƿs(" ms+Δ="    )ƿn(t_ms)
        ƿs(" Δ["       )ƿn(prevΔ)ƿs(" ")ƿn(Δ)ƿs(" ")ƿn(targΔ)ƿs("]")
        ƿe ƿs("    ")
        ƿs(" rgb_offs=")ƿn(𝼥.rgb_offs)
        ƿs(" pin="     )ƿn(𝔏.p)
        ƿs(" timing="  )ƿn(𝔏.t)
        ƿs(" reverse=" )ƿs(𝼥.reverse?"Y":"N")
        ƿe ƿs("    ")
        ƿs(" ledc["    )ƿn(𝔏.n)
        ƿs(" / "       )ƿn(𝼥.n)ƿs("]")
        ƿs(" <")ƿn(𝔐.l)ƿs(" ")ƿn(𝔐.h)ƿs(">")
        ƿe
        fcount = 0;
        t_log += LOG_INTRV_μ; } }
  WRITE(STATE_DEAD); }
#undef READ
#undef WRITE