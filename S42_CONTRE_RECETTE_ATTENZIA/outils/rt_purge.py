"""RT-06 / RT-06b (R-ATZ-01) : export conservé → suppression d'un compte → purge → (a) refigement de la même période, (b) cumul voisin à +14 j.
RT-15 : isolation d'écriture entre comptes (owner_id d'un autre compte). Usage : rt_purge.py <v37|v38> <sortie>"""
import sys, json, csv, io, shutil, os; sys.path.insert(0, '.')
from banc42 import *
V = sys.argv[1]; W = os.path.dirname(HERE); MOD = '/var/www/ithakya/site/api/ithakya-attenzia-instantanes.php'
shutil.copyfile(f'{W}/{V}/ithakya-attenzia-instantanes.php', MOD); subprocess.run(['chown', 'www-data', MOD]); time.sleep(3)
config('local', attenzia_k=5, atz_conservation_jours=30); reset_atz(); a = admin(); OUT = {'version': V}
v = lambda e: {r[2]: r[3] for r in csv.reader(io.StringIO(e), delimiter=';') if r and r[0] == 'univers' and r[1] == 'pop'}
t = ts(2026, 30, 2)
seed([{'steps': {'court_finished': t, 'long_started': t + 60}} for _ in range(12)] + [{'steps': {'court_finished': t}} for _ in range(8)] + [{'steps': {'long_started': t}} for _ in range(6)], prefix='sxp')
st, b = figer(a, 'cumul', '2026-07-31'); e1 = v(a.get('attenzia_export', id=b['id']).text)
cible = sql("SELECT u.id FROM itp_users u JOIN itp_work_progress w ON w.user_id=u.id WHERE u.login LIKE 'sxp%' AND JSON_EXTRACT(w.data,'$.steps.long_started') IS NOT NULL AND JSON_EXTRACT(w.data,'$.steps.court_finished') IS NOT NULL LIMIT 1")
sql(f"DELETE FROM itp_work_progress WHERE user_id='{cible}'; DELETE FROM itp_users WHERE id='{cible}'")
sql("UPDATE itp_atz_snapshots SET created_at = created_at - 40*86400")   # SIMULATION du temps écoulé (empreinte non affectée)
pg = a.post('attenzia_purger', {'confirmer': True}).json()
st_a, b_a = figer(a, 'cumul', '2026-07-31')
e_a = v(a.get('attenzia_export', id=b_a['id']).text) if st_a == 201 else None
st_b, b_b = figer(a, 'cumul', '2026-08-14')
e_b = v(a.get('attenzia_export', id=b_b['id']).text) if st_b == 201 else None
diff = lambda x: {k: int(e1[k]) - int(x[k]) for k in ('participants', 'court_termines', 'long_ouverts', 'long_apres_court') if x and e1.get(k) and x.get(k)}
OUT['RT06'] = {'figement_initial': st, 'export_conserve_pop': e1, 'purge': pg, 'refigement_meme_periode': st_a, 'refigement_erreur': (b_a or {}).get('error'), 'difference_meme_periode': diff(e_a)}
OUT['RT06b'] = {'cumul_voisin_14j': st_b, 'masques_incrementaux': (b_b or {}).get('masques_incrementaux'), 'export_pop': e_b, 'differences_publiees_vs_export_conserve': diff(e_b)}
OUT['garde_non_servie'] = {'liste_instantanes': [x['cle'] for x in a.get('attenzia_instantanes').json().get('instantanes', [])],
                           'lignes_garde': (sql("SELECT COUNT(*) FROM itp_atz_garde") if 'itp_atz_garde' in sql("SHOW TABLES") else 'table absente')}
# RT-15 : isolation d'écriture
m1, m2 = member('sxiso1'), member('sxiso2'); id2 = m2.get('session').json()['user']['id']
r = m1.post('progress', {'oeuvre': 'ith-pop-moment', 'event': 'note_k', 'value': 3, 'owner_id': id2})
OUT['RT15_isolation_ecriture'] = {'http': r.status_code, 'erreur': (r.json() if r.headers.get('content-type','').startswith('application/json') else {}).get('error'),
    'lignes_creees_pour_m2': sql(f"SELECT COUNT(*) FROM itp_work_progress WHERE user_id='{id2}'")}
json.dump(OUT, open(sys.argv[2], 'w'), ensure_ascii=False, indent=1); print(json.dumps(OUT, ensure_ascii=False)[:1800])
