# ITHAKYA Premium W360 — dossier de clôture et gel de la candidate C3.2 (21/11/2026)

## Verdict : **B — GEL SOUS RÉSERVES DOCUMENTÉES**

Les quatre conditions du gel local sont réunies :
- intégrité de C3.2 conforme ;
- contenus préservés ;
- comparaison visuelle C2/C3 close ;
- aucune régression bloquante dans le périmètre vérifié.

Le gel n'est pas qualifié « A — validé » parce que des vérifications restent ouvertes (section 8) :
- appareils physiques ;
- hébergement OVH ;
- comparaison avec la référence du 18/11, non reçue ;
- réserve F10-B, maintenue.

Aucune homologation de production n'est déclarée.

| Domaine | Statut |
|---|---|
| Gel technique C3.2 | **Sous réserves** |
| Intégrité des contenus | **Conforme** |
| MariaDB 11.8 | **Validé** (11.8.10, local isolé ; voir `RAPPORT_MARIADB_11_8.md`) |
| Appareils physiques | **Non testés** |
| OVH | **Non testé** |

## 1. Identification

| Élément | Valeur |
|---|---|
| Candidate | `ITHAKYA_W360_CANDIDATE_C3_2_20261121.zip` — 4 118 fichiers |
| SHA-256 | **`56a153cd2c758d2dcdca7d5021d30a6160002b90c8e7d99d287c8e3b1bef1607`** |
| Volumes | `../C3_2_D09T_N02/archive/ITHAKYA_W360_C3_2_20261121.part00` à `.part02` (33 486 927 / 33 486 926 / 33 486 926 octets) |
| Branche | `claude/new-session-q55sxl` ; étiquette Git `ithakya-c3.2-gel-20261121` (voir le message de commit) |
| Base | C3 (`c573b5e8…39d3`), issue de C2 (`279660f0…9411`) |
| Exclus | Le correctif F10B-1 n'est **pas** intégré (section 9) |

## 2. Manifeste et contrôle d'intégrité, refaits pour la clôture

- **Reconstitution** : les 3 volumes concaténés donnent `56a153cd…1607`, identique à l'empreinte attendue. Chaque volume est conforme à `RECONSTITUTION_C3_2.txt`.
- **Archive** : `unzip -t` sans erreur ; 4 118 fichiers extraits.
- **Manifeste** : `../C3_2_D09T_N02/MANIFESTE_C3_2_SHA256.txt`, 4 118/4 118 empreintes conformes sur l'archive reconstituée.
- **Corrections présentes** :
  - D-09-T : masquage du compteur placé avant le retour du mode Traversée ;
  - N-02 : règles critiques `.pil-etapes` présentes dans `site/exploration/missions.html` ;
  - V1 : déclenchement en fin de Long, aucune occurrence du déclenchement à 65 % ;
  - F10B-1 absent (`credit_rate` : 0 occurrence).
- **`ithakya-position-l19.js`** : identique à C3 (et à C2), dans le site comme dans les sources.

Aucune archive n'a été modifiée pendant la clôture.

## 3. Delta C3 → C3.2 : 9 fichiers

Le delta est détaillé dans `../C3_2_D09T_N02/delta/` (avant/après et script de retour).

| Fichiers | Correction |
|---|---|
| `ithakya-w360-media-availability.js` (site et tête validée), 4 pages de lecture (nouvelle empreinte `?sha=` seulement) | D-09-T |
| `source/w360_tete_validee/exploration/missions.html`, `site/exploration/missions.html`, `site/assets/data/recherche-pages.json` (`source_sha256` seulement) | N-02 |

Le delta C2 → C3 (42 fichiers : V1, L9, N-01, versionnement du cache) est dans `../delta/`. Ses allers-retours ont été testés.

## 4. Comparaison visuelle C2 / C3 (148 paires) : close

**Protocole** :
- captures `captures.cjs` aux mêmes dimensions et états : 390×844, 768×1024, 1440×900 et 844×390 en paysage ;
- page chargée puis stabilisée 1,5 s, visiteur, mires présentes ;
- comparaison `diff_pixels.py` (écart si une composante varie de plus de 16 niveaux).

**Résultat** : 132 paires identiques au pixel, 16 différentes.

