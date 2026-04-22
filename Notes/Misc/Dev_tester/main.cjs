require("./joon.cjs");
require("./scenes.cjs");

𝔠 = new Proxy( {}, { get(𝕊,x) { return (...𝔸) => ({ _: [x, ...𝔸] }); }});
𝖦 = (...𝔸) => [true, ...𝔸];
𝖡 = (...𝔸) => [false, ...𝔸];

api_body = (𝐭,𝐦,...dat) => JSON.stringify({ token:𝐭, ...𝔠[𝐦](...dat) });
api = async (𝐭,𝐦,...dat) => {
  const body = api_body(𝐭,𝐦,...dat);
  const req = await fetch("http://localhost:4004/api", {
    method: "POST",
    body,
    headers: { "Content-type": "application/json; charset=UTF-8" } });
  const r = await req.json();
  r.status = req.status;
  print(`API with "${𝔍.þ02191(𝔍.þ02193(body))}" → "${𝔍.þ02191(r, null, 2)}"`);
  return r; };
apiURL = (...𝔸) => `${location.origin}/call/${encodeURIComponent(api_body(...𝔸))}`;

const s_per_d = 60*60*24;
const s_per_w = s_per_d*7;
const utc_Δ_s = _ => new Date().getTimezoneOffset() * 60;
const s2utcW = s => ((s + utc_Δ_s())%s_per_w + s_per_w) % s_per_w;
const s2utcD = s => ((s + utc_Δ_s())%s_per_d + s_per_d) % s_per_d;
const dhms2s = (d,h,m,s) => (((d)*24+h)*60+m)*60+s;

𝐀 = TOK => {
  const 𝔄 = (...𝔸)=>api(TOK,...𝔸);
  const get_devs = async _ => await 𝔄("Get_devs");
  const dev = uuids => {
    const 𝔄𝔘 = (n,d={})=>𝔄(n,{uuids,...d});
    const sync     = async (    ) => await 𝔄𝔘("Sync");
    const config   = async ( dev) => await 𝔄𝔘("Change_dev",{dev});
    const recalb_t = async (   s) => await config({RECALB_T:s2utcD(s??3*60**2)});
    const set_AP   = async (    ) => await config({AP_MODE:true});
    const scheg    = async (   S) => { if(!S) return 𝔄𝔘("Pull_schedule");
                                       const schedule = 𝒟(S.ꟿ((x,y) => [s2utcW(dhms2s(...x)),y]));
                                       return await 𝔄𝔘("Set_schedule", {schedule}); };
    const scene    = async (...𝔸) => { const [n,s,q,d] = 𝔸;
                                       const l = 𝔸.length;
                                       if(l == 0) return await 𝔄𝔘("Pull_scenes", {              });
                                       if(l == 1) return await 𝔄𝔘("Push_scenes", {scenes:n      });
                                       if(l != 3)        await 𝔄𝔘("Push_scenes", {scenes:{[n]:s}});
                                       else       return await 𝔄𝔘("Set_scene"  , {scene :[n,s,q]});
                                       if(l == 4) return await 𝔄𝔘("Set_scene"  , {scene :[n,q,d]}); };
    return {sync,config,recalb_t,set_AP,scheg,scene}; };
  return {get_devs,dev}; };

const make_mode = (offs,mode) => ({ mode, offsets:𝒟(ζ(𝒪k(offs),𝒪v(offs).Ϝ((x,y)=>x+y,0)).slice(0,-1)) });

(async _ => {
  with(𝐀("testing")) {
    log(await get_devs());
    const devs = "testdevice0 testdevice2 testdevice1 testdevice3".split(' ');
    with(dev(devs)) {
      const conf = {LEDC:50,REVERSE:false,RGB_ORDER:"GBR",BIT_TIMING:"350 900 700 700"};
      const offs = 𝒟(devs.ᴍ(x=>[x,conf.LEDC]));
      const scenes = ᴍv(require("./scenes.json"),x=>make_mode(offs,x));
      scenes.synctest = S_timetest(devs,120);
      // await set_AP();
      
      // SCENE = S_rainbow_snake(devs);
      // await config(𝒪(SCENE.offsets).f(([k,v])=>v<0).ꟿ((k,v)=>(SCENE.offsets[k] = Math.abs(v), k)), {REVERSE:true});

      // await sync();

      await config(conf);
      await recalb_t(); //set to custom time for debugging w/ dhms2s(0,4,53,0);
      await scene(scenes);
      await scene("rainbow",false,-1);
      // await scene("synctest",false,-1);
      // await scene("fade_test",false,-1);
      // await scene("thousand",false,-1);

      // let [now,S] = [new Date(),[]];
      // for(let i=0; i<15; i++) {
      //   S.push([[now.getDay(),now.getHours(),now.getMinutes(),now.getSeconds()+i],
      //           [i%2?"blue":"red",false,-1]]); }
      // await scheg(S);
    }
  }
})();