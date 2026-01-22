{ "effects": [
    { "_": ["Rotate", {
              "speed":-1,
              "offset":0}]}],
  "_": ["Atom", {
          "leds":50,
          "_": ["Rainbow",{
                  "segs":5.0,
                  "sat":255,
                  "val":255 }]}]}

preset_normal = (0.1,-0.2, [(-0.2,0.1, [(0,0,250)]), (-5,0.25, [(0,0,250)])])


(offset,speed,stuff)

def parse_mode(mode,brightness=1):
  atoms = []
  
  r0,rΔ = 0,0
  reverse = 0
  for x in mode["effects"]:
    t,v = 𝔪(mode)
    if t == "brightness":
      brightness *= v
  t,v = 𝔪(mode)
  
  
  