# ITHAKYA Premium W360 — S42 — Rapport de contre-recette indépendante ATTENZIA
28 novembre 2026 — Référence d'entrée : S41 (candidate non gelée) — Sortie : S42 (ATTENZIA V3.7)

Conventions : **[PREUVE]** = résultat exécuté et reproductible (fichier cité). **[INDICE]** = constat d'analyse non démontré par exécution. **[NON VÉRIFIABLE]** = pièce absente.

## 1. Référence exclusive S41

| Contrôle | Résultat | Statut |
|---|---|---|
| Reconstitution des 6 parties (`ITHAKYA_S41.zip.part01…06`, 6 × 16 766 757 octets) | 100 600 542 octets | [PREUVE] conforme |
| SHA-256 | `01149a30e156f57fd556174ea86d461cb942e40161a87b00c4f1e0bb18be08c4` | [PREUVE] = attendu |
| CRC (`unzip -t`) | aucune erreur | [PREUVE] |
| Inventaire | 4 135 fichiers ; 4 135 empreintes identiques à `MANIFESTE_S41.json` (`inventaire_final`) | [PREUVE] 0 écart |
| Préservation | parties et archive S41 conservées en lecture seule ; travail sur copies | [PREUVE] |

Limite : le manifeste et l'archive proviennent de la même source. La concordance prouve l'intégrité du transfert, pas l'exactitude du contenu.

## 2. Différentiel S40 → S41

- Le correctif `attenzia_v3_6.patch` (dossier probatoire S41) s'applique en sens inverse sans conflit sur le module V3.6. V3.5 reconstituée : SHA-256 `d63d5f1e58df5abaeb21978a71482104593109d70978513f81f925b4b11a9b65`. [PREUVE]
- `source/serveur/…instantanes.php` et `site/api/…instantanes.php` sont identiques (V3.6 `33313dc9…6499`). Le générateur (`source/outils/generer.py`, l. 974-975) copie `source/serveur/*.php` vers `site/api/` sans transformation, et les 14 fichiers serveur ainsi que le cockpit sont identiques à leur source. [PREUVE]
- **[NON VÉRIFIABLE]** L'archive S40 (`b22621693ed6…d204`) n'a pas été transmise. Les affirmations « S41 = S40 sauf 2 chemins » et « V3.5 reconstituée = V3.5 de S40 » ne peuvent être confrontées à S40 par une source indépendante.

## 3. Contre-expertise du correctif V3.6

### 3.1 Rejeu des campagnes déclarées

| Campagne | V3.5 | V3.6 | V3.7 (S42) | Concordance avec le déclaré |
|---|---|---|---|---|
| `test_historique_267.php` | 267/267 | 267/267 | 267/267 | identique octet pour octet à `non_regression_267.json` |
| `test_complements.php` | 0 nouvelle (garde V3.6 inactif) | 10 750/10 750 | 10 750/10 750 ¹ | JSON V3.5 et V3.6 identiques aux résultats déclarés (`jq -S`) |

