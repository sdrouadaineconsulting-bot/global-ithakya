"""S42 — réconciliation de la matrice 128 articles et du registre S40 (Work) avec la contre-recette S42.
Les colonnes S36–S40 sont reprises sans modification ; quatre colonnes S42 sont ajoutées. Usage : reconcilier_s42.py <dossier_S40> <charge.json> <sortie>"""
import csv, json, sys, io
D, CH, OUT = sys.argv[1:4]
c = json.load(open(CH))
ok_charge = c['verdict_criteres']['plateau_conforme']
txt_charge = (f"Plateau {c['utilisateurs_simultanes']} comptes × {c['duree_s']} s (banc S42 : {c['banc']}). {c['requetes']} requêtes, {c['erreurs']} erreurs inattendues, "
              f"P95 {c['p95_ms']} ms, P99 {c['p99_ms']} ms (toutes opérations) ; contrôles finaux : {c['verdict_criteres']['controles_finaux']}. Scénario S42 distinct du protocole S35 (sans MP4 ni Publications).")
S42 = {
 'W-95': ('Contre-expertise V3.6 : 10 750 + 267 assertions rejouées ; anomalie A-01 démontrée (taux restituant un effectif masqué, complément 2 < k, y compris en exploitation) et corrigée en V3.7 ; attaquant automatisé sur 715 cellules conjointes : 84 → 0 cellule en fuite.',
          'Partiellement qualifié', 'Purge puis refigement : différence de 1 démontrée (R-ATZ-01, dépend de la politique de conservation) ; complément nul publié (R-ATZ-03) ; absence de fuite non démontrable en général ; inventaire des exports antérieurs avant activation réelle (inchangé).',
          'res_v36_*.json, res_v37_*.json, S41_S42_attenzia_v3_7.diff'),
 'W-37': ('Sécurité : rôles, habilitation nominative, échéance, k, niveau unique (RT-09, RT-13) ; exports simultanés (RT-08). ' + txt_charge,
          'Intégralement qualifié' if ok_charge else 'Partiellement qualifié', 'Exports soutenus bornés par la limite applicative (5 par 24 h et par administrateur) ; banc distinct du banc S35 ; OVH non qualifié (R14).', 'res_v37_integration.json, res_v37_exploitation.json, res_v37_charge_200_1800s.json'),
 'W-44': (txt_charge, 'Intégralement qualifié' if ok_charge else 'Partiellement qualifié', 'Protocole S35 (MP4 en requêtes partielles, Publications, instrumentation des invariants) non rejoué : son environnement d’exécution n’est pas fourni ; aucune extrapolation à OVH (R14).', 'res_v37_charge_200_1800s.json'),
 'W-35': ('Oracle indépendant S42 (attaquant automatisé sur restitution par taux) ajouté ; décision inchangée.', '', '', 'res_v3*_fuzz.json'),
 'W-36': ('A-01 relève de la confidentialité (W-95), pas de la validité des indicateurs : valeurs publiées exactes (RT-12, 0 écart export/JSON).', '', '', 'res_v37_integration.json'),
}
M = list(csv.DictReader(open(f'{D}/ITHAKYA_W360_MATRICE_128_ARTICLES_S40_20261128.csv', encoding='utf-8-sig')))
cols = list(M[0].keys()) + ['Apport S42', 'Décision stricte S42', 'Limite S42', 'Preuve S42']
for r in M:
    a, d, l, p = S42.get(r['Article'], ('', '', '', ''))
    base = r['Décision stricte S40'] or r['Statut strict S39']
    r.update({'Apport S42': a, 'Décision stricte S42': d or base, 'Limite S42': l, 'Preuve S42': p})
with open(f'{OUT}/MATRICE_128_ARTICLES_S42.csv', 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(M)
from collections import Counter
print('matrice', len(M), dict(Counter(r['Décision stricte S42'] for r in M)))
R = list(csv.DictReader(open(f'{D}/ITHAKYA_W360_REGISTRE_RESERVES_S40_20261128.csv', encoding='utf-8-sig')))
S42R = {
 'S39-I01': ('Technologique (A-01) corrigée ; insuffisance probatoire résiduelle', 'A-01 corrigée en V3.7 ; publications conjointes d’une même cellule : 0 fuite sur 715 cellules ; R-ATZ-01 (purge) démontrée et ouverte', 'Avant activation réelle : décision de conservation et correctif R-ATZ-01 ; inventaire des exports antérieurs ; arbitrage R-ATZ-03'),
 'S40-CHARGE': (('Levée sur le banc S42' if ok_charge else 'Insuffisance probatoire interne'), txt_charge, ('Aucune extrapolation à OVH (R14)' if ok_charge else 'Plateau à reprendre selon les critères S35')),
}
rc = list(R[0].keys()) + ['Nature S42', 'Décision S42', 'Action indispensable ou portée S42']
for r in R:
    n, d, a = S42R.get(r['Réserve'], ('', 'Décision S40 reconduite' if r['Décision S40'] else 'Décision antérieure reconduite', ''))
    r.update({'Nature S42': n, 'Décision S42': d, 'Action indispensable ou portée S42': a})
extra = [{'Réserve': x, 'Périmètre': p, 'Nature S42': n, 'Décision S42': d, 'Action indispensable ou portée S42': a} for x, p, n, d, a in [
 ('S42-A01', 'ATTENZIA — taux de substitution', 'Anomalie technologique', 'Corrigée et requalifiée (V3.7)', '—'),
 ('S42-R-ATZ-01', 'ATTENZIA — purge et refigement', 'Technologique, dépendante de la politique de conservation', 'Ouverte ; démontrée (Δ = 1)', 'Bloque l’activation sur données réelles, pas le gel du code (ATTENZIA désactivé par défaut)'),
 ('S42-R-ATZ-02', 'ATTENZIA — parcours sans suppression complémentaire', 'Technologique, banc seulement', 'Ouverte ; masqué en exploitation', 'Sans effet sur les données réelles'),
 ('S42-R-ATZ-03', 'ATTENZIA — complément dérivé nul', 'Arbitrage confidentialité / utilité', 'Ouverte', 'Décision du propriétaire'),
 ('S42-T07', 'Banc S42', 'Représentativité', 'MariaDB 10.11.14 / PHP 8.3.6 / 4 vCPU (banc S40 : 11.8.9 / 8.4.28 / 9 CPU)', 'Portée locale')]]
with open(f'{OUT}/REGISTRE_RESERVES_S42.csv', 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, fieldnames=rc); w.writeheader(); w.writerows(R + extra)
print('registre', len(R) + len(extra))
