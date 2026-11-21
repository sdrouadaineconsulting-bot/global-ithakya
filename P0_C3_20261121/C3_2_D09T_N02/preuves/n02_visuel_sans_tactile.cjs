// N-02 : la restauration de position en paysage (844×390) est-elle visible ? Captures avant/après rechargement et retour,
// scrollY à chaque image (rAF) depuis le début de navigation. Usage : node n02_visuel.cjs BASE DOSSIER
const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path');
const [BASE, DIR] = process.argv.slice(2); fs.mkdirSync(DIR, { recursive: true });
(async () => {
  const b = await chromium.launch(); const out = [];
  for (const pg of ['exploration/atlas.html', 'exploration/missions.html']) {
    const c = await b.newContext({ viewport: { width: 844, height: 390 }, isMobile: false, hasTouch: false, reducedMotion: 'reduce' });
    await c.addInitScript(() => { window.__frames = []; const t0 = performance.now(); let n = 0;
      const f = () => { window.__frames.push([Math.round(performance.now() - t0), Math.round(scrollY)]); if (++n < 90) requestAnimationFrame(f); }; requestAnimationFrame(f); });
    const p = await c.newPage(); const nom = pg.replace(/\//g, '_');
    await p.goto(BASE + '/' + pg, { waitUntil: 'load' }); await p.waitForTimeout(1500);
    await p.mouse.wheel(0, 1200); await p.waitForTimeout(1200);
    const etat = () => p.evaluate(() => { const h = document.querySelector('header.ithc-header,header'); const hb = h ? h.getBoundingClientRect().bottom : 0;
      const e = [...document.querySelectorAll('main h1,main h2,main h3,main p,main li,main a')].find(x => { const r = x.getBoundingClientRect(); return r.top >= hb && r.height > 0; });
      return { y: Math.round(scrollY), repere: e ? (e.textContent || '').trim().slice(0, 50) : null, repere_top: e ? Math.round(e.getBoundingClientRect().top) : null, hauteur_doc: document.documentElement.scrollHeight }; });
    const r = { page: pg, avant: await etat() };
    await p.screenshot({ path: path.join(DIR, nom + '_1_avant.png') });
    await p.reload({ waitUntil: 'load' }); await p.waitForTimeout(1800);
    r.apres_rechargement = await etat(); r.images_rechargement = await p.evaluate(() => window.__frames.filter((f, i, a) => i === 0 || f[1] !== a[i - 1][1]));
    await p.screenshot({ path: path.join(DIR, nom + '_2_rechargement.png') });
    await p.goto(BASE + '/cest-quoi.html', { waitUntil: 'load' }); await p.waitForTimeout(500); await p.goBack({ waitUntil: 'load' }); await p.waitForTimeout(1800);
    r.apres_retour = await etat(); r.images_retour = await p.evaluate(() => window.__frames.filter((f, i, a) => i === 0 || f[1] !== a[i - 1][1]));
    await p.screenshot({ path: path.join(DIR, nom + '_3_retour.png') });
    out.push(r); await c.close();
  }
  fs.writeFileSync(path.join(DIR, 'N02_VISUEL.json'), JSON.stringify(out, null, 1)); console.log(JSON.stringify(out, null, 1)); await b.close();
})();
