"""RT-01..RT-05 : substitution par ratio, homogénéité (complément nul), parcours (banc). Banc local, k=5, données SQL simulées."""
import sys, json; sys.path.insert(0, '.')
from banc42 import *
OUT = {}; K = 5
config('local', attenzia_k=K); reset_atz(); a = admin()
def week(w): return ts(2026, w, 2)
# RT-01 : taux_achevement_long → long_ouverts masqué
t = week(30); R = []
R += [{'steps': {'long_started': t, 'long_finished': t + 4000}} for _ in range(10)]
R += [{'steps': {'long_started': t}} for _ in range(8)]
R += [{'steps': {'court_finished': t}} for _ in range(2)]
seed(R); st, b = figer(a, 'semaine', '2026-S30'); _, r = lire(a, b['id']); c = r['instantane']['donnees']['univers']['pop']
lo = [n for n in range(1, 200) if round(c['long_termines'] / n, 3) == c['taux_achevement_long']] if c.get('taux_achevement_long') else None
OUT['RT01_ratio_achevement'] = {'http': st, 'regle': r['instantane']['regle'], 'cellule_publiee': c, 'reel': {'participants': 20, 'long_ouverts': 18, 'long_termines': 10},
    'long_ouverts_deduit': lo, 'complement_deduit_participants_moins_long_ouverts': (c['participants'] - lo[0]) if lo and len(lo) == 1 and c['participants'] else None}
# RT-02 : taux_approfondissement → court_termines masqué
t = week(31); R = []
R += [{'steps': {'court_finished': t, 'long_started': t + 600}} for _ in range(10)]
R += [{'steps': {'court_finished': t + 7200, 'long_started': t}} for _ in range(6)]
R += [{'steps': {'court_finished': t}} for _ in range(2)]
R += [{'steps': {'long_started': t}} for _ in range(2)]
seed(R); st, b = figer(a, 'semaine', '2026-S31'); _, r = lire(a, b['id']); c = r['instantane']['donnees']['univers']['pop']
ct = [n for n in range(1, 200) if c.get('taux_approfondissement') and round(c['long_apres_court'] / n, 3) == c['taux_approfondissement']]
OUT['RT02_ratio_approfondissement'] = {'http': st, 'cellule_publiee': c, 'reel': {'participants': 20, 'court_termines': 18, 'long_ouverts': 18, 'long_apres_court': 10},
    'court_termines_deduit': ct, 'complement_deduit': (c['participants'] - ct[0]) if len(ct) == 1 and c['participants'] else None}
# RT-05 : parcours (banc) — long_lances / long_termines sans suppression complémentaire
t = week(32); R = [{'steps': {'long_started': t, 'long_finished': t + 4000}} for _ in range(11)] + [{'steps': {'long_started': t}}]
seed(R); st, b = figer(a, 'semaine', '2026-S32'); _, r = lire(a, b['id']); p = r['instantane']['donnees']['parcours']['tous']; u = r['instantane']['donnees']['univers']['pop']
OUT['RT05_parcours_banc'] = {'http': st, 'parcours': {k: p[k] for k in ('court_lances', 'long_lances', 'long_termines', 'abandons_court')}, 'univers_pop': {k: u[k] for k in ('participants', 'long_ouverts', 'long_termines')},
    'complement_deduit_long_lances_moins_termines': (p['long_lances'] - p['long_termines']) if p['long_lances'] is not None and p['long_termines'] is not None else None}
# RT-03 + RT-04 : série cumul (quiz, homogénéité) — base remise à zéro
reset_atz(); t = ts(2026, 33, 2)
R = []
R += [{'steps': {'court_finished': t}, 'quiz': {'at': t, 'correct': True}} for _ in range(10)]
R += [{'steps': {'court_finished': t}, 'quiz': {'at': t, 'correct': False}} for _ in range(8)]
R += [{'steps': {'court_finished': t}} for _ in range(2)]
seed(R, prefix='sxq'); st, b = figer(a, 'cumul', '2026-08-16'); _, r = lire(a, b['id']); c = r['instantane']['donnees']['univers']['pop']
qr = [n for n in range(1, 200) if c.get('taux_quiz_correct') and round(c['quiz_corrects'] / n, 3) == c['taux_quiz_correct']]
OUT['RT03_ratio_quiz'] = {'http': st, 'cellule_publiee': {k: c[k] for k in ('participants', 'quiz_repondus', 'quiz_corrects', 'taux_quiz_correct')}, 'reel': {'participants': 20, 'quiz_repondus': 18, 'quiz_corrects': 10},
    'quiz_repondus_deduit': qr, 'complement_deduit': (c['participants'] - qr[0]) if len(qr) == 1 and c['participants'] else None}
reset_atz(); t = ts(2026, 33, 2)
R = [{'steps': {'court_finished': t, 'long_started': t + 600}} for _ in range(10)] + [{'steps': {'court_finished': t}} for _ in range(15)] + [{'steps': {}, 'quiz': {'at': t, 'correct': True}} for _ in range(5)]
seed(R, prefix='sxh'); st, b = figer(a, 'cumul', '2026-08-16'); _, r = lire(a, b['id']); c = r['instantane']['donnees']['univers']['pop']
OUT['RT04_homogeneite_complement_nul'] = {'http': st, 'cellule_publiee': {k: c[k] for k in ('participants', 'court_termines', 'long_ouverts', 'long_apres_court', 'taux_approfondissement')}, 'reel': {'participants': 30, 'court_termines': 25, 'long_ouverts': 10, 'long_apres_court': 10},
    'complement_long_ouverts_moins_long_apres_court': (c['long_ouverts'] - c['long_apres_court']) if c['long_ouverts'] is not None and c['long_apres_court'] is not None else None}
json.dump(OUT, open(sys.argv[1], 'w'), ensure_ascii=False, indent=1)
for k, v in OUT.items(): print(k, json.dumps(v, ensure_ascii=False))
