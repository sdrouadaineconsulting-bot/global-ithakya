"""RT-14 : attaquant automatisé indépendant sur jeux aléatoires (graine fixe). Pour chaque cellule publiée : effectifs publiés + effectifs
restitués par les taux (solution entière unique), puis compléments de toutes les relations d'inclusion garanties par le calcul.
Fuite = complément dans ]0, k[ ; homogénéité = complément nul. Utilité = nombre de valeurs scalaires publiées. Usage : rt_fuzz.py <v36|v37> <sortie>"""
import sys, json, random, shutil, os, time; sys.path.insert(0, '.')
from banc42 import *
V = sys.argv[1]; W = os.path.dirname(HERE); MOD = '/var/www/ithakya/site/api/ithakya-attenzia-instantanes.php'
shutil.copyfile(f'{W}/{V}/ithakya-attenzia-instantanes.php', MOD); subprocess.run(['chown', 'www-data', MOD])
K = 5; config('local', attenzia_k=K); reset_atz(); a = admin()
REL = [('participants', x) for x in ('court_termines', 'long_ouverts', 'long_termines', 'long_apres_court', 'quiz_repondus', 'quiz_corrects', 'notes_k_donnees')] + [('court_termines', 'long_apres_court'), ('long_ouverts', 'long_termines'), ('long_ouverts', 'long_apres_court'), ('quiz_repondus', 'quiz_corrects')]
TAUX = {'taux_approfondissement': ('long_apres_court', 'court_termines'), 'taux_achevement_long': ('long_termines', 'long_ouverts'), 'taux_quiz_correct': ('quiz_corrects', 'quiz_repondus')}
def attaquant(c):
    v = {k: x for k, x in c.items() if isinstance(x, int)}
    for t, (num, den) in TAUX.items():
        q = c.get(t)
        if not isinstance(q, float): continue
        if num in v and den not in v:
            s = [n for n in range(1, 2000) if round(v[num] / n, 3) == q]
            if len(s) == 1: v[den] = s[0]
        if den in v and num not in v:
            s = [n for n in range(0, v[den] + 1) if round(n / v[den], 3) == q]
            if len(s) == 1: v[num] = s[0]
    fuites = [(t, s, v[t] - v[s]) for t, s in REL if t in v and s in v and 0 < v[t] - v[s] < K]
    homog = [(t, s) for t, s in REL if t in v and s in v and v[t] == v[s]]
    return fuites, homog, sum(1 for x in c.values() if x is not None and not isinstance(x, list))
def jeu(rng, t, cumul):
    R = []
    for _ in range(rng.randint(8, 80)):
        st = {}; r = {}
        if rng.random() < .75: st['court_finished'] = t + rng.randint(0, 3600)
        if rng.random() < .6:
            st['long_started'] = (st['court_finished'] + rng.randint(1, 600)) if ('court_finished' in st and rng.random() < .8) else t + rng.randint(0, 1000)
            if rng.random() < .5: st['long_finished'] = st['long_started'] + 4000
        if cumul and rng.random() < .6: r['quiz'] = {'at': t, 'correct': rng.random() < .55}
        if cumul and rng.random() < .5: r['note_k'] = rng.randint(1, 5); r['field_at_ms'] = {'note_k': t * 1000}
        r['steps'] = st; r['ctx'], r['work'] = rng.choice([('pop', 'ith-pop-moment'), ('signature', 'ith-signature-lien'), ('soleil', 'ith-soleil-courant'), ('progression', 'ith-progression-elan')])
        R.append(r)
    return R
rng = random.Random(4242); stats = {'cellules': 0, 'cellules_avec_fuite': 0, 'fuites': 0, 'homogeneites': 0, 'valeurs_publiees': 0, 'instantanes': 0, 'exemples': []}
plan = [('semaine', f'2026-S{w:02d}', ts(2026, w, 2), False) for w in range(2, 42)] + [('cumul', None, None, True)] * 15
for serie, cle, t, cumul in plan:
    if cumul:
        reset_atz(); t = ts(2026, 20, 2); cle = '2026-05-31'
    seed(jeu(rng, t, cumul), prefix='sxf')
    st, b = figer(a, serie, cle)
    if st != 201: stats.setdefault('erreurs', []).append((cle, st, b)); continue
    _, r = lire(a, b['id']); stats['instantanes'] += 1
    for dim in ('univers', 'oeuvres', 'territoires'):
        for k_, c in r['instantane']['donnees'][dim].items():
            f, h, n = attaquant(c); stats['cellules'] += 1; stats['valeurs_publiees'] += n; stats['fuites'] += len(f); stats['homogeneites'] += len(h)
            if f:
                stats['cellules_avec_fuite'] += 1
                if len(stats['exemples']) < 6: stats['exemples'].append({'instantane': f'{serie}:{cle}', 'cellule': f'{dim}/{k_}', 'publie': c, 'fuites': f})
json.dump({'version': V, 'k': K, 'graine': 4242, **stats}, open(sys.argv[2], 'w'), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in stats.items() if k != 'exemples'}, ensure_ascii=False)); print(json.dumps(stats['exemples'][:2], ensure_ascii=False)[:900])
