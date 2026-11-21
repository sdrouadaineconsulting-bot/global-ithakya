// D-09 en mode Traversée (?traversee=regards) : visibilité de la ligne « — explorateurs » à chaque étape. Usage: node d09_traversee.cjs BASE OUT
const { chromium } = require('playwright'); const fs = require('fs'); const [BASE, OUT] = process.argv.slice(2);
(async () => { const b = await chromium.launch({ args: ['--autoplay-policy=no-user-gesture-required'] }); const res = [];
 for (const profil of ['visiteur', 'membre']) for (const q of ['', '?traversee=regards']) {
  const c = await b.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true }); const p = await c.newPage();
  if (profil === 'membre') { await p.goto(BASE + '/index.html'); await p.evaluate(async () => { const api = '/api/ithakya-pilote.php'; const s = await (await fetch(api + '?action=session')).json(); const l = 'dz' + Math.random().toString(16).slice(2, 10);
    await fetch(api + '?action=register', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': s.csrf }, body: JSON.stringify({ login: l, display_name: 'Banc D09', password: 'phrase de passe d09 ' + l }) }); }); }
  const etat = () => p.evaluate(() => { const c = document.getElementById('communityCount'); const l = c && c.closest('.community-inline'); if (!l) return null; const r = l.getBoundingClientRect();
    return { texte: l.textContent.trim().slice(0, 50), hidden: l.hidden, affiche: !!(l.offsetParent && r.height > 0 && getComputedStyle(l).visibility !== 'hidden'), dans_ecran: r.bottom > 0 && r.top < innerHeight }; });
  const r = { profil, mode: q || 'standard' };
  await p.goto(BASE + '/demos/01-signature.html' + q, { waitUntil: 'load' }); await p.waitForTimeout(1500); r.chargement = await etat();
  try { await p.click('#openCourt'); await p.waitForFunction(() => { const v = document.querySelector('#courtVideo'); return v && !v.paused; }, null, { timeout: 15000 });
   await p.waitForFunction(() => document.querySelector('#courtVideo').ended, null, { timeout: 60000 }); await p.waitForTimeout(2500); r.fin_court = await etat();
   await p.evaluate(() => { const l = document.querySelector('.community-inline'); if (l) l.scrollIntoView({ block: 'center' }); }); await p.waitForTimeout(400); r.fin_court_section_visee = await etat();
   await p.screenshot({ path: OUT.replace('.json', `_${profil}_${q ? 'traversee' : 'standard'}.png`) });
  } catch (e) { r.exception = e.message.slice(0, 120); }
  res.push(r); await c.close(); }
 fs.writeFileSync(OUT, JSON.stringify(res, null, 1)); for (const r of res) console.log(JSON.stringify(r)); await b.close(); })();
