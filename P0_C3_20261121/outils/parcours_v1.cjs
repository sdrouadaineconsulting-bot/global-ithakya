// Parcours membre complet par l'interface : Court → Long → V1 (où qu'elle s'ouvre) → crédits. Usage: node parcours_v1.cjs BASE page W H sortie.json
const { chromium } = require('playwright'); const fs = require('fs');
const [BASE, PAGE, W, H, OUT] = process.argv.slice(2);
(async () => {
  const b = await chromium.launch({ args: ['--autoplay-policy=no-user-gesture-required'] });
  const ctx = await b.newContext({ viewport: { width: +W, height: +H } }); const p = await ctx.newPage(); const r = { base: BASE, page: PAGE, vue: `${W}x${H}`, v1: [] };
  await ctx.addInitScript(() => { window.__mv = []; const L = (k, a) => window.__mv.push({ k, a, t: Math.round(performance.now()), y: Math.round(scrollY) });
    const siv = Element.prototype.scrollIntoView; Element.prototype.scrollIntoView = function (...x) { L('scrollIntoView', this.id || this.className); return siv.apply(this, x); };
    for (const n of ['scrollTo', 'scrollBy']) { const o = window[n]; window[n] = function (...x) { L(n, JSON.stringify(x).slice(0, 60)); return o.apply(this, x); }; } });
  await p.goto(BASE + '/index.html');
  await p.evaluate(async () => { const api = '/api/ithakya-pilote.php'; const s = await (await fetch(api + '?action=session')).json(); const l = 'pv' + Math.random().toString(16).slice(2, 10);
    await fetch(api + '?action=register', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': s.csrf }, body: JSON.stringify({ login: l, display_name: 'Banc parcours', password: 'phrase de passe parcours ' + l }) }); });
  const solde = () => p.evaluate(async () => { const j = await (await fetch('/api/ithakya-pilote.php?action=progression')).json(); return { xp: j.xp, points: j.points, journal: (j.journal || []).map(x => x.action + ':' + x.xp + '/' + x.points) }; });
  await p.goto(`${BASE}/demos/${PAGE}.html`, { waitUntil: 'load' }); await p.waitForTimeout(1500);
  await p.click('#openCourt');
  await p.waitForFunction(() => { const v = document.querySelector('#courtVideo'); return v && !v.paused && v.currentTime > 0.3; }, null, { timeout: 15000 });
  await p.waitForFunction(() => document.querySelector('#courtVideo').ended, null, { timeout: 60000 }); await p.waitForTimeout(4000);
  r.apres_court = await solde();
  const proche = '.v5-sequence-guide .v-final-long-trigger';
  const cible = await p.evaluate(s => { const t = document.querySelector(s); if (!t) return '#openLong'; const x = t.getBoundingClientRect(); return (x.height > 0 && x.top >= 0 && x.bottom <= innerHeight) ? s : '#openLong'; }, proche);
  if (cible === '#openLong') await p.evaluate(() => document.querySelector('#openLong').scrollIntoView({ block: 'center' }));
  await p.click(cible); r.commande_long = cible;
  await p.waitForFunction(() => { const v = document.querySelector('#longVideo'); return v && !v.paused && v.currentTime > 0.3; }, null, { timeout: 20000 });
  await p.evaluate(() => { document.querySelector('#longVideo').muted = true; });
  // Surveillance jusqu'à la fin du Long : ouverture éventuelle de V1 pendant la lecture
  const t0 = Date.now(); let fin = false;
  while (Date.now() - t0 < 110000) {
    const e = await p.evaluate(() => { const v = document.querySelector('#longVideo'); return { t: +v.currentTime.toFixed(1), d: v.duration, pause: v.paused, ended: v.ended, overlay: !!document.querySelector('.v1i'), y: Math.round(scrollY) }; });
    if (e.overlay) {
      const y0 = e.y; await p.waitForTimeout(2000);
      const e2 = await p.evaluate(() => { const v = document.querySelector('#longVideo'); return { t: +v.currentTime.toFixed(1), pause: v.paused, ended: v.ended }; });
      r.v1.push({ ouverture: e, deux_s_plus_tard: e2, pendant_lecture: !e.ended });
      await p.click('.v1i-r button >> nth=0'); await p.waitForTimeout(300);
      if (await p.$('.v1i-p')) await p.click('.v1i-p');
      await p.waitForTimeout(2500);
      r.v1[r.v1.length - 1].apres = await p.evaluate(y0 => { const v = document.querySelector('#longVideo'); return { overlay: !!document.querySelector('.v1i'), pause: v.paused, ended: v.ended, dy: Math.round(scrollY) - y0 }; }, y0);
    }
    if (e.ended && !e.overlay) { if (fin) break; fin = true; await p.waitForTimeout(1500); continue; }
    await p.waitForTimeout(500);
  }
  await p.waitForTimeout(4000);
  r.final = await solde(); r.mouvements = await p.evaluate(() => window.__mv);
  fs.writeFileSync(OUT, JSON.stringify(r, null, 1)); console.log(JSON.stringify(r)); await b.close();
})();