| Écart | Paires | Qualification | Preuve |
|---|---|---|---|
| Fiches œuvre (pop, progression, signature, soleil) × 4 tailles | 16 | **Évolution attendue et documentée (N-01)**. La mention fausse « Vidéo indisponible » disparaît quand le film est présent, et le contenu situé dessous remonte (5 à 79 px selon la taille). Les pixels résiduels après translation viennent d'éléments fixes (barre de navigation mobile) et de l'image d'en-tête recentrée. Contrôle visuel côte à côte à 390 et 1 440 px : aucune autre différence | `visuel/DIFF_PIXELS_C2_C3.json`, `visuel/TRANSLATION_N01.json`, `visuel/COTE_A_COTE_*.png`, `visuel/paires_differentes/`, `visuel/diff/` |
| Variation dynamique naturelle | 0 sur ces captures | Une zone dynamique existe sur Missions en pleine page ; elle est documentée dans `../C3_2_D09T_N02/preuves/n02_pixels/` | — |
| Artefact du banc | 0 sur ces captures | L'émulation tactile fausse la restauration de position en paysage (N-02, démontré) ; sans effet sur ces captures stabilisées | `../C3_2_D09T_N02/LISEZ_MOI.md` |
| **Régression visuelle effective** | **0** | — | — |

**Chargement des scripts**, C3, 148 cas : 2 414 scripts chargés, 0 sans version, 0 erreur HTTP, 0 erreur JS (`visuel/CAPTURES_C3.json`).

**Limites** :
- C3.2 diffère de C3 sur les 4 pages de lecture (script de compteur) et sur Missions (copie critique). Ces pages ont été contrôlées par les tests ciblés de la section 5. Leurs captures pleine page de C3.2 ne sont pas reprises dans les 148 paires.
- La comparaison avec la référence du 18/11 n'a **pas été faite** : la pièce n'a pas été reçue.

## 5. Non-régression, rattachée à la version exacte

