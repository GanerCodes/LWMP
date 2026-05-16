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

// #define struct4 __attribute__((aligned (4))) struct
typedef uint64_t u64a4 __attribute__((aligned(4)));

typedef struct { u32 n; u64a4 t; u8 *𝔇α,*𝔇β; u8 p;
                 u8 *𝔇; u64a4 write_finish_μ; } LedConf;
typedef struct { u32 n; u64a4 t; u8 *𝔇α,*𝔇β; u8 p,rgb_offs,reverse; } LW_Device;
typedef struct { Seg        *S    ; u32     S_len;
                 Atom       *atoms; u32 atoms_len;
                 u8         *fades;
                 StackEntry *stk  ; u32 l,h; } LW_Mode;
typedef struct { volatile u8 𝔪; volatile u32 Δ; } LW_State;
typedef struct {          passed_ptrs_t* globals;
                 volatile      LW_State* state  ;
                                   void* val    ; } LW_Loop_Args;