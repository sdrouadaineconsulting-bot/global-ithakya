const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();const c=await b.newContext({viewport:{width:844,height:390},isMobile:true,hasTouch:true});
await c.addInitScript(()=>{const L=(k)=>{try{const a=JSON.parse(sessionStorage.getItem('dbg')||'[]');a.push([k,Math.round(scrollY),document.documentElement.scrollHeight,document.visibilityState]);sessionStorage.setItem('dbg',JSON.stringify(a))}catch(e){}};
addEventListener('beforeunload',()=>L('beforeunload'),true);addEventListener('pagehide',()=>L('pagehide(capture)'),true);document.addEventListener('visibilitychange',()=>L('visibility:'+document.visibilityState),true);
let armed=false;addEventListener('beforeunload',()=>{armed=true},true);addEventListener('scroll',()=>{if(armed)L('scroll-pendant-dechargement')},true);
new ResizeObserver(()=>{if(armed)L('resize-pendant-dechargement')}).observe(document.documentElement);});
const p=await c.newPage();await p.goto('http://127.0.0.1:8093/exploration/atlas.html',{waitUntil:'load'});await p.waitForTimeout(1500);await p.evaluate(()=>sessionStorage.removeItem('dbg'));await p.mouse.wheel(0,1200);await p.waitForTimeout(1200);
console.log('avant',await p.evaluate(()=>[scrollY,document.documentElement.scrollHeight,innerHeight,visualViewport.height]));
await p.reload({waitUntil:'load'});await p.waitForTimeout(800);console.log(await p.evaluate(()=>sessionStorage.getItem('dbg')));
// témoin sans Playwright reload : navigation par location.reload()
await p.evaluate(()=>sessionStorage.removeItem('dbg'));await p.evaluate(()=>scrollTo(0,1200));await p.waitForTimeout(1200);
await Promise.all([p.waitForNavigation(),p.evaluate(()=>location.reload())]);await p.waitForTimeout(800);console.log('location.reload',await p.evaluate(()=>sessionStorage.getItem('dbg')));
await b.close()})();
