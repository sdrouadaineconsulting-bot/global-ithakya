// V1 après patch : lecture continue, membre. Usage: node v1c3.cjs BASE page W H sortie.json [repondre=1]
const { chromium } = require('playwright'); const fs = require('fs');
const [BASE, PAGE, W, H, OUT, REP] = process.argv.slice(2);
(async () => {
  const b = await chromium.launch({ args: ['--autoplay-policy=no-user-gesture-required'] });
  const ctx = await b.newContext({ viewport: { width: +W, height: +H } }); const pg = await ctx.newPage(); const res = { page: PAGE, viewport: `${W}x${H}` };
  await ctx.addInitScript(() => { window.__mv = []; const L = (k, a) => window.__mv.push({ k, a, t: Math.round(performance.now()) });
    const siv = Element.prototype.scrollIntoView; Element.prototype.scrollIntoView = function (...x) { L('scrollIntoView', this.id || this.className); return siv.apply(this, x); };
    for (const n of ['scrollTo', 'scrollBy', 'scroll']) { const o = window[n]; window[n] = function (...x) { L(n, JSON.stringify(x).slice(0, 60)); return o.apply(this, x); }; } });
  await pg.goto(`${BASE}/index.html`);
  res.inscription = await pg.evaluate(async () => { const api = '/api/ithakya-pilote.php'; const s = await (await fetch(api + '?action=session')).json(); const l = 'v1c' + Math.random().toString(16).slice(2, 10);
    return (await fetch(api + '?action=register', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': s.csrf }, body: JSON.stringify({ login: l, display_name: 'Banc V1', password: 'phrase de passe banc v1 ' + l }) })).status; });
  await pg.goto(`${BASE}/demos/${PAGE}.html?view=long`, { waitUntil: 'load' }); await pg.waitForTimeout(1500);
  await pg.evaluate(async () => { const v = document.getElementById('longVideo'); v.muted = true; if (v.readyState < 1) await new Promise(r => { v.addEventListener('loadedmetadata', r, { once: true }); setTimeout(r, 8000); }); await v.play().catch(() => {}); });
  await pg.waitForFunction(() => { const v = document.getElementById('longVideo'); return v.currentTime >= v.duration * 0.65 + 2 || v.paused; }, null, { timeout: 90000 }).catch(() => {});
  res.apres_repere = await pg.evaluate(() => { const v = document.getElementById('longVideo'); return { t: +v.currentTime.toFixed(2), pause: v.paused, overlay: !!document.querySelector('.v1i'), etat: window.ITHAKYA_V1_INTERACTION.etat() }; });
  await pg.waitForFunction(() => document.getElementById('longVideo').ended, null, { timeout: 90000 }).catch(() => {});
  const y0 = await pg.evaluate(() => { window.__mv = []; return Math.round(scrollY); });
  await pg.waitForTimeout(800);
  res.fin = await pg.evaluate(() => { const v = document.getElementById('longVideo'), o = document.querySelector('.v1i'); return { ended: v.ended, overlay: !!o, focus: (document.activeElement.textContent || '').slice(0, 50), scrollY: Math.round(scrollY) }; });
  res.fin.y0 = y0;
  await pg.screenshot({ path: OUT.replace('.json', '_fin.png') });
  if (REP === '1' && res.fin.overlay) {
    await pg.click('.v1i-r button >> nth=0'); await pg.waitForTimeout(400);
    res.apres_reponse = await pg.evaluate(() => ({ texte: (document.querySelector('.v1i-q') || {}).textContent, boutons: document.querySelectorAll('.v1i button').length }));
    await pg.waitForTimeout(4500);
  } else if (res.fin.overlay) { await pg.click('.v1i-p'); await pg.waitForTimeout(1500); }
  res.cloture = await pg.evaluate(async () => { const v = document.getElementById('longVideo'); const p = await (await fetch('/api/ithakya-pilote.php?action=progression')).json();
    return { overlay: !!document.querySelector('.v1i'), ended: v.ended, t: +v.currentTime.toFixed(1), pause: v.paused, scrollY: Math.round(scrollY), xp: p.xp, points: p.points, journal: (p.journal || []).map(j => j.action + ':' + j.xp), mouvements: window.__mv }; });
  fs.writeFileSync(OUT, JSON.stringify(res, null, 1)); console.log(JSON.stringify(res)); await b.close();
})();
