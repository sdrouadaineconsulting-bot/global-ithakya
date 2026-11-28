"""S42 — contrôles de fin de plateau (critères S35) puis verdict. Usage : controle_final_charge.py <charge.json>  (complète le fichier)."""
import sys, json, subprocess; sys.path.insert(0, __import__('os').path.dirname(__file__))
from banc42 import *
P = sys.argv[1]; c = json.load(open(P))
tables = sql("SHOW TABLES").split('\n')
chk = sql("CHECK TABLE " + ','.join(tables)); ok_tables = sum(1 for l in chk.splitlines() if l.split('\t')[2:4] == ['status', 'OK'])
a = admin(); sess = a.get('session'); prog = a.get('oeuvres').status_code
comptes = int(sql("SELECT COUNT(*) FROM itp_users WHERE login LIKE 'charge%'"))
lignes = sql("SELECT u.login, COUNT(w.user_id) FROM itp_users u LEFT JOIN itp_work_progress w ON w.user_id=u.id AND w.work_id='ith-pop-moment' WHERE u.login LIKE 'charge%' GROUP BY u.login")
par = [int(l.split('\t')[1]) for l in lignes.splitlines()]
notes = sql("SELECT JSON_EXTRACT(w.data,'$.note_k') FROM itp_work_progress w JOIN itp_users u ON u.id=w.user_id WHERE u.login LIKE 'charge%'").split()
orphelins = int(sql("SELECT COUNT(*) FROM itp_work_progress w LEFT JOIN itp_users u ON u.id=w.user_id WHERE u.id IS NULL"))
eco = {}
for t in ('itp_eco_ledger', 'itp_eco_wallets'):
    if t in tables: eco[t] = sql(f"SELECT COUNT(*) FROM {t}")
fin = {'tables_check_ok': f'{ok_tables}/{len(tables)}', 'session_admin_apres_drainage': sess.status_code, 'role_admin': (sess.json().get('user') or {}).get('is_admin'), 'oeuvres_apres_drainage': prog,
       'comptes_charge': comptes, 'lignes_progression_par_compte': sorted(set(par)), 'notes_k_hors_bornes': sum(1 for n in notes if n not in ('1', '2', '3', '4', '5')),
       'lignes_orphelines': orphelins, 'tables_economie': eco or 'absentes (économie fermée, mode A)'}
# Critères S35 : < 1 % de défauts inattendus ; P95 ≤ 500 ms ; P99 ≤ 1 500 ms sur les lectures nominales.
# Les distributions des lectures n'ont pas été enregistrées séparément. Lectures = 80 % des requêtes (4 opérations sur 5), écritures = 20 %.
# P95 : si P95(lectures) ≤ 500, alors part(toutes > 500) ≤ 0,8·5 % + 0,2·5 % (P95 écritures = 241 ms < 500) = 5 %, d'où P95(toutes) ≤ 500.
#       Or P95(toutes) > 500 : donc P95(lectures) > 500 — NON-CONFORMITÉ DÉMONTRÉE par dénombrement.
# P99 : la part des écritures au-delà de 1 500 ms n'est bornée qu'à 5 % : le critère n'est ni démontré ni infirmé (indéterminé).
lect = 0.8
p95_lect_gt_500 = c['p95_ms'] > 500 and c['p95_ecriture_ms'] <= 500
crit = {'defauts_inattendus_lt_1pct': c['taux_erreur'] < 0.01, 'P95_lectures_le_500ms': (False if p95_lect_gt_500 else None),
        'P99_lectures_le_1500ms': (True if c['max_ms'] <= 1500 else None), 'P95_toutes_operations_ms': c['p95_ms'], 'P99_toutes_operations_ms': c['p99_ms'], 'P95_ecritures_ms': c['p95_ecriture_ms'],
        'methode': 'dénombrement sur la répartition 80 % lectures / 20 % écritures ; distributions des lectures non enregistrées séparément ; None = indéterminé'}
integre = ok_tables == len(tables) and sess.status_code == 200 and prog == 200 and comptes == c['utilisateurs_simultanes'] and set(par) == {1} and fin['notes_k_hors_bornes'] == 0 and orphelins == 0
duree_ok = c['duree_s'] >= 1800
conf = all(v is True for v in (crit['defauts_inattendus_lt_1pct'],)) and duree_ok and integre
c['controles_finaux'] = fin; c['criteres_S35'] = crit
c['verdict_criteres'] = {'duree_ge_1800s': duree_ok, 'integrite_finale': integre, 'defauts': crit['defauts_inattendus_lt_1pct'], 'P95': crit['P95_lectures_le_500ms'], 'P99': crit['P99_lectures_le_1500ms'],
    'plateau_conforme': bool(conf and crit['P95_lectures_le_500ms'] is True and crit['P99_lectures_le_1500ms'] is True), 'controles_finaux': 'conformes' if integre else 'NON conformes'}
json.dump(c, open(P, 'w'), ensure_ascii=False, indent=1); print(json.dumps({k: c[k] for k in ('controles_finaux', 'criteres_S35', 'verdict_criteres')}, ensure_ascii=False, indent=1))
