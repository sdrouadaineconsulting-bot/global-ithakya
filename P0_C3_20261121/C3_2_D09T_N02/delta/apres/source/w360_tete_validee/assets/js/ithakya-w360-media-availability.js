/* ITHAKYA W360 — media availability: non-destructive progressive enhancement. */
(()=>{'use strict';
const root=document.querySelector('main');if(!root)return;
const path=location.pathname.split('/').pop();
const fiche={'01-signature.html':'signature','02-pop-culture.html':'pop','03-progression.html':'progression','05-soleil-xl.html':'soleil'}[path];
if(!fiche)return;
const historique = new URLSearchParams(location.search).get('traversee') === 'regards';
const hasMedia=v=>Boolean(v.currentSrc||v.getAttribute('src')||v.querySelector('source[src]'));
const check=(v,failed=false)=>{
 const host=v.closest('.media-card');if(!host)return;
 let note=host.querySelector('[data-ithakya-media-fallback]');
 if(hasMedia(v)&&!failed){if(note)note.remove();return;}
 if(!note){note=document.createElement('div');note.className='ith-w360-media-fallback';note.setAttribute('data-ithakya-media-fallback','');note.setAttribute('role','status');
 const p=document.createElement('p');p.textContent=failed?'La lecture de cette vidéo a rencontré un problème. Vous pouvez poursuivre la découverte.':'Cette vidéo n’est pas disponible pour le moment.';
 const a=document.createElement('a');a.href='../oeuvres/'+fiche+'.html#formats';a.textContent='Découvrir l’histoire et ses autres prolongements';
 note.append(p,a);v.insertAdjacentElement('afterend',note);}else{const p=note.querySelector('p');if(p)p.textContent=failed?'La lecture de cette vidéo a rencontré un problème. Vous pouvez poursuivre la découverte.':'Cette vidéo n’est pas disponible pour le moment.';}
};
/* V7 : au démarrage de la lecture, un lecteur hors champ est amené à l'écran (sans animation). Un lecteur déjà visible n'est pas déplacé. */
/* Correctif P+ R3 (15/11/2026) : la part visible se mesure sous l'en-tête collant (91, 65 ou 81 px selon la largeur), qui recouvre le haut de la fenêtre ;
   sans cela, un lecteur visible à 52 % seulement (Long après « Aller plus loin », 1 440 × 900) était compté visible à 66 % et laissé en place. */
const haut0=()=>{const e=document.querySelector('header.ithc-header');if(!e)return 0;const p=getComputedStyle(e).position;return (p==='sticky'||p==='fixed')?Math.max(0,e.getBoundingClientRect().bottom):0;};
const amener=v=>{const r=v.getBoundingClientRect(),h=window.innerHeight,t0=haut0();if(!r.height)return;const visible=Math.min(r.bottom,h)-Math.max(r.top,t0);if(visible<r.height*.6)v.scrollIntoView({block:'center',behavior:'instant'});};
const videos=[...root.querySelectorAll('video')];
/* C2 / F3 : arrivée par « Reprendre » ou « Voir le Court / le Long » (?view=…) : le lecteur demandé est montré, sans lancer la lecture.
   Un rechargement ou un retour arrière gardent la position restituée par le navigateur. */
(()=>{const type=(performance.getEntriesByType('navigation')[0]||{}).type,vue=new URLSearchParams(location.search).get('view');
if(type==='reload'||type==='back_forward'||(vue!=='court'&&vue!=='long'))return;
const montrer=()=>setTimeout(()=>{const v=document.getElementById(vue+'Video');if(v&&v.offsetParent)amener(v);},150);
if(document.readyState==='complete')montrer();else window.addEventListener('load',montrer,{once:true});})();
videos.forEach(v=>{check(v);v.addEventListener('loadedmetadata',()=>check(v));v.addEventListener('loadstart',()=>check(v));v.addEventListener('error',()=>check(v,true));v.addEventListener('canplay',()=>check(v,false));if(v.id!=='longVideo'||historique)v.addEventListener('play',()=>requestAnimationFrame(()=>amener(v)));
/* C2 / F1 : à la fin du Court, le choix « Aller plus loin » reçoit le focus ; s'il est hors champ, il est amené à l'écran. */
if(historique&&v.id==='courtVideo')v.addEventListener('ended',()=>setTimeout(()=>{const b=document.getElementById('openLong');if(!b||!b.offsetParent)return;const r=b.getBoundingClientRect();if(r.top<haut0()||r.bottom>window.innerHeight)b.scrollIntoView({block:'center',behavior:'instant'});},80));
 new MutationObserver(()=>check(v)).observe(v,{attributes:true,attributeFilter:['src'],childList:true,subtree:true});});

  /* P0 D-09-T (21/11/2026) : le compteur vide est masqué aussi en mode Traversée (?traversee=regards),
     où la ligne « — explorateurs… » s'affichait à la fin du Court. Seul ce bloc précède désormais le retour du mode Traversée. */
  const compteur = document.getElementById('communityCount');
  if (compteur) {
    const ligne = compteur.closest('.community-inline');
    if (ligne) {
      const actualiser = () => {
        ligne.hidden = compteur.dataset.verifiedCount !== 'true' || !/^\d+$/.test(compteur.textContent.trim());
      };
      actualiser();
      new MutationObserver(actualiser).observe(compteur, {
        childList: true, characterData: true, subtree: true, attributes: true,
        attributeFilter: ['data-verified-count']
      });
    }
  }

if (historique) return;

  const court = document.getElementById('courtVideo');
  const long = document.getElementById('longVideo');
  const longProche = document.querySelector('.v5-sequence-guide .v-final-long-trigger');
  const longFinal = document.getElementById('openLong');
  const MEDIA_LONG_PRESENT = '[data-av03-long-fichier="present"]';
  if (!court || !long || !longProche || !longFinal || !document.querySelector(MEDIA_LONG_PRESENT)) return;

  const declencheurs = '#openLong,#openLongFromCourt,#openLongDirect,#v5GoLong,.v-final-long-trigger,[data-av03-long]';
  const completementVisible = (element) => {
    const rect = element.getBoundingClientRect();
    return rect.height > 0 && rect.top >= haut0() && rect.bottom <= window.innerHeight;
  };

  court.addEventListener('ended', () => {
    if (court.dataset.mediaEnAttente || !court.ended) return;
    const mobile = window.matchMedia('(max-width: 1024px)').matches;
    if (mobile || !completementVisible(longFinal)) {
      /* Gel des contenus (21/11) : libellé d’origine conservé, seule la présentation change. */
      longProche.classList.add('ith-w360-long-pret');
      if (!completementVisible(longProche)) longProche.classList.add('ith-w360-long-epingle');
    }
  });
  court.addEventListener('play', () => {
    longProche.classList.remove('ith-w360-long-pret', 'ith-w360-long-epingle');
  });

  document.addEventListener('click', (event) => {
    const commande = event.target.closest?.(declencheurs);
    if (!event.isTrusted || !commande || commande.disabled) return;
    const commandeAuFocus = document.activeElement === commande;
    requestAnimationFrame(() => requestAnimationFrame(() => requestAnimationFrame(() => {
      const video = long.getBoundingClientRect();
      if (!video.height || long.dataset.mediaEnAttente) return;
      const haut = haut0();
      if (video.top < haut - 1 || video.top + Math.min(72, video.height) > innerHeight) {
        window.scrollBy({ top: video.top - haut - 12, behavior: 'instant' });
      }
      if (commandeAuFocus && [commande, document.body].includes(document.activeElement)) {
        long.tabIndex = -1;
        long.focus({ preventScroll: true });
      }
    })));
  }, true);
})();
