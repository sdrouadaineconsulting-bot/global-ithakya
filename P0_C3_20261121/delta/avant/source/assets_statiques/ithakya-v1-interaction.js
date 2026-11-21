/* ITHAKYA V1 — interaction native dans le lecteur : une question à un repère du Long.
 * Principe : la réponse choisie au repère est CONSERVÉE puis transmise par le chemin existant de la page (le bouton de réponse du quiz),
 * donc validée par le serveur (une seule attribution, bonne réponse comparée côté serveur, crédit seulement après validation du Long).
 * Aucun calcul de Points ici. Visiteur sans compte : aucune interaction proposée (rien ne pourrait être enregistré). */
(function () {
  'use strict';
  /* V1 (accessibilité) : des boutons masqués et vides, créés par des scripts historiques des pages démonstratrices, sont signalés sans nom accessible. */
  function nommer() { [].forEach.call(document.querySelectorAll('button'), function (b) { if (!(b.textContent || '').trim() && !b.getAttribute('aria-label') && !b.getAttribute('aria-labelledby') && !b.getAttribute('title')) { b.setAttribute('aria-label', 'Action masquée'); if (b.hidden) b.setAttribute('aria-hidden', 'true'); } }); }
  nommer(); try { new MutationObserver(function () { nommer(); }).observe(document.documentElement, { childList: true, subtree: true }); } catch (_) {}
  var video = document.getElementById('longVideo'), panel = document.getElementById('quizPanel');
  if (!video || !panel) return;
  var question = (panel.querySelector('p b') || {}).textContent || '';
  var reponses = [].slice.call(panel.querySelectorAll('[data-answer]'));
  if (!question || reponses.length < 2) return;
  var repere = Number(video.getAttribute('data-repere-s')) || 0, fait = false, choisi = null, overlay = null, retour = null;
  var apiSession = new URL('../api/ithakya-pilote.php?action=session', document.baseURI).href;
  var membre = null;
  fetch(apiSession, { credentials: 'same-origin', cache: 'no-store' }).then(function (r) { return r.json(); }).then(function (j) { membre = !!(j && j.user); }).catch(function () { membre = false; });
  window.ITHAKYA_V1_INTERACTION = { etat: function () { return { membre: membre, repere: repere, fait: fait, choisi: choisi, ouvert: !!overlay }; } };
  function fermer() { if (overlay) { overlay.remove(); overlay = null; } if (retour && retour.focus) retour.focus(); }
  function ouvrir() {
    retour = document.activeElement; video.pause();
    overlay = document.createElement('div'); overlay.className = 'v1i'; overlay.setAttribute('role', 'dialog'); overlay.setAttribute('aria-modal', 'true'); overlay.setAttribute('aria-labelledby', 'v1i-q');
    var box = document.createElement('div'); box.className = 'v1i-box';
    var k = document.createElement('p'); k.className = 'v1i-k'; k.textContent = 'UNE QUESTION EN CHEMIN · facultatif';
    var q = document.createElement('p'); q.id = 'v1i-q'; q.className = 'v1i-q'; q.textContent = question;
    var liste = document.createElement('div'); liste.className = 'v1i-r';
    reponses.forEach(function (b, i) {
      var c = document.createElement('button'); c.type = 'button'; c.textContent = b.textContent;
      c.addEventListener('click', function () { choisi = i; q.textContent = 'Réponse notée. Elle sera enregistrée à la fin du Long.'; liste.remove(); plus.textContent = 'Reprendre le film'; plus.focus(); });
      liste.appendChild(c);
    });
    var plus = document.createElement('button'); plus.type = 'button'; plus.className = 'v1i-p'; plus.textContent = 'Répondre plus tard';
    plus.addEventListener('click', function () { fermer(); video.play().catch(function () {}); });
    box.appendChild(k); box.appendChild(q); box.appendChild(liste); box.appendChild(plus); overlay.appendChild(box);
    overlay.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') { fermer(); video.play().catch(function () {}); }
      if (e.key === 'Tab') { var f = [].slice.call(overlay.querySelectorAll('button')); if (!f.length) return; var i = f.indexOf(document.activeElement); if (e.shiftKey && i <= 0) { f[f.length - 1].focus(); e.preventDefault(); } else if (!e.shiftKey && i === f.length - 1) { f[0].focus(); e.preventDefault(); } }
    });
    (video.parentNode || document.body).appendChild(overlay);
    var premier = overlay.querySelector('.v1i-r button'); if (premier) premier.focus();
  }
  video.addEventListener('loadedmetadata', function () { if (!repere && video.duration > 10) repere = Math.round(video.duration * 0.65); });
  video.addEventListener('timeupdate', function () {
    if (!repere && video.duration > 10) repere = Math.round(video.duration * 0.65);
    if (fait || !membre || !repere || video.seeking) return;
    if (video.currentTime >= repere && video.currentTime < repere + 4) { fait = true; ouvrir(); }
  });
  video.addEventListener('ended', function () {
    if (choisi === null) return;
    var i = choisi; choisi = null;
    /* laisse le suivi de lecture enregistrer la fin du Long, puis transmet la réponse par le bouton existant du quiz */
    setTimeout(function () { var b = reponses[i]; if (b) b.click(); }, 1800);
  });
  var st = document.createElement('style');
  st.textContent = '.v1i{position:absolute;inset:0;z-index:30;display:flex;align-items:center;justify-content:center;background:rgba(6,14,22,.82);padding:16px}.v1i-box{max-width:520px;width:100%;background:#10273b;color:#eef3f8;border:1px solid rgba(255,255,255,.18);border-radius:14px;padding:18px}.v1i-k{margin:0 0 6px;font-size:12px;letter-spacing:.08em;color:#c9d6e3}.v1i-q{margin:0 0 12px;font-size:18px;font-weight:700;line-height:1.3}.v1i-r{display:grid;gap:8px}.v1i button{font:inherit;color:#eef3f8;background:#1b3d5a;border:1px solid rgba(255,255,255,.25);border-radius:10px;padding:10px 12px;text-align:left;cursor:pointer;min-height:44px}.v1i button:focus-visible{outline:3px solid #f0c674;outline-offset:2px}.v1i-p{margin-top:12px;background:transparent!important;text-decoration:underline}';
  document.head.appendChild(st);
  var zone = video.parentNode; if (zone && getComputedStyle(zone).position === 'static') zone.style.position = 'relative';
})();
