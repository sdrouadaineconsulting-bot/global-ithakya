# Candidate C3.2 = C3 + D-09-T + N-02 (21/11/2026)

C3 reste intacte (SHA-256 `c573b5e8…39d3`). C3.2 n'intègre **pas** le correctif F10B-1 : il est livré à part dans `../F10B_patch/` et attend votre validation du seuil.

## Delta C3 → C3.2 : 9 fichiers

Le détail figure dans `delta/DELTA_C2_C3.json`, nom imposé par le script réutilisé : ici « avant » = C3 et « après » = C3.2.

| ID | Anomalie démontrée | Cause | Correctif | Fichiers |
|---|---|---|---|---|
| D-09-T | En mode Traversée (`?traversee=regards`), la ligne « — explorateurs ont déjà approfondi ce parcours » s'affiche à la fin du Court, pour un visiteur comme pour un membre | Le masquage du compteur vide était placé après `if (historique) return;` | Bloc de masquage déplacé avant ce retour ; aucun texte modifié | `ithakya-w360-media-availability.js` (tête validée et site), avec la nouvelle empreinte `?sha=` dans les 4 pages de lecture |
| N-02 | Missions et Atlas, 844 × 390 : restauration de position en plusieurs sauts | Voir l'analyse ci-dessous | Deux règles **existantes** (`.pil-etapes`, `.pil-etapes li`) recopiées à l'identique dans la copie CSS critique en ligne de la tête validée de Missions, à leur rang d'origine | `source/w360_tete_validee/exploration/missions.html`, `site/exploration/missions.html`, `recherche-pages.json` (empreinte de source seulement) |

## N-02 : analyse

1. **La dérive de +35 / +70 px mesurée en paysage était un artefact du banc.**
   - Sous l'émulation tactile de Playwright, la requête média `(pointer: coarse)` passe de vrai à faux entre `beforeunload` et `pagehide`.
   - Les règles de cible tactile sautent alors, la page raccourcit de 83 px, et L19 enregistre une position faussée.
   - Sans émulation, Atlas est restauré exactement.
   - Preuves : `preuves/n02/` (avec émulation) et `preuves/n02_sans_emulation_tactile/` ; outils `n02_unload.cjs` et `n02_cls.cjs`.
2. **Défaut réel, sans émulation : Missions oscille** (1 200 → 1 174 → 1 184 → 1 200).
   - La règle `.pil-etapes li` manquait dans la copie critique, parce que les cartes sont produites par script après la mesure.
   - Elle n'arrivait qu'avec la feuille différée `lot-7eb5c3815fcc.css`, et la liste grandissait de 26 px après la restauration.
   - Preuves : `n02_quelle_css.cjs` et `n02_regles.cjs`.
3. **Après correctif, 3 essais sur 3** : Atlas et Missions sont restaurés en **un seul déplacement, à la position exacte**, au rechargement comme au retour (`preuves/n02_corrige_1..3/`).
4. **Rendu final inchangé** : la seule différence de pixels entre C3.1 et C3.2 est la zone dynamique qui varie aussi entre deux captures d'une même version (`preuves/n02_pixels/`).
5. **Essais intermédiaires sur L19, tous écartés et annulés** : unicité du repère, attente des CSS différées, `scrollRestoration`. Ils n'avaient pas de bénéfice démontré ou reproductible. L19 est **identique à C3**.

## Contrôles

- **Générateur** : `--verifier` compare 315 fichiers, 0 écart. Régénération reproductible.
- **Contenus** : texte visible identique sur 6/6 pages. Aucun média modifié. `recherche-pages.json` ne change que par `source_sha256`.
- **D-09-T** : ligne masquée dans 4 cas sur 4 (visiteur et membre, mode standard et Traversée) (`preuves/D09_TRAVERSEE_C31.json`). Avant correctif, elle était affichée en Traversée (`D09_TRAVERSEE_C3.json`).
- **V1, parcours réel**, 4 pages × 3 tailles, sur C3.1 (code V1 identique dans C3.2) : 12 cas sur 12. V1 s'ouvre à la fin du Long, dy = 0, et aucun défilement n'est programmé. Crédits : 85 XP / 42 Points, ou 90 / 44 quand la réponse au quiz est juste (`preuves/v1_matrice_C31/`).
- **Stabilité Atlas / Missions**, 4 vues : menus 16 sur 16. Les écarts de position restants n'apparaissent que sous émulation tactile, l'artefact démontré au point 1 (`preuves/STAB_C32_missions_atlas.json`).

## Non exécuté pour C3.2

- Balayage complet des 37 pages × 4 vues : il a été fait sur C3, et C3.2 ne modifie que les 4 pages de lecture et Missions.
- Appareils physiques.
