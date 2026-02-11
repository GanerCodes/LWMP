S_timetest = (D,s=10)=>({
  "mode": { "effects": [["Rotate",[s,0]]],
            "_":["modes",[{ "effects":[], "_": ["atom",[10,["Static",[0x44,0x44,0x44]]]] },
                          { "effects":[], "_": ["atom",[40,["Static",[0x00,0x00,0x00]]]] }]]},
  "offsets": { [D[0]]:0, [D[1]]:0, [D[2]]:0, [D[3]]:0 } });
S_snake = D=>({
  "mode": { "effects": [["Rotate",[1,0]]],
            "_":["modes",[{ "effects":[], "_": ["atom",[2 ,["Static",[0x00,0x00,0xFF]]]] },
                          { "effects":[], "_": ["atom",[13 ,["Static",[0x00,0x00,0x00]]]] }]]},
  "offsets": { [D[0]]:0, [D[1]]:5, [D[2]]:10 } });
S_stress = D=>({
  "mode": { "effects": [
              ["Rotate",[20.34,0]]],
            "_":["modes",[
              { "effects":[
                  ["Brightness",0.5]],
                "_":["atom",
                  [250,["Static" ,[0xFF,0x00,0xFF]]]] },
              { "effects":[],
                "_": ["atom",
                  [250,["Rainbow",[5.25,0xE9,0xFF]]]] },
              { "effects":[
                  ["Reverse",true],
                  ["Brightness",0.5],
                  ["Rotate",[-20.34,23.2]]],
                "_":["modes",[
                  { "effects":[
                      ["Rotate",[ 20.34,23.2]]],
                    "_": ["atom",
                      [250,["Rainbow",[50.25,0xE9,0xFF]]]]},
                  { "effects":[
                      ["Rotate",[  0.00,23.2]]],
                    "_": ["atom",
                      [250,["Static",[0x00,0xFF,0x00]]]]}]] }]]},
  "offsets": { [D[0]]:0, [D[1]]:0, [D[2]]:0 } });
S_balance = D=>({
  "mode": { "effects":[
              ["Rotate",[500000.0,0]]],
            "_":["modes",[
              { "effects":[
                  ["Rotate",[-500000.0,0]]],
                "_":["atom",
                  [50,["Rainbow",[10.0,0xFF,0xFF]]]] }]]},
  "offsets": { [D[0]]:0, [D[1]]:0, [D[2]]:0 } });

S_rainbow_snake = D=>({
  "mode": { "effects": [["Rotate",[30,0]]],
            "_":["modes",[{ "effects":[], "_": ["atom",[25 ,["Rainbow",[2.  ,0xF5,0x55]]]] },
                          { "effects":[], "_": ["atom",[175,["Static" ,[0x00,0x00,0x00]]]] }]]},
  "offsets": { [D[0]]:0, [D[1]]:-50, [D[2]]:100, [D[2]]:-150 } });

S_rainbow_snake_balance = D=>({
  "mode": { "effects":[
              ["Rotate",[500000.0,0]]],
            "_":["modes",[
              { "effects":[
                  ["Rotate",[-500000.0,0]]],
                "_":["modes",[
                  { "effects": [
                      ["Rotate",[25,0]]],
                    "_":["modes",[
                      { "effects":[], "_": ["atom",[25 ,["Rainbow",[2.  ,0xF5,0x55]]]] },
                      { "effects":[], "_": ["atom",[125,["Static" ,[0x00,0x00,0x00]]]] }]]}]]}]]},
  "offsets": { [D[0]]:0, [D[1]]:-50, [D[2]]:100 } });

S_reverse_test = D=>({
  "mode": { "effects": [["Rotate",[1,0]]],
            "_":["modes",[{ "effects":[], "_": ["atom",[50,["Rainbow",[10,0xF5,0x55]]]] }]]},
  "offsets": { [D[0]]:0, [D[1]]:0, [D[2]]:0 } });
S_reverse_test_2 = D=>({
  "mode": { "effects": [["Rotate",[1,0]]],
            "_":["modes",[{ "effects":[], "_": ["atom",[3 ,["Static",[0xFF,0x00,0xFF]]]] },
                          { "effects":[], "_": ["atom",[7 ,["Static",[0x00,0x00,0x00]]]] }]]},
  "offsets": { [D[0]]:0, [D[1]]:0, [D[2]]:0 } });

S_big_rainbow = D=>({
  "mode": { "effects": [["Rotate", [-10,0]], ["Brightness", 0.25]],
            "_"      : ["atom",[1000, ["Rainbow",[5.0,255,255]]]]},
  "offsets": { [D[0]]:0, [D[1]]:0, [D[2]]:0 } });

S_strange = D=>({
  // "mode": {"effects":[["Rotate",[0,5]]],"_":["modes",[{"effects":[["Rotate",[-5,0]]],"_":["modes",[["atom",[5,["Rainbow",[1,255,255]]]],["atom",[5,["Rainbow",[1,255,255]]]]]]},{"effects":[["Rotate",[-5,0]]],"_":["modes",[["atom",[5,["Rainbow",[1,255,255]]]],["atom",[5,["Rainbow",[1,255,255]]]]]]}]]},
  "mode": {"effects":[["Rotate",[25,0]]],"_":["modes",[{"effects":[],"_":["atom",[25,["Static",[0,0,0]]]]},{"effects":[["Rotate",[-25,0]]],"_":["atom",[25,["Rainbow",[1,255,55]]]]}]]},
  "offsets": { [D[0]]:0, [D[1]]:0, [D[2]]:0 } });