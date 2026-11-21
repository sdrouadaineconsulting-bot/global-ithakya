const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:844,height:390}});
await p.goto('http://127.0.0.1:8092/exploration/missions.html',{waitUntil:'load'});await p.waitForTimeout(1500);
const r=await p.evaluate(async()=>{const H=()=>Math.round(document.querySelector('.pil-etapes').getBoundingClientRect().height);const base=H();const out=[];
const differees=[...document.querySelectorAll('link[rel=stylesheet]')].filter(l=>(l.getAttribute('onload')||'').includes('media')||l.dataset.w360||/lot-|qa360|composition|reconquete|direction|ux360|p4-cibles|p3-|p2-|nav-a2|entree|monde|avatar01/.test(l.href));
for(const l of differees){l.disabled=true;await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));const h=H();if(h!==base)out.push([l.href.split('/').pop().slice(0,50),base,h]);l.disabled=false;await new Promise(r=>requestAnimationFrame(r))}
return {base,nb:differees.length,attributs:differees.slice(0,2).map(l=>l.outerHTML.slice(0,200)),influentes:out}});console.log(JSON.stringify(r,null,1));await b.close()})();
