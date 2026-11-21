/* V9.9.71 : liens internes en chemins relatifs (le format #itk: ne fonctionnait que dans l'édition autonome). */
var ITH_ROOT=(/\/demos\//.test(location.pathname)?'../':'');
/* ITHAKYA V9.9.62 — Carnet éditorial, isolé des XP, Points, Premium et ATTENZIA. */
(function(){'use strict';
const KEY='ithakya_carnet_v1';
try{localStorage.removeItem(KEY)}catch(e){} /* V9.9.71 : efface les données des versions précédentes ; la mémoire ne dure plus que le temps de l'onglet */
const CATALOG=[
 {id:'science',title:'Le lien',universe:'Sciences & Tech',url:'01-signature.html',poster:'ITHAKYA_POSTER_SIGNATURE_COURT_960X540.webp',idea:'Les relations invisibles qui relient les phénomènes.',next:'sport'},
 {id:'culture',title:'Le moment',universe:'Divertissement & Pop culture',url:'02-pop-culture.html',poster:'ITHAKYA_POSTER_POP_COURT_960X540.webp',idea:'Tout ce qui prépare un instant visible.',next:'science'},
 {id:'sport',title:'L’élan',universe:'Sport & Aventure',url:'03-progression.html',poster:'ITHAKYA_POSTER_PROGRESSION_COURT_960X540.webp',idea:'L’observation et l’adaptation derrière le geste.',next:'culture'},
 {id:'solar',title:'Le courant',universe:'Soleil & cosmos',url:'05-soleil-xl.html',poster:'ITHAKYA_POSTER_SOLEIL_COURT_960X540.webp',idea:'Ce qui relie l’activité solaire à notre planète.',next:'science'}
].concat(/\/demos\/04-retail-media(?:\.html)?\/?$/.test(location.pathname)?[ /* espace partenaire uniquement (20/10/2026) */
 {id:'retail',title:'Le choix',universe:'Retail Media',url:'04-retail-media.html',poster:'ITHAKYA_POSTER_RETAIL_COURT_960X540.webp',idea:'Ce qui rend une offre disponible et laisse un choix au client.',next:'science'}
]:[]);
const route=location.pathname.replace(/\/+$/,'').split('/').pop()||'';
const currentFile=route.replace(/\.html$/i,'')+'.html';
const current=CATALOG.find(x=>x.url===currentFile)||null;
const byId=id=>CATALOG.find(x=>x.id===id)||null;
const make=(tag,klass,value)=>{const el=document.createElement(tag);if(klass)el.className=klass;if(value!==undefined)el.textContent=value;return el};
function inspect(){try{
 const raw=sessionStorage.getItem(KEY);if(raw===null)return {ok:true,items:[]};
 const obj=JSON.parse(raw);if(!obj||obj.version!==1||!Array.isArray(obj.ids))return {ok:false,items:[],reason:'Format de Carnet non reconnu : aucune donnée n’a été modifiée.'};
 const ids=[...new Set(obj.ids)].filter(x=>typeof x==='string'&&byId(x)).slice(0,CATALOG.length);
 return {ok:true,items:ids};
}catch(e){return {ok:false,items:[],reason:'Mémoire de visite indisponible : vos choix ne peuvent pas être gardés pendant cette visite.'}}}
function persist(ids){try{sessionStorage.setItem(KEY,JSON.stringify({version:1,ids:ids}));return true}catch(e){return false}}
function openItem(item,type){const a=make('a',type==='long'?'ith62-link muted':'ith62-link',type==='long'?'Voir le Long':'Revoir le Court');a.href=item.url+'?view='+(type==='long'?'long':'court');return a}
function initialize(){if(!current||document.getElementById('ith62-carnet'))return;
 const root=document.querySelector('section#progress.view > .panel');if(!root)return;
 let feedback=()=>{};
 const choice=document.getElementById('postCourt');if(choice){
  const note=make('div','ith62-keep');const keep=make('button','ith62-keep-button','Garder cette découverte');keep.type='button';keep.setAttribute('aria-pressed','false');
  const status=make('span','ith62-save-status');status.setAttribute('role','status');status.setAttribute('aria-live','polite');note.append(keep,status);
  /* P0-L9 (C-06, 21/11/2026) : « Garder » placé après « Explorer une autre œuvre » ; repli inchangé. */const autre=choice.querySelector('.ux79-post-more > .ux79-other');const actions=choice.querySelector('.post-actions');if(autre)autre.insertAdjacentElement('afterend',note);else if(actions)actions.insertAdjacentElement('afterend',note);else choice.appendChild(note);
  keep.addEventListener('click',()=>{const data=inspect();if(!data.ok){status.textContent=data.reason;return}
   const added=!data.items.includes(current.id);const items=added?[current.id,...data.items].slice(0,CATALOG.length):data.items.filter(id=>id!==current.id);
   if(!persist(items)){status.textContent='Mémoire de visite indisponible dans ce navigateur.';return}
   status.textContent=added?'Découverte gardée dans cet onglet.':'Découverte retirée de vos favoris.';
   feedback();
  });
  feedback=()=>{const data=inspect();const isSaved=data.ok&&data.items.includes(current.id);keep.textContent=isSaved?'Retirer des découvertes gardées':'Garder cette découverte';keep.setAttribute('aria-pressed',String(isSaved));keep.disabled=!data.ok;if(!data.ok){status.textContent=data.reason}};
 }
 const box=make('section','ith62-carnet');box.id='ith62-carnet';box.setAttribute('aria-label','Mon Carnet de découvertes');
 const head=make('div','ith62-carnet-head');head.appendChild(make('span','ith62-kicker','MON ITHAKYA · CARNET PERSONNEL'));
 const counter=make('span','ith62-count');head.appendChild(counter);box.appendChild(head);
 box.appendChild(make('h3',null,'Découvertes gardées'));
 box.appendChild(make('span','ith62-intro','Gardez les sujets qui vous intéressent pendant votre visite. Rien n’est envoyé ; la mémoire est limitée à cet onglet ; une restauration de session peut la conserver.'));
 const list=make('div','ith62-list');box.appendChild(list);
 const suggestion=make('div','ith62-suggestion');box.appendChild(suggestion);
 const explanations=make('span','ith62-disclaimer','Aucune sélection n’augmente les XP, Points ou avantages Premium. Les pistes proposées sont des rapprochements éditoriaux, pas une recommandation calculée sur vos données personnelles.');box.appendChild(explanations);
 const older=document.getElementById('ith61-memory');if(older)older.insertAdjacentElement('afterend',box);else root.appendChild(box);
 const hero=document.querySelector('#home .ux79-court-copy');
 const original=choice?.querySelector('.ith62-keep-button');
 if(hero && original){
  let early=hero.querySelector('.ith10003-keep-early');
  if(!early){
   early=make('button','text-link ith10003-keep-early','Garder cette découverte');
   early.type='button';
   hero.appendChild(early);
  }
  const syncEarly=()=>{
   early.textContent=original.textContent;
   early.setAttribute('aria-pressed',original.getAttribute('aria-pressed'));
   early.disabled=original.disabled;
  };
  early.addEventListener('click',()=>{original.click();syncEarly();});
  const oldFeedback=feedback;
  feedback=()=>{oldFeedback();syncEarly();};
 }
 const prev=feedback;
 feedback=()=>{prev();const data=inspect();list.replaceChildren();suggestion.replaceChildren();
  if(!data.ok){counter.textContent='Sauvegarde indisponible';list.appendChild(make('span','ith62-empty',data.reason));return}
  counter.textContent=data.items.length+' / '+CATALOG.length+' découvertes';
  if(!data.items.length){const empty=make('div','ith62-empty','Votre Carnet est vide. Après un Court, choisissez « Garder cette découverte » pour le retrouver ici.');list.appendChild(empty)}
  else data.items.forEach(id=>{const item=byId(id);const card=make('article','ith62-card');
   const img=make('img');img.src='../posters/'+item.poster;img.loading='lazy';img.decoding='async';img.alt='';img.width=120;img.height=80;card.appendChild(img);
   const text=make('div','ith62-card-body');text.appendChild(make('span','ith62-universe',item.universe));text.appendChild(make('strong',null,item.title));text.appendChild(make('span','ith62-idea',item.idea));
   const actions=make('div','ith62-card-actions');actions.append(openItem(item,'court'),openItem(item,'long'));
   const del=make('button','ith62-delete','Retirer');del.type='button';del.setAttribute('aria-label','Retirer '+item.title+' du Carnet');del.addEventListener('click',()=>{
    const read=inspect();if(!read.ok)return;if(persist(read.items.filter(x=>x!==id)))feedback();else{del.disabled=true;del.textContent='Stockage indisponible'}
   });actions.appendChild(del);text.appendChild(actions);card.appendChild(text);list.appendChild(card)
  });
  const anchor=byId(data.items[0]||current.id);
  const target=byId(anchor.next);
  if(target&&!data.items.includes(target.id)){
   suggestion.appendChild(make('span','ith62-reason','UNE PISTE POUR CONTINUER'));
   suggestion.appendChild(make('strong',null,target.title+' · '+target.universe));
   suggestion.appendChild(make('span','ith62-why',data.items.length?'Parce que vous avez gardé « '+anchor.title+' », ce sujet offre un autre regard sur ce qui reste invisible au premier coup d’œil.':'Pour commencer, découvrez un autre univers. Cette proposition est éditoriale et ne dépend pas de vos données.'));
   suggestion.appendChild(openItem(target,'court'));
  }else{
   suggestion.appendChild(make('span','ith62-reason','UN AUTRE CHEMIN POSSIBLE'));
   suggestion.appendChild(make('strong',null,'Ce que l’image ne montre pas'));
   suggestion.appendChild(make('span','ith62-why','Prolongez vos découvertes par une Traversée éditoriale à trois regards.'));
   const a=make('a','ith62-link','Explorer la Traversée');a.href=ITH_ROOT+'traversee.html';suggestion.appendChild(a);
  }
 };
 function sync(){feedback()}
 sync();window.addEventListener('pageshow',sync);window.addEventListener('storage',sync);
 document.addEventListener('visibilitychange',()=>{if(!document.hidden)sync()});
 document.addEventListener('click',event=>{const t=event.target;if(t&&t.closest&&t.closest('[data-view="progress"]'))Promise.resolve().then(sync)},true)
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',initialize);else initialize();
})();
