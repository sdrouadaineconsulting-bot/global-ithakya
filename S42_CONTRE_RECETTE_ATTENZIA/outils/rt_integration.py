"""RT-06..RT-12 : purge et refigement, utilité intersérie, concurrence, isolation/rôles, exploitation, intégrité, compatibilité, cohérence export. Banc local."""
import sys, json, csv, io, threading, subprocess, time; sys.path.insert(0, '.')
from banc42 import *
from concurrent.futures import ThreadPoolExecutor
OUT = {}; K = 5
config('local', attenzia_k=K, atz_conservation_jours=30); reset_atz(); a = admin()
pop = lambda r: r['instantane']['donnees']['univers']['pop']
# RT-06 : export conservé → purge → refigement de la même période après suppression d'un compte
t = ts(2026, 30, 2)
seed([{'steps': {'court_finished': t, 'long_started': t + 60}} for _ in range(12)] + [{'steps': {'court_finished': t}} for _ in range(8)], prefix='sxp')
st, b = figer(a, 'cumul', '2026-07-31'); e1 = a.get('attenzia_export', id=b['id']).text
cible = sql("SELECT id FROM itp_users WHERE login LIKE 'sxp%' ORDER BY id LIMIT 1")
sql(f"DELETE FROM itp_work_progress WHERE user_id='{cible}'; DELETE FROM itp_users WHERE id='{cible}'")   # suppression de compte (simulation SQL)
refig_avant = figer(a, 'cumul', '2026-07-31')[0]
sql("UPDATE itp_atz_snapshots SET created_at = created_at - 40*86400")   # SIMULATION du passage du temps (40 j) ; empreinte inchangée (payload non modifié)
pg = a.post('attenzia_purger', {'confirmer': True}).json()
st2, b2 = figer(a, 'cumul', '2026-07-31'); e2 = a.get('attenzia_export', id=b2['id']).text
v = lambda e: {r[2]: r[3] for r in csv.reader(io.StringIO(e), delimiter=';') if r and r[0] == 'univers' and r[1] == 'pop'}
OUT['RT06_purge_refigement'] = {'figement_1': st, 'refigement_avant_purge': refig_avant, 'purge': pg, 'refigement_apres_purge': st2,
    'export_1_pop': v(e1), 'export_2_pop': v(e2), 'difference_participants': int(v(e1)['participants']) - int(v(e2)['participants']) if v(e1)['participants'] and v(e2)['participants'] else None}
# RT-07 : utilité — masquage intersérie (cumul existant → semaine recoupée)
reset_atz(); t = ts(2026, 30, 2)
seed([{'steps': {'court_finished': t, 'long_started': t + 60, 'long_finished': t + 4000}} for _ in range(20)] + [{'steps': {'court_finished': t}} for _ in range(20)] + [{'steps': {'long_started': t}} for _ in range(15)], prefix='sxu')
_, s1 = figer(a, 'semaine', '2026-S30'); _, r1 = lire(a, s1['id'])
reset_atz(); seed([{'steps': {'court_finished': t, 'long_started': t + 60, 'long_finished': t + 4000}} for _ in range(20)] + [{'steps': {'court_finished': t}} for _ in range(20)] + [{'steps': {'long_started': t}} for _ in range(15)], prefix='sxu')
figer(a, 'cumul', '2026-08-31'); _, s2 = figer(a, 'semaine', '2026-S30'); _, r2 = lire(a, s2['id'])
cnt = lambda d: sum(1 for dim in ('univers', 'oeuvres', 'territoires', 'parcours') for c in d[dim].values() for x in c.values() if x is not None and not isinstance(x, list))
OUT['RT07_utilite_interserie'] = {'semaine_seule_valeurs_publiees': cnt(r1['instantane']['donnees']), 'semaine_apres_cumul_valeurs_publiees': cnt(r2['instantane']['donnees']), 'masques_incrementaux': r2['instantane']['masques_incrementaux']}
# RT-08 : concurrence (même instantané ×10 ; deux cumuls trop proches en parallèle ; exports simultanés)
reset_atz(); seed([{'steps': {'court_finished': ts(2026, w, 2)}} for w in range(20, 30) for _ in range(6)], prefix='sxc')
with ThreadPoolExecutor(10) as ex: codes = list(ex.map(lambda _: figer(a, 'semaine', '2026-S25')[0], range(10)))
with ThreadPoolExecutor(2) as ex: proches = list(ex.map(lambda c: figer(a, 'cumul', c)[0], ['2026-06-10', '2026-06-12']))
with ThreadPoolExecutor(8) as ex: distincts = list(ex.map(lambda w: figer(a, 'semaine', f'2026-S{w}')[0], range(20, 25)))
n_s25 = sql("SELECT COUNT(*) FROM itp_atz_snapshots WHERE serie='semaine' AND cle='2026-S25'"); n_cum = sql("SELECT COUNT(*) FROM itp_atz_snapshots WHERE serie='cumul'")
sid = sql("SELECT id FROM itp_atz_snapshots WHERE cle='2026-S25'")
with ThreadPoolExecutor(5) as ex: exports = list(ex.map(lambda _: a.get('attenzia_export', id=sid), range(5)))
OUT['RT08_concurrence'] = {'meme_instantane_x10_codes': sorted(codes), 'lignes_S25': int(n_s25), 'cumuls_proches_paralleles_codes': sorted(proches), 'cumuls_en_base': int(n_cum),
    'semaines_distinctes_paralleles_codes': sorted(distincts), 'exports_paralleles_codes': [x.status_code for x in exports], 'exports_identiques': len({x.text for x in exports}) == 1,
    'verrous_residuels': sql("SELECT COUNT(*) FROM information_schema.METADATA_LOCK_INFO") if False else 'n/a'}
