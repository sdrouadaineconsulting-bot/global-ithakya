// Mesure V1 à 65 % du Long, média présent (mires), membre connecté. Usage: node v1.cjs BASE page largeur hauteur sortie.json
const { chromium } = require('playwright');
const [BASE, PAGE, W, H, OUT] = process.argv.slice(2);
(async () => {
  const b = await chromium.launch({ args: ['--autoplay-policy=no-user-gesture-required'] });
  const ctx = await b.newContext({ viewport: { width: +W, height: +H } });
  const pg = await ctx.newPage();
  const res = { page: PAGE, viewport: `${W}x${H}` };
  await pg.goto(`${BASE}/index.html`);
  const reg = await pg.evaluate(async () => {
    const api = '/api/ithakya-pilote.php';
    let s = await (await fetch(api + '?action=session', { credentials: 'same-origin' })).json();
    const login = 'v1' + Math.random().toString(16).slice(2, 10);
    const r = await fetch(api + '?action=register', { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': s.csrf }, body: JSON.stringify({ login, display_name: 'Banc V1', password: 'phrase de passe banc v1 ' + login }) });
    return r.status;
  });
  res.inscription = reg;
  await pg.goto(`${BASE}/demos/${PAGE}.html?view=long`, { waitUntil: 'load' });
  await pg.waitForTimeout(1500);
  res.v1_etat_initial = await pg.evaluate(() => window.ITHAKYA_V1_INTERACTION && window.ITHAKYA_V1_INTERACTION.etat());
  // Ouvrir le Long par l'interface si un déclencheur existe
  const trig = await pg.$('#openLongDirect, #v5GoLong, #openLong');
  if (trig && await trig.isVisible()) { await trig.click(); res.declencheur = await trig.getAttribute('id'); }
  await pg.waitForTimeout(800);
  const info = await pg.evaluate(async () => {
    const v = document.getElementById('longVideo');
    if (!v) return { erreur: 'pas de longVideo' };
    v.muted = true;
    if (!(v.readyState >= 1)) await new Promise(r => { v.addEventListener('loadedmetadata', r, { once: true }); setTimeout(r, 8000); });
    return { duree: v.duration, src: (v.currentSrc || '').replace(location.origin, ''), visible: !!v.offsetParent };
  });
  res.long = info;
  await pg.evaluate(async () => { const v = document.getElementById('longVideo'); v.muted = true; await v.play().catch(() => {}); });
  res.t_depart = await pg.evaluate(() => document.getElementById('longVideo').currentTime);
  await pg.waitForFunction(() => { const v = document.getElementById('longVideo'); return v.currentTime >= v.duration * 0.65 + 1 || v.paused; }, null, { timeout: 90000 }).catch(() => {});
  res.au_repere = await pg.evaluate(() => {
    const v = document.getElementById('longVideo'), o = document.querySelector('.v1i');
    const rv = v.getBoundingClientRect(), ro = o && o.getBoundingClientRect();
    return { t: +v.currentTime.toFixed(2), pause: v.paused, overlay: !!o,
      couverture_video: ro ? +((Math.min(rv.bottom, ro.bottom) - Math.max(rv.top, ro.top)) * (Math.min(rv.right, ro.right) - Math.max(rv.left, ro.left)) / (rv.width * rv.height)).toFixed(2) : 0,
      fond: o ? getComputedStyle(o).backgroundColor : null, focus: document.activeElement && (document.activeElement.textContent || '').slice(0, 40),
      etat: window.ITHAKYA_V1_INTERACTION && window.ITHAKYA_V1_INTERACTION.etat(), scrollY: scrollY };
  });
  await pg.screenshot({ path: OUT.replace('.json', '_repere.png') });
  await pg.waitForTimeout(3000);
  res.trois_s_plus_tard = await pg.evaluate(() => { const v = document.getElementById('longVideo'); return { t: +v.currentTime.toFixed(2), pause: v.paused, overlay: !!document.querySelector('.v1i') }; });
  // Reprise par « Répondre plus tard »
  const plus = await pg.$('.v1i-p');
  if (plus) { await plus.click(); await pg.waitForTimeout(1500); }
  res.apres_reporter = await pg.evaluate(() => { const v = document.getElementById('longVideo'); return { t: +v.currentTime.toFixed(2), pause: v.paused, overlay: !!document.querySelector('.v1i') }; });
  // Fin du Long : présence du quiz de la page
  await pg.waitForFunction(() => document.getElementById('longVideo').ended, null, { timeout: 90000 }).catch(() => {});
  await pg.waitForTimeout(2500);
  res.fin_du_long = await pg.evaluate(() => {
    const v = document.getElementById('longVideo'), q = document.getElementById('quizPanel');
    return { ended: v.ended, quizPanel_visible: !!(q && q.offsetParent && getComputedStyle(q).visibility !== 'hidden'), quizPanel_hidden_attr: q ? q.hidden : null,
      quiz_texte: q ? (q.querySelector('p b') || {}).textContent : null, overlay: !!document.querySelector('.v1i') };
  });
  await pg.screenshot({ path: OUT.replace('.json', '_fin.png') });
  require('fs').writeFileSync(OUT, JSON.stringify(res, null, 1));
  console.log(JSON.stringify(res));
  await b.close();
})();
