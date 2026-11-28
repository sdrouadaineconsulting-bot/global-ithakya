# INTEGRATION_W360 — contrat d'intégration des médias W360 dans la candidate définitive

Version 1 — 2026-11-28. Destinataire : la session qui finalise la candidate (socle gelé S39-B).
Ce document ne modifie rien dans le socle : il décrit ce qu'il faudra y brancher une fois toutes les vidéos réunies.

## 1. État des médias

| ID | Univers | Format | Œuvre | Mode de diffusion | État au 2026-11-28 |
|---|---|---|---|---|---|
| W360-ST-COURT | Sciences & Tech | Court | One Revolution per Minute | Fichier | Récupéré et qualifié : copie de diffusion Vimeo 2160p, 3840x1620, 9 162 images à 24 i/s, SHA-256 `110019832645ff2fdd30182cad6f804195e000afcf6e3a38fed0e076dae9b0a9`. Copie de conservation : Google Drive de l'utilisateur, fichier `1CJ4UXh8CSWY6Lk8LFwhjgWA5sMnsODpk`. |
| W360-ST-LONG | Sciences & Tech | Long | D'étranges signaux radios… | Fichier | À fournir |
| W360-SA-COURT | Sport & Aventure | Court | Why I Fly | Fichier | À fournir (+ versions voix off EN/DE/IT/ES si disponibles) |
| W360-SA-LONG | Sport & Aventure | Long | Weightless | Fichier | À fournir |
| W360-PC-COURT | Pop Culture & Divertissement | Court | PROZACZOPIXAN | Fichier | À fournir |
| W360-PC-LONG | Pop Culture & Divertissement | Long | Intro Pandemonium… | Fichier | À fournir |
| W360-GT-FILM | La Grande Traversée | Film intégral | Priorities | Intégration Vimeo (code de l'auteur) | Validé ; `03_integration/` |

Les vidéos ne sont jamais versionnées dans git (limite GitHub : 100 Mo par fichier). Le dépôt ne contient que les métadonnées, les outils et le présent contrat.

## 2. Procédure quand toutes les vidéos sont réunies

1. Déposer chaque fichier dans `01_masters/<ID>.<ext>` (copie depuis Drive : lien de partage, puis téléchargement par `drive.usercontent.google.com`, domaine autorisé dans l'environnement « Par défaut »).
2. `sh 07_outils/preparer.sh` : ffprobe, SHA-256, HLS fMP4 (échelle 3840 → 640 selon la largeur du master, images-clés à 2 s), MP4 de repli ≤ 1920 px, sous-titres HLS, affiche, affiche dynamique 6 s, miniatures 25/50/75 %, manifeste régénéré.
3. Publier `02_declinaisons/` et `03_affiches_miniatures/` sur l'hébergement retenu (section 5). Reporter l'URL de base dans `MEDIA_BASE_URL` (section 3).
4. Appliquer les branchements de la section 4 dans la candidate, puis dérouler la recette (section 6).

## 3. Schéma de données média (à ajouter à côté de `ITHAKYA_MEDIA_LIBRARY`)

`ITHAKYA_MEDIA_LIBRARY` reste en place (chemins `.mp4` par univers, `court` et `long`) pour la compatibilité. Le nouvel objet le complète :

```js
const MEDIA_BASE_URL = 'https://<hébergement>/w360/';          // à fixer à la mise en ligne
const ITHAKYA_MEDIA_W360 = Object.freeze({
  'Sciences & Tech': { court: 'W360-ST-COURT', long: 'W360-ST-LONG' },
  'Sport & Aventure': { court: 'W360-SA-COURT', long: 'W360-SA-LONG' },
  'Pop Culture & Divertissement': { court: 'W360-PC-COURT', long: 'W360-PC-LONG' },
  'La Grande Traversée': { film: 'W360-GT-FILM' }
});
// Une entrée par média, générée depuis 06_manifeste/manifeste.json :
// { id, mode: 'fichier' | 'vimeo',
//   hls: MEDIA_BASE_URL + '<ID>/hls/master.m3u8', mp4: MEDIA_BASE_URL + '<ID>/<ID>_repli.mp4',
//   poster, posterDynamic, thumbnails: [..],
//   subtitles: [{ lang: 'fr', label: 'Français', src: MEDIA_BASE_URL + '<ID>/hls/subs/fr.vtt', auto: false }],
//   editorialDurationSec, communityThresholdSec,              // section ATTENZIA du manifeste
//   vimeo: { videoId: '93124212' } }                           // mode 'vimeo' uniquement
```

## 4. Branchements dans le socle (relevés dans la démo 07, V4.9)

| Point du socle | Comportement actuel | Branchement W360 |
|---|---|---|
| `applyThemeMediaSources()` | `video.src = media.court` (MP4 local) selon `state.territory` | Appeler `attachMedia(video, entry)` : HLS natif si `video.canPlayType('application/vnd.apple.mpegurl')`, sinon hls.js ; en cas d'échec, `entry.mp4`. |
| `prepareLongMedia()` | `longVideoDemo.src = src` | Même `attachMedia(longVideoDemo, entryLong)`. |
| Sous-titres | aucun | Une balise `<track kind="subtitles" srclang label src>` par entrée `subtitles`, en mode `disabled` par défaut (VO conservée) ; libellé « (automatique) » si `auto: true`. |
| `VisibleTimeTracker` | échantillonne toutes les 250 ms pendant la lecture, onglet visible, fenêtre focalisée | Inchangé pour les médias « fichier ». Pour Priorities (Vimeo), alimenter le suivi à partir des événements `ithakya:embed-progress` (`visibleTimeSec` déjà calculé selon la même règle). |
| `AttentionEngine.buildSessionMetrics({editorialDurationSec, visibleTimeSec, completionRatio})` | `editorialDurationSec = video.duration` | Fichier : inchangé. Vimeo : `durationSec` de l'événement `ithakya:embed-ready`. |
| Long qualifié | 80 % de séquence unique regardée | Vimeo : `completionRatio` de `ithakya:embed-progress` (`percent` du lecteur). Vérifier en recette que la notion de « séquence unique » reste respectée (le lecteur Vimeo ne distingue pas les relectures). |
| Note K | signal éditorial seul, après le Court, découplé de l'XP et des Points (RM-03 / SOC-02) | Aucun changement. |

Esquisse de `attachMedia` (hls.js à épingler à une version exacte au moment de l'intégration) :

```js
function attachMedia(el, m) {
  el.querySelectorAll('track').forEach(t => t.remove());
  (m.subtitles || []).forEach(s => { const t = document.createElement('track');
    Object.assign(t, { kind: 'subtitles', srclang: s.lang, label: s.label + (s.auto ? ' (automatique)' : ''), src: s.src });
    el.appendChild(t); t.track.mode = 'disabled'; });
  if (m.poster) el.poster = m.poster;
  if (el.canPlayType('application/vnd.apple.mpegurl')) { el.src = m.hls; }
  else if (window.Hls && Hls.isSupported()) { const h = new Hls(); h.loadSource(m.hls); h.attachMedia(el);
    h.on(Hls.Events.ERROR, (_, d) => { if (d.fatal) { h.destroy(); el.src = m.mp4; } }); }
  else { el.src = m.mp4; }
  el.load();
}
```

Priorities : remplacer le conteneur `<video>` par le fragment `03_integration/W360-GT-FILM_vimeo_embed.html` (code de l'auteur repris tel quel + adaptateur `ithakya:embed-*`). Domaines Vimeo à autoriser dans la politique de sécurité du contenu (CSP) de la candidate, le cas échéant : `player.vimeo.com` et les domaines de ressources du lecteur, à relever en recette.

## 5. Hébergement des déclinaisons

- Stockage objet ou CDN (pas git). Arborescence publiée telle quelle : `<ID>/hls/…`, `<ID>/<ID>_repli.mp4`, affiches et miniatures.
- Types MIME : `.m3u8` → `application/vnd.apple.mpegurl` ; `.m4s` et `*_init.mp4` → `video/iso.segment` ou `video/mp4` ; `.vtt` → `text/vtt`.
- CORS : autoriser l'origine de la candidate (requis par hls.js et par les pistes `<track>`).
- Masters (`01_masters/`) : conservés hors ligne, jamais publiés.

## 6. Recette (à dérouler avant mise en ligne)

- [ ] Chaque média se lit en entier (durée = durée qualifiée ±1 image) sur Safari macOS/iOS (HLS natif), Chrome, Firefox, Edge (hls.js) et Android.
- [ ] Repli MP4 effectif quand le HLS est coupé (simuler une erreur réseau sur `master.m3u8`).
- [ ] Changement de variante HLS sans coupure ni désynchronisation audio.
- [ ] Sous-titres désactivés par défaut ; activables ; synchronisés (Why I Fly FR et EN-US, ORPM EN automatique).
- [ ] ATTENZIA : le temps visible ne progresse qu'en lecture, onglet visible, fenêtre focalisée ; seuil communauté à 50 % ; aucun gain hors de ces conditions.
- [ ] Long qualifié à 80 % ; Note K sans effet sur l'XP, les Points et les phases.
- [ ] Priorities : événements `ithakya:embed-ready/play/pause/progress/ended` reçus ; temps visible cohérent avec la lecture réelle.
- [ ] Proportions natives respectées (pas de recadrage) : 3840x1620 pour ORPM, ≈ 2,39:1 pour Priorities.
- [ ] Affiches et miniatures affichées ; affiche dynamique muette et en boucle.
- [ ] Aucune requête vers un domaine non prévu (console réseau).

## 7. Mise en ligne

1. Geler la liste des médias (aucun « À fournir » restant, ou décision explicite de reporter une œuvre).
2. Publier les déclinaisons, vérifier les URL depuis un navigateur extérieur.
3. Fusionner les branchements de la section 4 dans la candidate gelée, recette complète, puis mise en ligne avec le socle.

## 8. Où se trouve quoi

- Dépôt `global-ithakya`, branche de travail de cette session, dossier `w360/` : ce contrat, les deux paquets sans vidéo (éditorial et masters), les outils.
- Vidéo ORPM : Google Drive de l'utilisateur (fichier `1CJ4UXh8CSWY6Lk8LFwhjgWA5sMnsODpk`), vérifiable par son SHA-256.
- Points ouverts : 5 vidéos YouTube à fournir ; hébergement à choisir. Les cinq personnages de La Grande Traversée relèvent de la candidate qui finalise la plateforme.
