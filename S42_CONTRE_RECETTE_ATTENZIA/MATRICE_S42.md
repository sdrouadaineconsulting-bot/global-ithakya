# Matrice S42 — mise à jour des articles touchés par la contre-recette

**La matrice des 128 articles n'a pas été transmise (P-02) : elle n'est ni actualisée ni réconciliée.**
La seule matrice que S41 permet de reconstruire est celle de 81 articles et 129 contrôles historiques (`QUALIFICATION_W360_ASSAINISSEMENT_20261126/outils/matrice_maitre.py`, état au 27/11). Le tableau ci-dessous met à jour ses articles concernés par S42, avec leur numérotation. La correspondance avec la numérotation en 128 articles reste à établir sur pièce.

Statuts : VALIDÉE · CORRIGÉE ET REQUALIFIÉE · PARTIELLEMENT VALIDÉE · NON VALIDÉE · NON EXÉCUTÉE · NON VÉRIFIABLE.

| Art. (81) | Exigence | Statut 27/11 | Statut S42 | Preuve S42 / réserve |
|---|---|---|---|---|
| 27 | Inventaire ATTENZIA | VALIDÉE | VALIDÉE | Lecture intégrale du module V3.6 (379 l.) et du moteur direct |
| 28 | Collecte ATTENZIA | PARTIELLEMENT VALIDÉE | PARTIELLEMENT VALIDÉE | Inchangé (hors périmètre S42) |
| 30 | Antifraude ATTENZIA | VALIDÉE | VALIDÉE | RT-09, RT-13 (rôles, habilitation nominative, échéance, k) |
| 31 | Agrégations ATTENZIA | CORRIGÉE ET REQUALIFIÉE | **CORRIGÉE ET REQUALIFIÉE (S42)** | A-01 corrigée (V3.7) ; RT-01/02/03/13/14 : 0 fuite sur 715 cellules ; réserves R-ATZ-01 à R-ATZ-05 |
| 32 | Interconnexions ATTENZIA | CORRIGÉE ET REQUALIFIÉE | VALIDÉE | RT-11 (instantanés V3.5 lus, exportés et recoupés), RT-12 (export ↔ JSON 0 écart) |
| 33 | Sécurité du cockpit | CORRIGÉE ET REQUALIFIÉE | VALIDÉE | RT-09 : cockpit 404 membre/anonyme, 200 administrateur |
| 34 | Performance ATTENZIA | PARTIELLEMENT VALIDÉE | PARTIELLEMENT VALIDÉE | Pas de volumétrie ATTENZIA à grande échelle ; liste des instantanés sous charge (voir charge) |
| 35 | Rapport autonome ATTENZIA | VALIDÉE | VALIDÉE | RAPPORT_CONTRE_RECETTE_S42.md |
| 45 | Intégrité des données | PARTIELLEMENT VALIDÉE | PARTIELLEMENT VALIDÉE | RT-10 (altération détectée, blocage par défaut) ; orphelins non recherchés |
| 46 | Concurrence et atomicité | VALIDÉE | VALIDÉE | RT-08 (×10 même instantané, cumuls concurrents, exports simultanés) |
| 49 | Charge | VALIDÉE (paliers de 20 s) | voir PV § charge | `res_v37_charge_200_1800s.json` |
| 64 | Compatibilité OVH | PARTIELLEMENT VALIDÉE | PARTIELLEMENT VALIDÉE | Banc MariaDB 10.11 ; OVH non contrôlé (LE) |
| 66 | Non-régression intégrale | PARTIELLEMENT VALIDÉE | PARTIELLEMENT VALIDÉE | S41 → S42 : 2 fichiers modifiés, 0 ajout, 0 retrait ; campagnes générales non rejouées (consigne 4) |
| 67 | Contre-expertise finale | PARTIELLEMENT VALIDÉE | PARTIELLEMENT VALIDÉE | ATTENZIA contre-expertisée ; réserves transverses T-01 à T-04 non vérifiables |
| 79 | Conditions du gel | NON VALIDÉE | **NON VALIDÉE** | Voir PV_GEL_S42.md |

Contrôles nouveaux S42 : RT-01 à RT-14 (rapport § 3.3), statut individuel dans `preuves/res_v37_*.json`.
