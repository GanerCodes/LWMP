𝔠 = new Proxy( {}, { get(𝕊,x) { return (...𝔸) => ({ _: [x, ...𝔸] }); }});
𝖦 = (...𝔸) => [true , ...𝔸];
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
  print(`API with "${JSON.stringify(JSON.parse(body))}" → "${JSON.stringify(r, null, 2)}"`);
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
  const dev = (...𝐔) => {
    𝐔 = 𝐔.flat(1/0);
    const 𝔄𝔘 = (n,d={})=>𝔄(n,{uuids:𝐔,...d});
    const off      = (    ) => [["Off"]];
    const sync     = (    ) => [["Sync"]];
    const config   = ( dev) => [["Change_dev",{dev}]];
    const recalb_t = (   s) => config({RECALB_T:s2utcD(s??3*60**2)});
    const set_AP   = (    ) => config({AP_MODE:true});
    const scene    = (...𝔸) => { const [n,s,q,d] = 𝔸;
                                 const l = 𝔸.length;
                                 if(l == 0) return [["Pull_scenes", {}]];
                                 if(l == 1) return [["Push_scenes", {scenes:n}]];
                                 if(l == 3) return [["Set_scene"  , {scene :[n,s,q]}]];
                                 if(l == 4) return [["Push_scenes", {scenes:{[n]:s}}],
                                                    ["Set_scene"  , {scene :[n,q,d]}]] };
    const scheg    = (   S) => { if(!S) return [["Pull_schedule"]];
                                 const schedule = Object.fromEntries(S.map(([x,y]) => [s2utcW(dhms2s(...x)),y]));
                                 return [["Set_schedule", {schedule}]]; };
    const M = {sync,config,recalb_t,set_AP,off,scene,scheg};
    
    log = (...𝔸)=>console.log(...𝔸)||𝔸[0];
    const R = {
      𝐭: TOK,
      𝐔: 𝐔,
      ...Object.fromEntries(
           Object.entries(M).map(
             ([k,ƒ])=>[
               k,
               async (...𝔸)=>
                 (async v =>
                   await 𝔄𝔘(...log(v.length>1 ? ["*",{reqs: v.map(([x,...𝔸])=>𝔠[x](...𝔸))}]
                                              : v[0]))
                 )(ƒ(...𝔸))]))};
    
    // const 𝔐 = (...𝐑)=>𝔄("*",{uuids,reqs:𝐑.map((m,...𝔸)=>M[m](...𝔸))𝔠["*"]()});
    return R; };
  return {get_devs,dev}; };

// const make_mode = (offs,mode) => ({ mode, offsets:𝒟(ζ(𝒪k(offs),𝒪v(offs).Ϝ((x,y)=>x+y,0)).slice(0,-1)) });