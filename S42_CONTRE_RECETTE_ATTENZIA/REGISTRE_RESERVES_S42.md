# Registre des réserves — S42 (28/11/2026)

Base documentaire disponible : `QUALIFICATION_W360_ASSAINISSEMENT_20261126/REGISTRE_REPRISE.md` (état au 27/11, contenu dans S41), rapport S41, présente contre-recette. Les registres S36 à S40 n'ont pas été transmis.

Catégories : **TB** = réserve technologique bloquante · **IP** = insuffisance probatoire · **LE** = limitation externe · **NB** = réserve non bloquante pour le gel.

## A. ATTENZIA

| Id | Réserve | Catégorie | État S42 | Preuve | Levée |
|---|---|---|---|---|---|
| A-01 | Taux publiés alors qu'un terme est masqué → restitution d'un effectif masqué et d'un complément < k (V3.6 et antérieures, régime d'exploitation compris) | TB | **Corrigée (V3.7) et requalifiée** : 0 fuite sur RT-01/02/03/13/14 | res_v36_*, res_v37_* | — |
| R-ATZ-01 | Purge puis refigement d'une même période (ou d'un cumul proche) : le garde ne voit plus l'historique purgé ; un export conservé permet une différence de 1 (démontré : RT-06) | TB pour l'**activation sur données réelles** ; NB pour le gel du code (ATTENZIA désactivé par défaut) | Ouverte, non corrigée : la correction dépend de la politique de conservation | res_v37_integration.json (RT06) | Décision du propriétaire sur la conservation, puis correctif (par ex. trace des périodes purgées) |
| R-ATZ-02 | Parcours : aucune suppression complémentaire (complément 1 publié) | NB : banc synthétique seulement ; masqué en exploitation (RT-13 : 0 valeur hors niveau) | Ouverte | RT05, RT13 | — |
| R-ATZ-03 | Complément dérivé nul publié (homogénéité ; ex. tous les Longs ouverts après le Court) ; la suppression primaire, elle, masque le complément nul | NB : arbitrage entre confidentialité et utilité | Ouverte, correctif écarté (masquage de cellules entières dans un usage normal) | RT04 | Décision du propriétaire |
| R-ATZ-04 | Compositions multivariées, croisements entre cellules, données auxiliaires, signaux du masque : absence de fuite non démontrable | IP (structurelle) | Ouverte | § 3.6 du rapport | Pas de levée possible par essais ; seule une méthode formelle le permettrait |
| R-ATZ-05 | Utilité : semaine recoupée par un cumul entièrement masquée ; −9,1 % de valeurs publiées avec V3.7 | NB | Constatée | RT07, RT14 | — |
| R-ATZ-06 | Verrous d'exploitation (administrateurs nommés, échéance, niveau, conservation) non activés ; état réel OVH non contrôlé | LE | Ouverte | — | Décision du propriétaire, puis recette OVH |
| R-ATZ-07 | Cockpit non rejoué en navigateur (contrôlé par lecture du code) | IP | Ouverte | rapport § 4 | Rejeu navigateur |

## B. Transverses (registre du 27/11 ; état postérieur inconnu)

| Id | Réserve (27/11) | Catégorie | État vérifiable en S42 |
|---|---|---|---|
| T-01 | Dette CSS active (173 feuilles, `!important`) — conditions de l'art. 24 | TB au 27/11 | **NON VÉRIFIABLE** : levée éventuelle en S36 à S40 non documentée dans S41 |
| T-02 | Dette JavaScript active (53 scripts sur Signature) | TB au 27/11 | NON VÉRIFIABLE |
| T-03 | PERF-01 : LCP Signature 3,3 s (bloqué par la sanctuarisation de l'en-tête des démos) | TB au 27/11 | NON VÉRIFIABLE |
| T-04 | VID-02 : HLS, VO/FR, plein écran, orientation | TB au 27/11 | NON VÉRIFIABLE |
| T-05 | Zoom réel, Firefox, WebKit | LE | inchangé |
| T-06 | OVH : upload, version MariaDB, HTTP/2, compression ; appareils physiques ; médias réels | LE | inchangé |
| T-07 | Écart de version MariaDB (banc 10.11.14, compose 11.8) | LE | constaté en S42 |

## C. Pièces probatoires manquantes

| Id | Pièce | Effet |
|---|---|---|
| P-01 | Archive S40 | Différentiel S40 → S41 non vérifiable de façon indépendante |
| P-02 | Matrice des 128 articles | Réconciliation impossible |
| P-03 | Registres et rapports S36 à S40 (dont le rapport Work S40) | État des réserves T-01 à T-04 inconnu |
| P-04 | Résultats historiques de charge sur « S40 » (`charge.json`) | Non joints à S41 ; seul le registre du 27/11 les mentionne (paliers 20/50/100/200, 20 s chacun, 0 erreur) |
