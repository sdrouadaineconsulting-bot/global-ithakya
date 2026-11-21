// Stabilité P0 §11/§14 : 37 pages × 4 vues, visiteur (et membre si MEMBRE=1).
// Mesures : CLS, ET déplacements programmatiques (scrollTo/scrollBy/scroll/scrollIntoView/focus/ancres), variations de scrollY
// sans entrée utilisateur, position/hauteur de l'en-tête (100 ms × 30), ouverture/fermeture du menu, débordement horizontal.
// Usage : node stabilite.cjs <origine> <étiquette> <sortie.json>
const { chromium } = require('playwright'); const fs = require('fs');
const [O, LAB, OUT] = process.argv.slice(2);
const PAGES = fs.readFileSync(__dirname + '/pages37.txt', 'utf8').trim().split('\n');
const VP = [['390x844', 390, 844, true], ['768x1024', 768, 1024, true], ['1440x900', 1440, 900, false], ['844x390-paysage', 844, 390, true]]
  .filter(v => !process.env.VUES || process.env.VUES.split(',').includes(v[0]));
const INIT = () => {
  window.__mv = []; window.__cls = 0; window.__t0 = performance.now();
  const log = (k, a) => { try { window.__mv.push({ k, t: Math.round(performance.now() - window.__t0), y: Math.round(scrollY), a: a, s: (new Error().stack || '').split('\n').slice(2, 4).map(x => x.trim().replace(location.origin, '')).join(' < ') }); } catch (e) {} };
  for (const n of ['scrollTo', 'scrollBy', 'scroll']) { const o = window[n]; window[n] = function (...x) { log('window.' + n, JSON.stringify(x).slice(0, 80)); return o.apply(this, x); }; }
  const siv = Element.prototype.scrollIntoView; Element.prototype.scrollIntoView = function (...x) { log('scrollIntoView', (this.id || this.className || this.tagName).toString().slice(0, 40)); return siv.apply(this, x); };
  const fo = HTMLElement.prototype.focus; HTMLElement.prototype.focus = function (...x) { log('focus', (this.id || this.className || this.tagName).toString().slice(0, 40) + ' ' + JSON.stringify(x)); return fo.apply(this, x); };
  let ly = 0; addEventListener('scroll', () => { const y = Math.round(scrollY); if (y !== ly) { window.__mv.push({ k: 'scroll', t: Math.round(performance.now() - window.__t0), de: ly, a: y }); ly = y; } }, { passive: true });
  try { new PerformanceObserver(l => { for (const x of l.getEntries()) if (!x.hadRecentInput) window.__cls += x.value; }).observe({ type: 'layout-shift', buffered: true }); } catch (e) {}
};
(async () => {
  const b = await chromium.launch(); const out = [];
  for (const [nom, w, h, m] of VP) {
    const c = await b.newContext({ viewport: { width: w, height: h }, isMobile: m, hasTouch: m });
    await c.addInitScript(INIT);
    if (process.env.MEMBRE) {
      const p0 = await c.newPage(); await p0.goto(O + '/index.html');
      await p0.evaluate(async () => { const api = '/api/ithakya-pilote.php'; const s = await (await fetch(api + '?action=session')).json(); const l = 'st' + Math.random().toString(16).slice(2, 10);
        await fetch(api + '?action=register', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': s.csrf }, body: JSON.stringify({ login: l, display_name: 'Banc stabilite', password: 'phrase de passe stabilite ' + l }) }); });
      await p0.close();
    }
    for (const pg of PAGES) {
      const p = await c.newPage(); const err = []; const navs = [];
      p.on('pageerror', x => err.push('pageerror ' + x.message.slice(0, 120)));
      p.on('framenavigated', f => { if (f === p.mainFrame()) navs.push(f.url().replace(O, '')); });
      const r = { vue: nom, page: pg, profil: process.env.MEMBRE ? 'membre' : 'visiteur' };
      try {
        await p.goto(O + '/' + pg, { waitUntil: 'load' });
        const hdr = [];
        for (let i = 0; i < 30; i++) { hdr.push(await p.evaluate(() => { const e = document.querySelector('header.ithc-header,header'); if (!e) return null; const x = e.getBoundingClientRect(); return [Math.round(x.top), Math.round(x.height)]; })); await p.waitForTimeout(100); }
        const hs = hdr.filter(Boolean);
        r.entete = { positions: [...new Set(hs.map(x => x[0]))], hauteurs: [...new Set(hs.map(x => x[1]))] };
        r.chargement = await p.evaluate(() => ({ cls: +window.__cls.toFixed(4), mouvements: window.__mv.slice(0, 12), scrollY: Math.round(scrollY) }));
        r.debordementX = await p.evaluate(() => document.documentElement.scrollWidth - innerWidth);
        // Menu : ouverture puis fermeture (Échap), position de page et en-tête avant/après
        const menu = await p.$('nav button[aria-expanded], .ithc-header button[aria-expanded]');
        if (menu && await menu.isVisible()) {
          const avant = await p.evaluate(() => { window.__mv = []; const e = document.querySelector('header.ithc-header,header'); return { y: Math.round(scrollY), h: e ? Math.round(e.getBoundingClientRect().height) : null }; });
          await menu.click(); await p.waitForTimeout(400); await p.keyboard.press('Escape'); await p.waitForTimeout(400);
          r.menu = { avant, apres: await p.evaluate(() => { const e = document.querySelector('header.ithc-header,header'); return { y: Math.round(scrollY), h: e ? Math.round(e.getBoundingClientRect().height) : null, mv: window.__mv.filter(x => x.k !== 'focus').slice(0, 6) }; }) };
        }
        // Défilement volontaire puis immobilité 1,5 s : aucun mouvement non sollicité attendu
        const H = await p.evaluate(() => document.documentElement.scrollHeight);
        const cible = Math.min(1200, Math.max(0, H - h - 10));
        await p.mouse.wheel(0, cible); await p.waitForTimeout(600);
        const y0 = await p.evaluate(() => { window.__mv = []; return Math.round(scrollY); });
        await p.waitForTimeout(1500);
        r.immobilite = await p.evaluate(y0 => ({ y0, y1: Math.round(scrollY), mv: window.__mv.slice(0, 6) }), y0);
        // Rechargement et retour arrière (restauration attendue)
        await p.reload({ waitUntil: 'load' }); await p.waitForTimeout(1500);
        r.rechargement = await p.evaluate(y0 => ({ avant: y0, apres: Math.round(scrollY), mv: window.__mv.filter(x => x.k !== 'scroll').slice(0, 6) }), y0);
        await p.goto(O + '/cest-quoi.html', { waitUntil: 'load' }); await p.waitForTimeout(400); await p.goBack({ waitUntil: 'load' }); await p.waitForTimeout(1500);
        r.retour = await p.evaluate(y0 => ({ avant: y0, apres: Math.round(scrollY), type: performance.getEntriesByType('navigation')[0].type, mv: window.__mv.filter(x => x.k !== 'scroll').slice(0, 6) }), y0);
        r.navigations = navs;
      } catch (e) { r.exception = e.message.slice(0, 160); }
      r.erreurs = err; out.push(r); await p.close();
    }
    await c.close();
  }
  fs.writeFileSync(OUT, JSON.stringify(out, null, 1)); console.log('ok', out.length); await b.close();
})();
