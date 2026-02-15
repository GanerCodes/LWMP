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
scheg = async (uuids,S) => {
  if(S === undefined) return api(TOK,"Pull_schedule", {uuids});
  await api(TOK,"Set_schedule", {uuids, schedule:𝒟(S.ꟿ((x,y) => [s_to_utc(dhms2utcWs(...x)),y]))}); }
config = async (uuids,dev) => await api(TOK,"Change_dev", {uuids, dev});

// timetest snake stress balance rainbow_snake rainbow_snake_balance reverse_test reverse_test_2
devs       = "testdevice0 testdevice2 testdevice1 testdevice3".split(' ');
LEDC       = 1000;
REVERSE    = false;
RGB_ORDER  = "GBR";
BIT_TIMING = "350 900 700 700";

offs = 𝒟(devs.ᴍ(x=>[x,LEDC]));
make_mode = (offs,mode) => ({ mode, offsets:𝒟(ζ(𝒪k(offs),𝒪v(offs).Ϝ((x,y)=>x+y,0)).slice(0,-1)) });

(async _ => {

// let d = [now.getDay(),now.getHours(),now.getMinutes(),now.getSeconds()+5]

// SCENE = S_rainbow_snake(devs);
// await config(𝒪(SCENE.offsets).f(([k,v])=>v<0).ꟿ((k,v)=>(SCENE.offsets[k] = Math.abs(v), k)), {REVERSE:true});

await sync(devs);

scenes = ᴍv(require("./scenes.json"),x=>make_mode(offs,x));
scenes.synctest = S_timetest(devs,10);
await scene(devs,scenes);
await config(devs,{LEDC,REVERSE,RGB_ORDER,BIT_TIMING});

await scene(devs,"synctest",false,-1);

// now = new Date();
// let S = [];
// for(let i=0; i<15; i++) {
//   S.push([[now.getDay(),now.getHours(),now.getMinutes(),i+55],
//           [i%2?"blue":"red",false,-1]]); }
// await scheg(devs,S);

})();