| Périmètre | Résultat | Version testée | Rattachement à C3.2 |
|---|---|---|---|
| Court → Long, 4 pages × 3 tailles (outil du dossier C2) | **12/12** (Long à l'écran et en lecture, 0 erreur) | C3 | Hérité. Le code de transition est inchangé entre C3 et C3.2 : seul le bloc du compteur est déplacé. Le passage Court → Long a aussi été rejoué 12 fois avec succès dans la matrice V1 sur C3.1 |
| Question V1, 4 pages × 3 tailles, parcours réel | **12/12** (ouverture à 60 s, dy = 0, aucun défilement programmé ; 85 XP / 42 Points, ou 90 / 44 avec un quiz juste) | C3.1 | Le code V1 et les pages de lecture sont identiques entre C3.1 et C3.2 |
| V1 et crédits, parcours complet | 85 XP / 42 Points | **C3.2** (banc MariaDB 11.8) | Direct |
| Stabilité, 37 pages × 4 tailles | 0 mouvement au chargement, 0 mouvement sans action, en-tête stable, CLS ≤ 0,0006, 0 erreur JS | C3 | Hérité pour les 32 pages que C3.2 ne modifie pas |
| Menus | **288** ouvertures et fermetures, sans déplacement | C3 | Hérité (en-tête inchangé) |
| Atlas et Missions, N-02 | Restauration exacte en un seul déplacement, 3 essais sur 3 (sans émulation) | C3.1 + N-02, contenu identique à C3.2 | Direct pour les pages concernées |
| Compteur social D-09 et D-09-T | Masqué dans 4 cas sur 4 (visiteur et membre, standard et Traversée) | C3.1 | Code identique à C3.2 |
| Générateur | `--verifier` : 315 fichiers, **0 écart** ; régénération reproductible | **C3.2** | Direct |
| L19 | Identique à C3 | **C3.2** | Direct |
| Antifraude, concurrence, migrations | Voir le rapport MariaDB 11.8 | **C3.2** | Direct |

## 6. MariaDB 11.8

Statut : **Validé (11.8.10, local isolé)**. Voir `RAPPORT_MARIADB_11_8.md`.

Les mêmes scénarios avaient donné les mêmes résultats sur MariaDB 10.11.14.

## 7. Intégrité des contenus : **Conforme**

Fichiers : `CONTENUS_C3_C32.json`, `CONTENUS_C2_C32.json`, outil `controle_contenus.py`.

- **Fichiers** : 4 118 de part et d'autre ; aucun ajout, aucun retrait.
- **Médias** : les 875 fichiers médias (vidéos, images, sous-titres, polices, dans `site/`, `source/` et les dossiers documentaires) ont une empreinte **identique**.
- **Pages HTML** : texte visible et attributs textuels identiques sur **38/38** pages modifiées entre C2 et C3.2 (6/6 entre C3 et C3.2).
- **Scripts** : sur les 6 modifiés, **aucune** chaîne de texte d'interface ajoutée ou retirée.
- **Données** : seul `recherche-pages.json` change, uniquement par `source_sha256`.
- **Autre** : `source/outils/generer.py` (outil de génération).
- **Qualification** : toutes les différences sont exclusivement techniques et tracées (sections 3 et 4).

## 8. Réserves résiduelles

| Réserve | Bloquante pour le gel local | Bloquante pour la production |
|---|---|---|
| Appareils physiques (Safari iOS, Android, plein écran natif, BFCache réel) : non testés. Les résultats sont des émulations Chromium/Playwright | Non | **Oui**, avant le pilote |
| OVH (versions réelles, droits SQL, php-fpm, HTTPS, déploiement et retour arrière) : non testé, aucun accès | Non | **Oui** |
| Référence graphique du 18/11 : non reçue ; comparaison historique non faite | Non | À arbitrer |
| F10-B : lecture automatisée créditable (limite démontrée) ; économie réelle fermée | Non | Non, tant que l'économie reste fermée (F10B-1 disponible) |
| Cache CSS : `ithakya-composition-360.css` porte une version périmée depuis avant le 18/11 ; sans effet pour un nouveau domaine | Non | Non |
| L6/L10 Grande Traversée en œuvre unique : bloqué (œuvre absente, contenus gelés, F09 non transmise) | Non | Arbitrage éditorial |
| L8 « Voir le Court » en tête de fiche : à confirmer | Non | Arbitrage |
| Migrations cadeaux L15/L16 : non appliquées (décision du propriétaire) | Non | Selon la décision |

## 9. F10B-1 : séparé, inchangé, non activé

**Emplacement** : `../F10B_patch/` (delta de 4 fichiers serveur, manifeste, preuves MariaDB 10.11.14, notice).

**Mécanisme** : au-delà de `credit_rate_max_hour` crédits de lecture confirmés par compte et par heure, le crédit suivant passe en revue (`pending`).
- Défaut : 12. La valeur 0 désactive le plafond.
- Clé privée dans `config.php`, donc seuil modifiable sans changer le code.

**Faux positifs** : un lecteur très assidu voit ses crédits suivants mis en attente, sans perte, jusqu'à une décision de l'administration.

Il n'est ni intégré, ni activé, et **attend l'arbitrage du seuil**.

## 10. Reprise et retour arrière

- **Reconstituer C3.2** : `cat ITHAKYA_W360_C3_2_20261121.part00 .part01 .part02 > ITHAKYA_W360_CANDIDATE_C3_2_20261121.zip`, puis `sha256sum`, puis `unzip`, puis `sha256sum -c MANIFESTE_C3_2_SHA256.txt`.
- **Autres voies** :
  - C2 → C3 : `../delta/RETOUR_ARRIERE_C3.py <dossier> vers-c3` ;
  - C3 → C3.2 : `../C3_2_D09T_N02/delta/RETOUR_ARRIERE_C32.py <dossier> vers-c3`.

  Le libellé « vers-c3 » est générique : il applique l'état « après ».
- **Retour C3.2 → C3** : même script, sens `vers-c2`, qui applique l'état « avant ». **Testé dans les deux sens pendant la clôture** : C3 → C3.2 puis C3.2 → C3, 4 118/4 118 empreintes conformes à chaque étape (`RETOUR_ARRIERE_C3_C32_TEST.txt`). Également testé pour C2 ↔ C3 et C3 ↔ C3+F10B.
- **Déploiement**, selon `docs_v1/GUIDE_INSTALLATION_OVH_V1.md` :
  - seul `site/` va à la racine web ;
  - `config.php` et `prive/` restent hors de la racine web ;
  - migrations dans l'ordre documenté, après une sauvegarde logique.

## 11. Après le gel

C3.2 n'est plus modifiable. Toute évolution, y compris l'intégration de F10B-1, se fera sur une nouvelle branche, avec un nouvel identifiant de candidate et un contrôle d'impact.
