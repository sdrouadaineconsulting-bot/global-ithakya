# ITHAKYA Premium W360 · Procès-verbal S42 · 28 novembre 2026

**Décision : candidate S42 NON GELÉE. S36 demeure la référence technologique officielle. S40 et S41 sont préservées sans modification.**

Candidate : `ITHAKYA_PREMIUM_W360_S42_ATTENZIA_V38_CANDIDATE_20261128.zip` — 100 601 358 octets — SHA-256 `8b7df5c93cd07027d1fb9bab502533d3d56d38596bfdfc28f4032c8ecb9e6655` — CRC OK — 4 135 fichiers. Seuls diffèrent de S40 et de S41 les deux chemins du module, identiques entre eux : `source/serveur/` et `site/api/ithakya-attenzia-instantanes.php` (règle `ATZ-INSTANTANES-V3.8`, SHA-256 `e0cd26db…bd87`). Aucun ajout, aucun retrait. Aucun contenu éditorial, graphique, narratif, de quiz, de parcours ou de gamification n'est modifié.

## Filiation vérifiée
- S41 reconstituée à partir de six parties (100 600 542 octets, `01149a30…08c4`) ; 4 135 empreintes conformes à `MANIFESTE_S41.json`.
- Inventaire S40 (`ITHAKYA_W360_MANIFESTE_INTEGRAL_S40_20261128.json`) comparé à S41 : seuls les deux chemins du module diffèrent. La V3.5 reconstituée en inversant le correctif S41 a l'empreinte S40 (`d63d5f1e…9b65`). L'archive S40 elle-même n'a pas été transmise ; seule son empreinte déclarée (`b2262169…d204`) est connue.

## Condition S40 n° 1 — confidentialité ATTENZIA (W-95, S39-I01)
- V3.6 rejouée : 267 et 10 750 assertions identiques au déclaré. Leur couverture est limitée : une relation, le garde isolé, l'auteur du correctif.
- **A-01, démontrée** sur V3.6 et les versions antérieures, y compris en exploitation privée : un taux publié avec un terme masqué restitue l'effectif masqué et un complément de 2 < k. Un attaquant automatisé trouve 84 cellules en fuite sur 715. **Corrigée en V3.7** : 0 fuite. Utilité : −9,1 % de valeurs publiées.
- **R-ATZ-01, démontrée** : après purge, un export conservé et un refigement de la même période ou d'un cumul voisin (+14 j) révèlent une différence de 1. **Corrigée en V3.8** : la purge retire l'instantané de la consultation et de l'export, mais conserve une trace de garde non servie. Refigement de la même période : 409. Cumul voisin : cellule masquée. Toutes les suites V3.7 sont rejouées sur V3.8 ; les écarts se limitent à l'identifiant de règle et à RT-06 ; l'attaquant automatisé donne un résultat identique.
- Restent ouverts : complément dérivé nul publié (R-ATZ-03, arbitrage du propriétaire) ; parcours sans suppression complémentaire, banc seulement (R-ATZ-02) ; absence de fuite non démontrable en général (R-ATZ-04) ; inventaire des exports antérieurs avant activation réelle (action S40 maintenue).
- **Comportement modifié à valider par le propriétaire :** la purge V3.8 conserve les agrégats déjà publiés dans une table de garde.

## Condition S40 n° 2 — plateau de 1 800 s à 200 utilisateurs (S40-CHARGE, W-37, W-44)
Exécuté sur la candidate V3.7 : 200 comptes pendant 1 817,7 s ; 1 102 381 requêtes ; 0 erreur inattendue ; P95 de 677,7 ms la première minute et de 704,6 ms la dernière, sans dérive notable. La différence V3.7 → V3.8 ne touche ni les chemins de ce scénario ni la liste des instantanés : le plateau n'a pas été relancé.

| Critère S35 | Résultat | Statut |
|---|---|---|
| Défauts inattendus < 1 % | 0 % | Conforme |
| P95 lectures ≤ 500 ms | > 500 ms, démontré par dénombrement (P95 toutes opérations 678,5 ms ; écritures 241,4 ms). Diagnostic serveur de 90 s : lectures 602,6 ms | **Non conforme** |
| P99 lectures ≤ 1 500 ms | indéterminé sur le plateau (toutes opérations 1 757,6 ms) ; diagnostic serveur : 736,3 ms | Non démontré |
| Intégrité finale | 15/15 tables OK, 200 comptes, une ligne de progression par compte, 0 orphelin, Note K bornée, économie fermée ; contrôles faits après un redémarrage imprévu du conteneur (reprise sur incident InnoDB réussie) | Conforme |
| Isolation | écriture avec l'`owner_id` d'un autre compte : 409, aucune ligne créée ; rôles 403 | Conforme |

Analyse de l'écart P95, sans attribution automatique au matériel. Côté serveur, `session` (P95 621 ms) et `profile` (666 ms) concentrent le dépassement ; `oeuvres`, `progression` et les écritures restent sous 205 ms. À vide, ces deux actions coûtent 7,8 et 9,4 ms, contre 2,4 à 2,8 ms pour les autres : environ trois fois plus. Sous saturation (4 vCPU, 150 processus Apache sur 150, charge moyenne jusqu'à 152, client sur la même machine), ce coût s'amplifie. Le banc S42 diffère du banc S40 : MariaDB 10.11.14 contre 11.8.9, PHP 8.3.6 contre 8.4.28, 4 vCPU contre 9, 150 workers contre 24, scénario sans MP4 ni Publications. Les mesures ne sont pas transposables à OVH (R14). Optimiser `session` et `profile` sort du périmètre S42 : c'est une proposition séparée, non appliquée.

## Réconciliation
Matrice des 128 articles : `reconciliation/MATRICE_128_ARTICLES_S42.csv`. Les colonnes S36 à S40 sont reprises sans modification ; quatre colonnes S42 sont ajoutées. Résultat : **48 articles intégralement qualifiés, 80 partiellement** (inchangé). W-95, W-37 et W-44 restent partiellement qualifiés malgré les apports S42.
Registre : `reconciliation/REGISTRE_RESERVES_S42.csv` (19 réserves S40 reprises, 6 entrées S42). R12, R13, R14 et R15 sont inchangées et restent sans effet sur la décision.

## Motif du non-gel
La seule réserve technologique qui empêche objectivement le gel est **S40-CHARGE (W-37, W-44)** : le critère S35 « P95 des lectures ≤ 500 ms à 200 comptes » n'est pas atteint sur le banc de recette. Il est démontré que ce dépassement vient principalement de `session` et de `profile`.
Pour W-95, la partie démontrable par essais est traitée (A-01 et R-ATZ-01 corrigées). Le reliquat relève de l'insuffisance probatoire structurelle (R-ATZ-04) et d'actions préalables à l'activation sur données réelles (inventaire des exports antérieurs, R-ATZ-03, validation de la purge V3.8). Il appartient au propriétaire de dire si ce reliquat conditionne aussi le gel.

## Actions indispensables avant le gel
1. Ramener le P95 des lectures nominales à 500 ms ou moins à 200 comptes (critère S35), ou faire réviser ce critère par le propriétaire. Puis rejouer un plateau de 1 800 s en enregistrant séparément les distributions des lectures.
2. Faire valider par le propriétaire le comportement de purge V3.8 et l'arbitrage R-ATZ-03.
