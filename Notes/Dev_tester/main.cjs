require("./joon.cjs");
require("./scenes.cjs");

𝔠 = new Proxy( {}, { get(𝕊,x) { return (...𝔸) => ({ _: [x, ...𝔸] }); }});
𝖦 = (...𝔸) => [true, ...𝔸];
𝖡 = (...𝔸) => [false, ...𝔸];

api_body = (token, method, ...dat) => 𝔍.þ02191({ token, ...𝔠[method](...dat) });
api = async (token, method, ...dat) => {
  const body = api_body(token, method, ...dat);
  const req = await fetch("http://localhost:4004/api", {
    method: "POST",
    body,
    headers: { "Content-type": "application/json; charset=UTF-8" } });
  const r = await req.json();
  r.status = req.status;
  print(`API with "${𝔍.þ02191(𝔍.þ02193(body))}" → "${𝔍.þ02191(r, null, 2)}"`);
  return r; };
apiURL = (...𝔸) => `${location.origin}/call/${encodeURIComponent(api_body(...𝔸))}`;

const s_to_utc = s => {
  const s_per_w = (s_per_d = 60*60*24)*7;
  const offset = new Date().getTimezoneOffset() * 60;
  return ((s + offset) % s_per_w + s_per_w) % s_per_w; }
const dhms2utcWs = (d,h,m,s) => (((d)*24+h)*60+m)*60+s;

TOK = "testing"
sync  = async uuids => await api(TOK,"Sync", {uuids});
scene = async (uuids,...𝔸) => {
  const [n,s,q,d] = 𝔸;
  if(𝔸.length == 0) return await api(TOK,"Pull_scenes", {uuids                });
  if(𝔸.length == 1) return await api(TOK,"Push_scenes", {uuids, scenes:n      });
  if(𝔸.length != 3)        await api(TOK,"Push_scenes", {uuids, scenes:{[n]:s}});
  else              return await api(TOK,"Set_scene"  , {uuids, scene :[n,s,q]});
  if(𝔸.length == 4) return await api(TOK,"Set_scene"  , {uuids, scene :[n,q,d]}); };
scheg = async (uuids,...𝔸) => await api(TOK,"Set_schedule", {uuids, schedule:𝒟(𝔸.ꟿ((x,y) => [s_to_utc(dhms2utcWs(...x)),y]))});
config = async (uuids,dev) => await api(TOK,"Change_dev", {uuids, dev});

// timetest snake stress balance rainbow_snake rainbow_snake_balance reverse_test reverse_test_2
devs       = "testdevice0 testdevice2 testdevice1 testdevice3".split(' ');
LEDC       = 50;
REVERSE    = false;
RGB_ORDER  = "GBR";
BIT_TIMING = "350 900 700 700";

now = new Date();
offs = 𝒟(devs.ᴍ(x=>[x,LEDC]));
make_mode = (offs,mode) => ({ mode, offsets:𝒟(ζ(𝒪k(offs),𝒪v(offs).Ϝ((x,y)=>x+y,0)).slice(0,-1)) });

