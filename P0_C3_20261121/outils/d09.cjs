const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch();const out=[];
for(const w of [390,1440])for(const p of ['01-signature','02-pop-culture','03-progression','05-soleil-xl'])for(const q of ['','?traversee=regards']){
 const pg=await b.newPage({viewport:{width:w,height:844}});const errs=[];pg.on('pageerror',e=>errs.push(e.message.slice(0,80)));
 await pg.goto(`http://127.0.0.1:8765/demos/${p}.html${q}`,{waitUntil:'load'});await pg.waitForTimeout(800);
 const r=await pg.evaluate(()=>{const c=document.getElementById('communityCount');if(!c)return {present:false};const l=c.closest('.community-inline');const cs=l?getComputedStyle(l):null;return {present:true,texte:(l||c).textContent.trim().slice(0,60),affiche:!!(l&&cs.display!=='none'&&l.offsetParent!==null),hidden:l?l.hidden:null};});
 out.push({w,p,q:q||'-',...r,errs:errs.length});await pg.close();}
console.table(out);await b.close();})();
