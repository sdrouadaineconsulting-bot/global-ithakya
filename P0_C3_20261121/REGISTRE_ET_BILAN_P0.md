# ITHAKYA W360 — P0 du 21/11/2026 : registre des points, réserves et bilan des tests

**Mode : clôture conservatoire. La campagne n'est pas terminée.**

Aucune homologation n'est déclarée. Les verdicts ci-dessous ne valent que pour un banc local : PHP 8.3.6 en serveur intégré, SQLite et MariaDB 10.11.14, Chromium piloté par Playwright, mires synthétiques. Aucun appareil physique, aucune infrastructure OVH, aucune version MariaDB 11.8.

Statuts : **CONFORME PROUVÉ** · **CORRIGÉ ET RETESTÉ** · **NON EXÉCUTÉ** · **BLOQUÉ (motivé)** · **À CONFIRMER**.

## 1. Pièces et intégrité

| Pièce | Empreinte et contrôle | Statut |
|---|---|---|
| C2 (4 volumes) | SHA-256 `279660f0…9411`, conforme ; 4 118 fichiers conformes à `MANIFESTE_C2_SHA256.txt` | CONFORME PROUVÉ |
| Dossier de qualification C2 | SHA-256 `869a2665…247b` ; 197/197 empreintes `SHA256SUMS` conformes | CONFORME PROUVÉ |
| Delta C2 vs référence du 18/11 (dossier) | 35/35 empreintes avant/après cohérentes ; texte visible identique sur les 20 pages HTML du delta | CONFORME PROUVÉ (dans la limite du delta) |
| **C3** | `ITHAKYA_W360_CANDIDATE_C3_20261121.zip` : SHA-256 **`c573b5e86b9f44fb0064de902d5c18777bbcef4323786477bcd5401496f139d3`**, 4 118 fichiers, 100 460 459 octets, `unzip -t` sans erreur. Archive hors Git (taille > 100 Mo) ; elle se reconstitue depuis C2 et `delta/` (voir `LISEZ_MOI.md`) | Produite |
| Référence du 18/11 (`…V1_FINALE_STABILISEE_20261118.zip`) | Non reçue. Annoncée dans un autre fil Claude Code ; non récupérée (pas d'accès immédiat, sauvegarde prioritaire) | Pièce manquante |
| Captures C2 (`ITHAKYA_W360_C2_CAPTURES_20261121`) | part01 seul reçu (98 PNG valides sur 148) | Pièce manquante |
| Archive Work F09 (lots L6 à L10) | Non reçue ; seules les empreintes existent (`delta_base_f08_f09.json`) | Pièce manquante |

## 2. Delta C2 → C3 : 42 fichiers

Le détail figure dans `delta/DELTA_C2_C3.json`. Aucun fichier n'est ajouté ni retiré.

**Retour arrière :** aller-retour prouvé dans les deux sens, 4 118/4 118 empreintes identiques (`preuves/RETOUR_ARRIERE_C3_TEST.txt`).

**Intégrité des contenus :**

- 37/37 pages ont un texte visible identique.
- 37/37 pages sont identiques une fois les `?sha=` retirés.
- 0 média, 0 donnée JSON et 0 fichier PHP modifiés.

**Générateur :**

- Deux générations successives sont identiques au fichier près.
- `--verifier` compare 315 fichiers : 0 écart.

## 3. Registre des points

| ID | Source | Point | Décision et action | Fichiers | Preuve | Statut |
|---|---|---|---|---|---|---|
| P-V1 | P0 §3, add. rect. §2, add. final §1 | Question V1 à 65 % du Long | Mesure avec média : la question **interrompt** le film (pause maintenue, voile opaque à 82 % sur 100 % du lecteur, reprise sur action seulement). Déclenchement déplacé à la fin effective du Long, sans condition et sans obligation de répondre. Énoncé, réponses, libellés, transmission et crédits inchangés | `ithakya-v1-interaction.js` (site et source) | `preuves/v1/` : C2 en pause à 39,3 s ; C3 s'ouvre à 60 s ; 85 XP / 42 Points identiques sur C2 et C3 (parcours réel par l'interface, 390 px) ; défilement dy = 0 | **CORRIGÉ ET RETESTÉ** (390 et 1 440 px, Chromium ; appareils réels non testés) |
| P-L9 | Lot Work L9, C-06, add. rect. §4 | « Garder cette découverte » | Placé après « Explorer une autre œuvre » ; libellé inchangé ; aucun CTA ajouté | `ithakya-v9962-carnet.js` (site et source) | `preuves/l9/` : ordre C3 = Long → Explorer → Garder → Vérifier → Ça me suffit ; position du Long et `scrollY` identiques | **CORRIGÉ ET RETESTÉ** (390 px, Chromium) |
| P-N01 | Constat nouveau | Avec films présents, la tête de fiche affiche « Vidéo indisponible » (faux) | Mention retirée seulement si Court et Long sont présents. Aucun effet sur C2/C3 livrées sans film | `generer.py` | Banc avec mires : 4/4 fiches avant (mention présente), 0/4 après | **CORRIGÉ ET RETESTÉ** (génération) ; rendu visuel non recapturé |
| P-CACHE | Consigne utilisateur | Scripts JS conservés en cache | Version `?sha=` calculée sur le contenu pour chaque `<script src>` local. C2 présentait **162 références périmées** sur 17 scripts (dont `ithakya-memoire.js`, porteur de X03) et des scripts sans version (dont `ithakya-v1-interaction.js`) | `generer.py`, 37 pages | `outils/sha_refs.py` : C2 = 621 correctes, 162 périmées, 983 sans version ; C3 = 0 script sans version, 0 référence JS périmée | **CORRIGÉ ET RETESTÉ** (statique). Chargement en navigateur : partiel (captures C3 interrompues) |
| P-CSS | Constat nouveau | Versions CSS | `ithakya-composition-360.css` reste en `?sha=` périmé (70 références) ; 47 feuilles sans version | — | `sha_refs.py` | **RÉSERVE ouverte** (hors périmètre JS demandé) |
| L6, L10 | Lots Work, add. GO §2, rect. §3 | Grande Traversée en œuvre unique | Œuvre unique absente (aucun média, droits non acquis, 7 options à l'étude). Le lot réécrit des contenus gelés (« trois histoires à relier » sur 34 pages, catalogue, Lounge, mentions). Archive F09 non reçue | — | Registre `REGISTRE_CONVERGENCE_LOTS.csv` | **BLOQUÉ (motivé)** |
| L8 | Lot Work, C-04, rect. §4 | « Voir le Court » en tête de fiche | Le lien vers le Court est sous la flottaison (1 447 px à 390 px). L'appliquer imposerait de réécrire le libellé de tête ou d'ajouter un CTA, ce que l'additif interdit | — | Mesure de la fiche (banc C2 avec mires) | **À CONFIRMER** (position et libellé) |
| D-06, D-07 | Section 9 du document maître | Bouton du Long hors écran ; Long hors écran | Infirmés par le dossier C2 ; non rouverts (pas de nouvelle preuve) | — | Dossier C2 | CONFORME (preuve historique réutilisée) |
| D-08 | Section 9 du document maître | Générateur non reproductible | `--verifier` : 0 écart (C2 et C3) | — | `gen` | **CONFORME PROUVÉ** |
| D-09 | Section 9 du document maître | Compteur « — explorateurs » | Masqué hors Traversée (8/8). En mode `?traversee=regards`, la ligne n'est pas masquée (`hidden=false`) mais n'apparaît pas au chargement | — | Mesure Chromium | Partiel. **Résidu à vérifier** en mode Traversée en déroulant le parcours |
| F10-B | Dossier C2 §6, P0 §9.3 | Crédits sans visionnage humain | SQLite et MariaDB : 13 cas conformes (forgé, accéléré ×4, rejeu, vol de témoin, concurrence, quiz sans lecture, session révoquée, CSRF, owner_id). **T9 : un automate sans affichage, au rythme réel, avec des images calculées depuis le fichier servi, obtient le crédit (+5 XP).** Chaque témoin forgé reçoit 200 ; le refus intervient à la décision de crédit | — | `preuves/f10b_sqlite.json`, `preuves/f10b_mariadb.json` | **RÉSERVE MAINTENUE.** La limite est démontrée (le dossier la supposait seulement). Impact borné : `economic_eligible=false`, économie fermée (mode A) |
| MDB-1 | P0 §4 | Concurrence des crédits sur MariaDB 10.11.14 | 10 comptes en parallèle (8 processus PHP) : 10 crédits exacts. Rafale de 30 appels sur un même compte : aucun double crédit. 0 deadlock, 0 attente de verrou | — | `preuves/mariadb/CONCURRENCE_10_COMPTES_8WORKERS.json` | **CONFORME PROUVÉ** (10.11.14 seulement) |
| MDB-2 | P0 §4 | Arrêt brutal et redémarrage | `kill -9`, récupération InnoDB, données identiques, `CHECK TABLE` OK, API 200 | — | Journal de session | **CONFORME PROUVÉ** (10.11.14) |
| MDB-3 | P0 §4, §9.5 | Migrations, idempotence, retours | 7 migrations documentées : rc=0 (13 → 32 tables InnoDB) ; 4 rejouées : rc=0 ; 3 retours : rc=0. Les migrations cadeaux L15/L16 ne sont pas appliquées (décision du propriétaire requise) | — | `preuves/mariadb/MIGRATIONS_10_11.txt` | **CONFORME PROUVÉ** (10.11.14) |
| MDB-4 | P0 §12 | MariaDB 11.8 (`compose.yaml`) et version OVH | Non testées | — | — | **NON EXÉCUTÉ** |
| PHP-1 | P0 §4 | Compatibilité PHP | `php -l` sur 35 fichiers en PHP 8.3.6 : 0 erreur. PHP 8.2, la version OVH réelle, php-fpm et HTTPS ne sont pas testés | — | `preuves/mariadb/PHP_LINT.txt` | Partiel |
| STAB-C2 | P0 §11, §14 | Stabilité sur C2 (148 cas) | 0 mouvement au chargement, 0 mouvement sans action, en-tête stable, 0 débordement, 0 erreur JS, CLS ≤ 0,0006. Restauration décalée de 7 à 70 px sur Atlas et Missions en paysage (**N-02**, préexistant). 4 cas `cest-quoi` relèvent d'un artefact du protocole. **Le test du menu n'a pas été exercé (0/148, sélecteur erroné)** | — | `preuves/stabilite/STAB_C2_visiteur.json` | Partiel |
| STAB-C3 | P0 §11, §14 | Stabilité sur C3 | Campagne interrompue (clôture conservatoire) | — | — | **NON EXÉCUTÉ** |
| VIS | Add. final §2 | Recette graphique des 37 pages | C2 : 116/148 captures (partiel) ; C3 : 0. Comparaison C3 / référence du 18/11 impossible (référence non reçue) | — | `preuves/captures_C2_partiel/` | **NON EXÉCUTÉ** |
| CL | P0 §3 | Court → Long avec films présents, C3 | Seul le parcours réel 01-signature à 390 px a été exécuté (C2 et C3 identiques sur ce cas). La matrice 4 pages × 3 vues n'a pas été rejouée | — | `preuves/v1/PARCOURS_*` | Partiel |
| 27 scénarios | Dossier C2 | T01 à T27 | Non rejoués sur C3. Le code serveur PHP est identique entre C2 et C3 ; seuls trois points navigateur changent (V1, L9, versionnement) | — | Dossier C2 | Hérités de C2 : 13 conformes, 3 partiels, 6 repris de Work, **5 non exécutés** |
| E2 | Journal | Captures part02 et suivants | Pièces non reçues | — | — | Ouvert |

## 4. Restant à réaliser, explicitement non exécuté

1. **Stabilité C3, 37 pages × 4 vues** : chargement, menu « Découvrir / Participer » (balises `<summary>`), immobilité, rechargement, retour, orientation. Comparer à C2, mouvements JS compris.
2. **Recette graphique C3 face à la référence du 18/11** : pages, bandeaux, pieds de page, CTA, composants IA, aux mêmes dimensions et états. À reprendre :
   - captures C2 (complétées) et C3 ;
   - fiches avec films présents (effet de N-01 sur la mise en page) ;
   - V1 en fin de Long ;
   - panneau de fin du Court (L9).
3. **Court → Long sur C3** : 4 pages × 3 vues avec l'outil du dossier (`recette_transition.cjs`), et chargement effectif des scripts versionnés (aucun 404).
4. **Jonctions transversales** : visiteur vers membre, reconnexion, deux onglets, coupure réseau, ancien cache JS, Grande Traversée (D-09 en mode Traversée), Missions, Communauté, Lounge.
5. **Appareils physiques** : iPhone/Safari (HLS, plein écran natif), Android, BFCache réel.
6. **Environnements** : MariaDB 11.8, version MariaDB/PHP réelle de l'offre OVH, php-fpm, HTTPS.

## 5. Verdict provisoire, pilote privé OVH

**NON PRONONCÉ. Qualification incomplète.**

- Rien de ce qui a été exécuté ne montre de régression de C3 face à C2.
- Les corrections V1, L9, N-01 et du cache sont prouvées sur le banc.
- La stabilité C3, la recette graphique et la qualification OVH ne sont pas exécutées.
- F10-B reste une réserve. Elle est non bloquante pour un pilote sans économie réelle ; cette appréciation reste à arbitrer.

Un GO, même sous réserves, demande au minimum les points 1 à 3 de la section 4.