(async _ => {

// let d = [now.getDay(),now.getHours(),now.getMinutes(),now.getSeconds()+5]
// await scheg(devs, [d, ["test",false,null]])

// SCENE = S_rainbow_snake(devs);
// flip = 𝒪 Object.entries(SCENE.offsets).f(([k,v])=>v<0).map(([k,v])=>(SCENE.offsets[k] = Math.abs(v), k));
// await config(flip, {REVERSE:true});

scenes = {}
scenes.test_time = S_timetest(devs,120);
// scenes.rainbowstatics = make_mode(offs, {"effects":[["Rotate",[0,0]]],"_":["modes",[{"effects":[["Rotate",[25,0]]],"_":["modes",[{"effects":[],"_":["atom",[25,["Rainbow",[1,245,50]]]]},{"effects":[],"_":["atom",[25,["Static",[68,0,0]]]]}]]},{"effects":[["Rotate",[25,0]]],"_":["modes",[{"effects":[],"_":["atom",[25,["Rainbow",[1,245,50]]]]},{"effects":[],"_":["atom",[25,["Static",[0,68,0]]]]}]]},{"effects":[["Rotate",[25,0]]],"_":["modes",[{"effects":[],"_":["atom",[25,["Rainbow",[1,245,50]]]]},{"effects":[],"_":["atom",[25,["Static",[0,0,68]]]]}]]},{"effects":[["Rotate",[25,0]]],"_":["modes",[{"effects":[],"_":["atom",[25,["Rainbow",[1,245,50]]]]},{"effects":[],"_":["atom",[25,["Static",[68,0,68]]]]}]]}]]});
// scenes.test1 = make_mode(offs, {"effects":[["Rotate",[25,0]]],"_":["modes",[{"effects":[],"_":["atom",[25,["Rainbow",[1,245,50]]]]},{"effects":[],"_":["atom",[175,["Static",[0,0,0]]]]}]]});
// scenes.test1 = make_mode(offs, {"effects":[["Rotate",[0,0]]],"_":["modes",[{"effects":[["Rotate",[25,0]]],"_":["modes",[{"effects":[],"_":["atom",[25,["Rainbow",[1,245,50]]]]},{"effects":[],"_":["atom",[25,["Static",[0,0,0]]]]}]]},{"effects":[["Rotate",[25,0]]],"_":["modes",[{"effects":[],"_":["atom",[25,["Rainbow",[1,245,50]]]]},{"effects":[],"_":["atom",[25,["Static",[0,0,0]]]]}]]},{"effects":[["Rotate",[25,0]]],"_":["modes",[{"effects":[],"_":["atom",[25,["Rainbow",[1,245,50]]]]},{"effects":[],"_":["atom",[25,["Static",[0,0,0]]]]}]]},{"effects":[["Rotate",[25,0]]],"_":["modes",[{"effects":[],"_":["atom",[25,["Rainbow",[1,245,50]]]]},{"effects":[],"_":["atom",[25,["Static",[0,0,0]]]]}]]}]]});
// scenes.test2 = make_mode(offs, {"effects":[["Rotate",[0,0]]],"_":["modes",[{"effects":[["Rotate",[45,0]]],"_":["modes",[{"effects":[],"_":["atom",[25,["Static",[34,34,34]]]]},{"effects":[],"_":["atom",[25,["Static",[0,0,0]]]]}]]},{"effects":[["Rotate",[45,0]]],"_":["modes",[{"effects":[],"_":["atom",[25,["Static",[34,34,34]]]]},{"effects":[],"_":["atom",[25,["Static",[0,0,0]]]]}]]},{"effects":[["Rotate",[45,0]]],"_":["modes",[{"effects":[],"_":["atom",[25,["Static",[34,34,34]]]]},{"effects":[],"_":["atom",[25,["Static",[0,0,0]]]]}]]},{"effects":[["Rotate",[45,0]]],"_":["modes",[{"effects":[],"_":["atom",[25,["Static",[34,34,34]]]]},{"effects":[],"_":["atom",[25,["Static",[0,0,0]]]]}]]}]]});
// scenes.test3 = make_mode(offs, {"effects":[["Rotate",[0,0]]],"_":["modes",[{"effects":[["Rotate",[45,0]]],"_":["modes",[{"effects":[],"_":["atom",[25,["Static",[255,0,0]]]]},{"effects":[],"_":["atom",[25,["Static",[0,0,0]]]]}]]},{"effects":[["Rotate",[45,0]]],"_":["modes",[{"effects":[],"_":["atom",[25,["Static",[0,255,0]]]]},{"effects":[],"_":["atom",[25,["Static",[0,0,0]]]]}]]},{"effects":[["Rotate",[45,0]]],"_":["modes",[{"effects":[],"_":["atom",[25,["Static",[0,0,255]]]]},{"effects":[],"_":["atom",[25,["Static",[0,0,0]]]]}]]},{"effects":[["Rotate",[45,0]]],"_":["modes",[{"effects":[],"_":["atom",[25,["Static",[255,0,255]]]]},{"effects":[],"_":["atom",[25,["Static",[0,0,0]]]]}]]}]]});
scenes.test_fade = make_mode(offs, {"effects":[["Rotate",[0,0]]],"_":["modes",[{"effects":[],"_":["atom",[50,["Fade",{"speed":0.1,"sharp":0,"clrs":[[255,0,0],[0,255,0],[0,0,255]]}]]]},{"effects":[],"_":["atom",[50,["Fade",{"speed":0.1,"sharp":0.5,"clrs":[[255,0,0],[0,255,0],[0,0,255]]}]]]},{"effects":[],"_":["atom",[50,["Fade",{"speed":0.1,"sharp":0.75,"clrs":[[255,0,0],[0,255,0],[0,0,255]]}]]]},{"effects":[],"_":["atom",[50,["Fade",{"speed":0.1,"sharp":0.875,"clrs":[[255,0,0],[0,255,0],[0,0,255]]}]]]}]]});
await scene(devs, scenes);

// await sync(devs);
await config(devs, {LEDC,REVERSE,RGB_ORDER,BIT_TIMING});
await scene(devs,"test_fade",false,-1);

// await scene(devs,"test1",true,3*1000);
// await scene(devs,"test2",true,3*1000);
// await scene(devs,"test1",true,3*1000);
// await scene(devs,"test2",true,3*1000);

})();