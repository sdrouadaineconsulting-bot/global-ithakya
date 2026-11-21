// Captures à dimensions identiques + contrôle de chargement des scripts (visiteur). Usage : node captures.cjs <origine> <étiquette> <dossier>
const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path');
const [O, LAB, DIR] = process.argv.slice(2); fs.mkdirSync(path.join(DIR, LAB), { recursive: true });
const PAGES = fs.readFileSync(__dirname + '/pages37.txt', 'utf8').trim().split('\n');
const VP = [['390x844', 390, 844, true], ['768x1024', 768, 1024, true], ['1440x900', 1440, 900, false], ['844x390-paysage', 844, 390, true]];
(async () => {
  const b = await chromium.launch(); const out = [];
  for (const [nom, w, h, m] of VP) {
    const c = await b.newContext({ viewport: { width: w, height: h }, isMobile: m, hasTouch: m, reducedMotion: 'reduce' });
    for (const pg of PAGES) {
      const p = await c.newPage(); const r = { vue: nom, page: pg, scripts: [], http_err: [], js_err: [] };
      p.on('response', x => { const u = x.url().replace(O, ''); if (x.status() >= 400 && !u.includes('/api/')) r.http_err.push(x.status() + ' ' + u.slice(-70));
        if (x.request().resourceType() === 'script' && u.startsWith('/assets')) r.scripts.push(u); });
      p.on('pageerror', e => r.js_err.push(e.message.slice(0, 120)));
      try { await p.goto(O + '/' + pg, { waitUntil: 'load' }); await p.waitForTimeout(1500);
        await p.screenshot({ path: path.join(DIR, LAB, `${nom}__${pg.replace(/\//g, '_')}.png`) });
      } catch (e) { r.exception = e.message.slice(0, 120); }
      r.scripts_sans_version = r.scripts.filter(u => !/\?sha=[0-9a-f]{12}/.test(u) && !/-[0-9a-f]{12}\.js/.test(u) && !/\/vendor\//.test(u));
      r.nb_scripts = r.scripts.length; delete r.scripts; out.push(r); await p.close();
    }
    await c.close();
  }
  fs.writeFileSync(path.join(DIR, `CAPTURES_${LAB}.json`), JSON.stringify(out, null, 1)); console.log('ok', out.length); await b.close();
})();
