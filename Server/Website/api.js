𝔠 = new Proxy( {}, { get(𝕊,x) { return (...𝔸) => ({ _: [x, ...𝔸] }); }});
𝖦 = (...𝔸) => [true , ...𝔸];
𝖡 = (...𝔸) => [false, ...𝔸];

api_base = location.origin;
apiBody = (𝐭,P,...𝔸) => JSON.stringify({ 𝐭, _:[...𝔸], ...P });
api = async (𝐭,P,...𝔸) => {
  const body = apiBody(𝐭,P,...𝔸);
  const req = await fetch(`${api_base}/api`, {
    method: "POST",
    body,
    headers: { "Content-type": "application/json; charset=UTF-8" } });
  const r = await req.json();
  r.status = req.status;
  console.log(`API with "${JSON.stringify(JSON.parse(body))}" → "${JSON.stringify(r,null,2)}"`);
  return r; };
apiURL = (...𝔸) => `${api_base}/api/${encodeURIComponent(apiBody(...𝔸))}`;

const s_per_d = 60*60*24;
const s_per_w = s_per_d*7;
const utc_Δ_s = _ => new Date().getTimezoneOffset() * 60;
const s2utcW = s => ((s + utc_Δ_s())%s_per_w + s_per_w) % s_per_w;
const s2utcD = s => ((s + utc_Δ_s())%s_per_d + s_per_d) % s_per_d;
const dhms2s = (d,h,m,s) => (((d)*24+h)*60+m)*60+s;

𝐀 = (𝐭,...𝐔) => {
  let api_ƒ = api;
  if(typeof 𝐔[0] === "boolean")
    if(𝐔.shift())
      api_ƒ = apiURL;
  const 𝔄 = (...𝔸)=>api_ƒ(𝐭,...𝔸);
  const get_devs = _ => 𝔄({},"Get_devs");
  const dev = (...𝐔) => {
    𝐔 = 𝐔.flat(1/0);
    const 𝔄𝔘 = (...𝔸)=>𝔄({𝐔},...𝔸);
    const off      = (    ) => [["Off"]];
    const sync     = (    ) => [["Sync"]];
    const config   = ( dev) => [["Change_dev",dev]];
    const del      = (    ) => [["Delete_dev"]]
    const recalb_t = (   s) => config({RECALB_T:s2utcD(s??3*60**2)});
    const set_AP   = (    ) => config({AP_MODE:true});
    const scene    = (...𝔸) => { const [n,s,q,d] = 𝔸;
                                 const l = 𝔸.length;
                                 if(l == 0) return [["Pull_scenes"]];
                                 if(l == 1) return [["Push_scenes", n]];
                                 if(l == 3) return [["Set_scene"  , n,s,q]];
                                 if(l == 4) return [["Push_scenes", {[n]:s}],
                                                    ["Set_scene"  , n,q,d  ]]; };
    const scheg    = (   S) => { if(!S) return [["Pull_schedule"]];
                                 const scheg = Object.fromEntries(S.map(([x,y]) => [s2utcW(dhms2s(...x)),y]));
                                 return [["Set_schedule", scheg]]; };
    
    const M = {del,sync,config,recalb_t,set_AP,off,scene,scheg};
    const send = v=>𝔄𝔘(...v.length>1 ? ["*",...v] : v[0])
    return { type:"d",𝐭,𝐔,
             bulk: (...𝔸)=>send(𝔸.flatMap(([n,...𝔸])=>M[n](...𝔸))),
             ...Object.fromEntries(Object.entries(M).map(([k,ƒ])=>[k,(...𝔸)=>send(ƒ(...𝔸))])) }; };
  if(𝐔.length) return dev(...𝐔);
  return {type:"t",𝐭,get_devs,dev}; };

// const make_mode = (offs,mode) => ({ mode, offsets:𝒟(ζ(𝒪k(offs),𝒪v(offs).Ϝ((x,y)=>x+y,0)).slice(0,-1)) });