# RT-09 : isolation des rôles (banc)
m = member('sxmembre01'); anon = C()
acts = [('get', 'attenzia_instantanes', {}), ('get', 'attenzia_instantane', {'id': sid}), ('get', 'attenzia_export', {'id': sid}), ('get', 'attenzia_journal', {}), ('post', 'attenzia_instantane_creer', {'serie': 'semaine', 'cle': '2026-S26'}), ('post', 'attenzia_purger', {'confirmer': True})]
def appel(c, m_, act, p): return (c.get(act, **p) if m_ == 'get' else c.post(act, p)).status_code
OUT['RT09_roles_banc'] = {'membre': {act: appel(m, m_, act, p) for m_, act, p in acts}, 'anonyme': {act: appel(anon, m_, act, p) for m_, act, p in acts},
    'admin_filtre_libre': a.get('attenzia_instantanes', univers='pop').status_code, 'cockpit_membre': m.s.get(B + '/attenzia-cockpit.php').status_code, 'cockpit_anonyme': anon.s.get(B + '/attenzia-cockpit.php').status_code, 'cockpit_admin': a.s.get(B + '/attenzia-cockpit.php').status_code}
# RT-10 : intégrité (altération d'un instantané en base) — lecture et nouvelle publication refusées (fail closed)
sql(f"UPDATE itp_atz_snapshots SET payload = REPLACE(payload, '\"participants\":6', '\"participants\":7') WHERE id='{sid}'")
OUT['RT10_integrite'] = {'lecture_alteree': lire(a, sid)[0], 'export_altere': a.get('attenzia_export', id=sid).status_code, 'nouvelle_publication_recoupee': figer(a, 'cumul', '2026-07-31')[0]}
# RT-12 : cohérence export CSV / JSON (instantané sain)
reset_atz(); seed([{'steps': {'court_finished': t, 'long_started': t + 60}} for _ in range(12)] + [{'steps': {'court_finished': t}} for _ in range(8)], prefix='sxe')
_, b = figer(a, 'semaine', '2026-S30'); _, r = lire(a, b['id']); e = a.get('attenzia_export', id=b['id'])
rows = list(csv.reader(io.StringIO(e.text), delimiter=';'))[1:]; D = r['instantane']['donnees']
ecarts = [x for x in rows if str(D[x[0]][x[1]][x[2]] if D[x[0]][x[1]][x[2]] is not None else '') != x[3]]
attendus = sum(1 for dim in ('univers', 'oeuvres', 'territoires', 'parcours') for c in D[dim].values() for x in c.values() if not isinstance(x, list))
OUT['RT12_coherence_export'] = {'http': e.status_code, 'type': e.headers.get('Content-Type'), 'lignes_csv': len(rows), 'valeurs_json_scalaires': attendus, 'ecarts': ecarts[:5], 'n_ecarts': len(ecarts)}
json.dump(OUT, open(sys.argv[1], 'w'), ensure_ascii=False, indent=1)
for k, v in OUT.items(): print(k, json.dumps(v, ensure_ascii=False)[:700])
