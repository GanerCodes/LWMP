#include <math.h>
#include <stdint.h>
#include <stdio.h>

typedef struct { int σ,Σ,d,m;
                 float r0,rΔ; } Seg;
typedef struct { int r,σ,Σ; } StackEntry;

int mod(int a, int b) { int r = a%b;
                        return r<0 ?r+b: r; }

void assign_leds(Seg *S, int S_len, int t, StackEntry *stk, int *leds) {
    int p=0, d=0;
    for(int i=0; i<S_len; i++) {
        Seg s = S[i];
        if(s.d<d) p += s.d - d;

        stk[p] = (StackEntry){(int)(s.r0 + s.rΔ*t),s.σ,s.Σ};
        p++;

        if(s.m>0) { for(int o = 0; o<s.Σ; o++) {
                        int n = o;
                        for(int q=p-1; q>=0; q--) {
                            StackEntry e = stk[q];
                            n = mod(e.r+n, e.Σ) + e.σ; }
                        leds[n] = s.m-1; }
                    p--; }
        d = s.d; } }

int main() {
    Seg S[] = { {  0, 14, 0, 0, 0.0f,  1.0f },
                {  0,  7, 1, 0, 0.0f, -1.0f },
                {  0,  3, 2, 1, 0.0f,  0.0f },
                {  3,  4, 2, 2, 0.0f,  0.0f },
                {  7,  5, 1, 3, 0.0f,  0.0f },
                { 12,  2, 1, 4, 0.0f,  0.0f } };
    int S_len = sizeof(S) / sizeof(S[0]);
    int leds_N = S[0].Σ;
    int leds[leds_N];

    int max_d = 0;
    for(int i=0; i<S_len; i++) if(S[i].d>max_d) max_d = S[i].d;
    StackEntry stk[max_d+1];
    for(int i=0; i<=max_d; i++) stk[i] = (StackEntry){0,0,0};
    
    for(int t=0; t<10; t++) {
        assign_leds(S,S_len,t,stk,leds);
        for(int i=0; i<leds_N; i++) printf("%d",leds[i]);
        printf("\n"); }

    return 0; }