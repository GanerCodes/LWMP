S_timetest = (D,s=10)=>({
  "mode": { "fx": [[1,s,0]],
            "*":[{ "fx":[], "1":[10,0,0x555555] },
                 { "fx":[], "1":[40,0,0x000000] }]},
  "offsets": { [D[0]]:0, [D[1]]:0, [D[2]]:0, [D[3]]:0 } });
/* S_snake = D=>({
  "mode": { "fx": [["Rotate",[1,0]]],
            "_":["modes",[{ "fx":[], "_": ["atom",[2 ,["Static",0x0000FF]]] },
                          { "fx":[], "_": ["atom",[13 ,["Static",0x000000]]] }]]},
  "offsets": { [D[0]]:0, [D[1]]:5, [D[2]]:10 } });
S_stress = D=>({
  "mode": { "fx": [
              ["Rotate",[20.34,0]]],
            "_":["modes",[
              { "fx":[
                  ["Brightness",0.5]],
                "_":["atom",
                  [250,["Static" ,0xFF00FF]]] },
              { "fx":[],
                "_": ["atom",
                  [250,["Rainbow",[5.25,0xE9,0xFF]]]] },
              { "fx":[
                  ["Reverse",true],
                  ["Brightness",0.5],
                  ["Rotate",[-20.34,23.2]]],
                "_":["modes",[
                  { "fx":[
                      ["Rotate",[ 20.34,23.2]]],
                    "_": ["atom",
                      [250,["Rainbow",[50.25,0xE9,0xFF]]]]},
                  { "fx":[
                      ["Rotate",[  0.00,23.2]]],
                    "_": ["atom",
                      [250,["Static",0x00FF00]]]}]] }]]},
  "offsets": { [D[0]]:0, [D[1]]:0, [D[2]]:0 } });
S_balance = D=>({
  "mode": { "fx":[
              ["Rotate",[500000.0,0]]],
            "_":["modes",[
              { "fx":[
                  ["Rotate",[-500000.0,0]]],
                "_":["atom",
                  [50,["Rainbow",[10.0,0xFF,0xFF]]]] }]]},
  "offsets": { [D[0]]:0, [D[1]]:0, [D[2]]:0 } });

S_rainbow_snake = D=>({
  "mode": { "fx": [["Rotate",[30,0]]],
            "_":["modes",[{ "fx":[], "_": ["atom",[25 ,["Rainbow",[2.  ,0xF5,0x55]]]] },
                          { "fx":[], "_": ["atom",[175,["Static" ,0x000000]]] }]]},
  "offsets": { [D[0]]:0, [D[1]]:-50, [D[2]]:100, [D[2]]:-150 } });

S_rainbow_snake_balance = D=>({
  "mode": { "fx":[
              ["Rotate",[500000.0,0]]],
            "_":["modes",[
              { "fx":[
                  ["Rotate",[-500000.0,0]]],
                "_":["modes",[
                  { "fx": [
                      ["Rotate",[25,0]]],
                    "_":["modes",[
                      { "fx":[], "_": ["atom",[25 ,["Rainbow",[2.  ,0xF5,0x55]]]] },
                      { "fx":[], "_": ["atom",[125,["Static" ,0x000000]]] }]]}]]}]]},
  "offsets": { [D[0]]:0, [D[1]]:-50, [D[2]]:100 } });

S_reverse_test = D=>({
  "mode": { "fx": [["Rotate",[1,0]]],
            "_":["modes",[{ "fx":[], "_": ["atom",[50,["Rainbow",[10,0xF5,0x55]]]] }]]},
  "offsets": { [D[0]]:0, [D[1]]:0, [D[2]]:0 } });
S_reverse_test_2 = D=>({
  "mode": { "fx": [["Rotate",[1,0]]],
            "_":["modes",[{ "fx":[], "_": ["atom",[3 ,["Static",0xFF00FF]]] },
                          { "fx":[], "_": ["atom",[7 ,["Static",0x000000]]] }]]},
  "offsets": { [D[0]]:0, [D[1]]:0, [D[2]]:0 } });

S_big_rainbow = D=>({
  "mode": { "fx": [["Rotate", [-10,0]], ["Brightness", 0.25]],
            "_"      : ["atom",[1000, ["Rainbow",[5.0,255,255]]]]},
  "offsets": { [D[0]]:0, [D[1]]:0, [D[2]]:0 } });

S_strange = D=>({
  // "mode": {"fx":[["Rotate",[0,5]]],"_":["modes",[{"fx":[["Rotate",[-5,0]]],"_":["modes",[["atom",[5,["Rainbow",[1,255,255]]]],["atom",[5,["Rainbow",[1,255,255]]]]]]},{"fx":[["Rotate",[-5,0]]],"_":["modes",[["atom",[5,["Rainbow",[1,255,255]]]],["atom",[5,["Rainbow",[1,255,255]]]]]]}]]},
  "mode": {"fx":[["Rotate",[25,0]]],"_":["modes",[{"fx":[],"_":["atom",[25,["Static",[0,0,0]]]]},{"fx":[["Rotate",[-25,0]]],"_":["atom",[25,["Rainbow",[1,255,55]]]]}]]},
  "offsets": { [D[0]]:0, [D[1]]:0, [D[2]]:0 } }); */