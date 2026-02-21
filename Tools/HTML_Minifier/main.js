import {minify as minifyJS} from "terser";
import {minify} from "html-minifier-next";

const input = await (new Promise(r => {
  let d="";
  process.stdin.setEncoding("utf8");
  process.stdin.on("data", c => d += c);
  process.stdin.on("end", () => r(d)); }));

console.log(
  await minify(
     input,
     { collapseWhitespace:true,
       removeComments:true,
       minifyCSS:true,
    	 minifyJS:async (x,_) => 
          (await minifyJS(x,{ module:true})).code }));