¹ Le script ne déroule ses assertions que si la règle vaut exactement `ATZ-INSTANTANES-V3.6`. Pour V3.7, une copie déclarée ne modifie que cette condition (`outils/test_complements_v37.php`, différence d'une ligne). Les 9 cas nommés donnent des résultats identiques sous V3.6 et V3.7.

### 3.2 Pertinence, indépendance et couverture réelle des assertions

- **267** = grille de 8 × 16 valeurs de `participants`, soit 128 points × 2 assertions (dont une sur une cellule témoin), plus 11 cas. Ces assertions ne testent qu'un seul indicateur. [PREUVE : décompte]
- **10 750** = 10 assertions ciblées et 2 × 5 370 points d'un balayage qui porte sur **une seule relation** (`participants/long_ouverts`), avec des écarts de 5 à 9. [PREUVE : décompte recalculé]
- Les deux scripts appellent `itpAtzMasquerRecoupements` **isolément**, sur des cellules écrites à la main. Ils n'exercent ni `itpAtzCalculer`, ni la publication primaire (`$pub`), ni les taux, ni la base, ni HTTP. Ils sont écrits par l'auteur du correctif. Le volume de 10 750 assertions ne mesure donc pas une couverture des risques.

### 3.3 Essais adverses indépendants (banc HTTP réel, données SQL simulées déclarées)

Banc : Apache 2.4.58 (prefork, HTTPS 127.0.0.1:8443), mod_php 8.3.6, MariaDB 10.11.14, k = 5. Les faits de progression sont insérés en SQL pour des périodes closes (simulation déclarée). Calcul, garde, persistance et lecture passent par l'API réelle.

| Id | Hypothèse adverse | V3.6 (S41) | V3.7 (S42) |
|---|---|---|---|
| RT-01 | `taux_achevement_long` restitue `long_ouverts` masqué | **FUITE** : 10 / 0,556 → 18 ; complément 20 − 18 = **2 < k** | aucune (taux masqué) |
| RT-02 | `taux_approfondissement` restitue `court_termines` masqué | **FUITE** : complément **2** | aucune |
| RT-03 | `taux_quiz_correct` restitue `quiz_repondus` masqué (cumul) | **FUITE** : complément **2** | aucune |
| RT-13 | RT-01 en **régime d'exploitation privée** (`environment=production`, HTTPS, administrateur nommé) | **FUITE** : complément **2** | aucune |
| RT-14 | Attaquant automatisé, 55 instantanés aléatoires (graine 4242), 715 cellules | **84 cellules en fuite (99 fuites)** | **0** |
| RT-04 | Complément nul `long_ouverts − long_apres_court` = 0 (homogénéité) | publié | publié (inchangé, voir réserve R-ATZ-03) |
| RT-05 | Parcours (banc) : `long_lances − long_termines` = 1 | publié | publié (banc seulement ; masqué en exploitation, RT-13) |
| RT-06 | Export conservé → purge → refigement de la même période après suppression d'un compte | Δ participants = **1** | Δ = **1** (inchangé, voir R-ATZ-01) |
| RT-07 | Utilité : semaine recoupée par un cumul existant | 25 → **0** valeur publiée | identique |
| RT-08 | Concurrence : même instantané × 10 ; deux cumuls trop proches en parallèle ; 5 semaines en parallèle ; 5 exports simultanés | 1 × 201 + 9 × 409 ; 201 + 409 ; 5 × 201 ; exports identiques | identique |
| RT-09 | Rôles : membre et anonyme sur les 6 actions ; filtre libre ; cockpit | 403 partout ; 422 ; cockpit 404/404/200 (membre, anonyme, administrateur) | identique |
| RT-10 | Instantané altéré en base | lecture 500, export 500, nouvelle publication recoupée 500 (blocage par défaut) | identique |
| RT-11 | Instantané figé sous V3.5, lu, exporté, comparé et recoupé sous la version courante | 200, contenu et empreinte inchangés, 201 | identique |
| RT-12 | Cohérence export CSV ↔ JSON | 102/102, 0 écart | identique |
| RT-13 | Exploitation : administrateur non nommé, changement de niveau, échéance dépassée, k < 5, banc hors local | 403, 409, 403, 403, 403 | identique |

Preuves : `preuves/res_v36_*.json`, `preuves/res_v37_*.json` ; outils : `outils/`.

**Anomalie matérielle démontrée (A-01).** La publication primaire publie un taux lorsque ses termes atteignent k, même si l'un d'eux est masqué par la suppression complémentaire. Le taux, multiplié ou divisé par le terme publié, restitue alors l'effectif masqué et son complément inférieur à k. Ce comportement contredit l'invariant écrit dans le module (« Un ratio ou une distribution ne doit pas servir de substitut à un effectif masqué ») et l'affirmation du rapport S41 selon laquelle le masque intégral évite les ratios de substitution. La cause est antérieure à V3.6 : elle se trouve dans `$pub`, qui n'est pas modifié par V3.6. Le défaut est présent en régime d'exploitation.

### 3.4 Correctif S42 (V3.7) — minimal et localisé

`attenzia_v3_7.diff` : ajout de 4 lignes dans `$pub`, plus l'identifiant de règle `ATZ-INSTANTANES-V3.7`, dans les deux fichiers identiques `source/serveur/` et `site/api/`. Un taux n'est publié que si son numérateur **et** son dénominateur sont eux-mêmes publiés. Rien d'autre n'est modifié : ni le garde V3.6, ni le schéma, ni les instantanés existants, ni le moteur direct (banc).

Écarté après essai : inclure le complément nul dans le garde (homogénéité). Cette option masque des cellules entières dans un cas d'usage normal (tous les Longs ouverts après le Court), ce qui relève d'un arbitrage entre confidentialité et utilité. Elle est consignée en réserve R-ATZ-03.

SHA-256 V3.7 : `51a4e6bbfe507d965e5d632dfa2847e23fe4ca1fe5abd659866a76c958664e85`.

### 3.5 Utilité statistique

- Sur le même jeu aléatoire : **1 132** valeurs scalaires publiées sous V3.6, **1 029** sous V3.7, soit −9,1 %. Les 103 valeurs retirées sont des taux dont un terme était masqué. [PREUVE RT-14]
- Masquage intersérie (antérieur à V3.6) : une semaine recoupée par un cumul existant est intégralement masquée (25 → 0). [PREUVE RT-07]
- V3.6 masque des cellules entières dès qu'un complément dérivé ou sa variation est inférieur au seuil effectif (cas « deuxième publication », dossier S41).

### 3.6 Constats d'analyse non démontrés [INDICE]

- `note_k_moyenne` et `idees_choisies` peuvent être publiés alors que `notes_k_donnees` ou la somme des réponses sont masqués. Aucune restitution unique d'effectif n'a été établie (les solutions entières sont multiples en général). Ce point n'est pas démontré.
- Croisements entre cellules d'une même dimension en exploitation : le catalogue courant ne contient aucun territoire inclus dans un autre, donc aucune différence de cellules ne fournit un effectif. Cela dépend des futures œuvres.
- Signal porté par le masque : une cellule intégralement masquée indique qu'une variation inférieure au seuil a eu lieu, sans en donner la valeur. Ce point n'est pas quantifié.
- Le chemin SQLite crée les instantanés sans verrou. Il ne concerne que le banc.

**Aucun résultat ci-dessus ne constitue une preuve de confidentialité absolue.** Le mécanisme reste un k-anonymat avec suppression complémentaire et contrôle des fenêtres recoupées, sans garantie formelle (pas de confidentialité différentielle).

## 4. Contre-recette intégrée (Apache / PHP / MariaDB)

Le banc est décrit au § 3.3. Instantanés historiques (RT-11), exports simultanés (RT-08), transactions concurrentes (RT-08 : `GET_LOCK` puis `REPEATABLE READ`, aucun doublon ; créations suivantes acceptées, donc aucun blocage résiduel constaté ; l'état des verrous nommés n'a pas été interrogé directement), isolation des comptes et des rôles (RT-09, RT-13), seuils (RT-01 à RT-05, RT-13), cohérence de l'export avec les données (RT-12), conservation des instantanés figés antérieurement (RT-11 : empreinte inchangée) et compatibilité des anciennes sorties (RT-11).

Cockpit : contrôle par lecture du code (`assets/ithakya-atz-cockpit.js`). Les valeurs affichées sont celles servies par l'API, sans calcul dérivé, et la règle affichée provient de l'instantané. **Non rejoué en navigateur.**

Écart de représentativité : MariaDB **10.11.14** sur le banc, alors que `compose.yaml` déclare `mariadb:11.8`. La version MariaDB et la configuration PHP d'OVH n'ont pas été contrôlées (limitation externe).

## 5. Non-régression S41 → S42

`MANIFESTE_S42.json` : 4 135 fichiers ; **2 modifiés** (les deux copies du module, identiques entre elles), 0 ajouté, 0 supprimé. Aucun autre fichier du patrimoine technologique, graphique, fonctionnel ou éditorial n'est modifié. [PREUVE] Les campagnes générales déjà démontrées n'ont pas été rejouées (consigne 4).

## 6. Résistance en charge

Voir `preuves/res_v37_charge_200_1800s.json` et la section correspondante du PV. Le banc local, client compris, tourne sur une seule machine de 4 vCPU. Ses mesures ne sont pas transposables à l'hébergement OVH.

## 7. Limites de la contre-recette

Données synthétiques uniquement ; aucune base de production ni aucun export réel. L'archive S40, les documents S36 à S40, le registre des réserves postérieur au 27/11 et la matrice des 128 articles n'ont pas été transmis (§ 8 du PV). Firefox, WebKit et les appareils réels sont hors champ.
