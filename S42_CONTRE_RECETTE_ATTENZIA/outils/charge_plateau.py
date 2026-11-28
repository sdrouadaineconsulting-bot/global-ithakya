"""S42 — plateau de charge : 200 utilisateurs simultanés pendant DUREE s (défaut 1800) sur la candidate finale (banc local, client sur la même machine).
Scénario identique à QUALIFICATION_W360_ASSAINISSEMENT_20261126/outils/charge.py (session, oeuvres, progression, profil, écriture note_k), plus 1 administrateur
lisant la liste des instantanés ATTENZIA toutes les 30 s. Séries par minute : débit, p50/p95/p99, erreurs, mémoire, threads MariaDB, processus Apache."""
import sys, json, time, threading, subprocess; sys.path.insert(0, '.')
from banc42 import *
from concurrent.futures import ThreadPoolExecutor
N = int(sys.argv[2]) if len(sys.argv) > 2 else 200; DUREE = int(sys.argv[3]) if len(sys.argv) > 3 else 1800; OUT = sys.argv[1]
config('local', attenzia_k=5, limites_recette=50)
def mk(i):
    c = C(); r = c.post('register', {'login': f'charge{i:04d}', 'display_name': 'Charge', 'password': PW, 'avatar': 'ocean', 'interests': []})
    if r.status_code != 201: c.login(f'charge{i:04d}')
    return c
with ThreadPoolExecutor(20) as ex: pool = list(ex.map(mk, range(N)))
ids = [c.get('session').json()['user']['id'] for c in pool]
lock = threading.Lock(); LAT = []; ERR = []
def scen(c, uid, stop):
    i = 0
    while time.time() < stop:
        for act, fn in (('session', lambda: c.get('session')), ('oeuvres', lambda: c.get('oeuvres')), ('progression', lambda: c.get('progression')), ('profile', lambda: c.get('profile')),
                        ('ecriture', lambda: c.post('progress', {'oeuvre': 'ith-pop-moment', 'event': 'note_k', 'value': 1 + i % 5, 'owner_id': uid}))):
            t = time.perf_counter()
            try: s = fn().status_code
            except Exception: s = -1
            now = time.time(); d = (time.perf_counter() - t) * 1000
            with lock:
                LAT.append((now, act, d))
                if s >= 400 or s < 0: ERR.append((now, act, s))
        i += 1
def adm(stop):
    a = admin()
    while time.time() < stop:
        t = time.perf_counter(); s = a.get('attenzia_instantanes').status_code
        with lock:
            LAT.append((time.time(), 'atz_admin', (time.perf_counter() - t) * 1000))
            if s >= 400: ERR.append((time.time(), 'atz_admin', s))
        time.sleep(30)
def sample():
    mem = subprocess.run("free -m | sed -n 2p", shell=True, capture_output=True, text=True).stdout.split()
    con = subprocess.run(['mariadb', '-uroot', '-N', '-e', "show status like 'Threads_connected'"], capture_output=True, text=True).stdout.split()
    ap = subprocess.run("pgrep -c apache2", shell=True, capture_output=True, text=True).stdout.strip()
    la = open('/proc/loadavg').read().split()[0]
    return {'t': time.time(), 'mem_mo': int(mem[2]), 'mariadb_threads': int(con[-1]) if con else None, 'apache_proc': int(ap or 0), 'loadavg1': float(la)}
t0 = time.time(); stop = t0 + DUREE
th = [threading.Thread(target=scen, args=(pool[i], ids[i], stop)) for i in range(N)] + [threading.Thread(target=adm, args=(stop,))]
[t.start() for t in th]; S = []
while any(t.is_alive() for t in th): S.append(sample()); time.sleep(10)
dur = time.time() - t0
def q(v, p): v = sorted(v); return round(v[min(len(v) - 1, int(p * len(v)))], 1) if v else None
minutes = []
for m in range(int(dur // 60) + 1):
    lo, hi = t0 + 60 * m, t0 + 60 * (m + 1); L = [x[2] for x in LAT if lo <= x[0] < hi]; E = [x for x in ERR if lo <= x[0] < hi]; Sm = [s for s in S if lo <= s['t'] < hi]
    if L: minutes.append({'minute': m, 'requetes': len(L), 'debit_req_s': round(len(L) / 60, 1), 'p50_ms': q(L, .5), 'p95_ms': q(L, .95), 'p99_ms': q(L, .99), 'erreurs': len(E),
                          'mem_max_mo': max((s['mem_mo'] for s in Sm), default=None), 'mariadb_threads_max': max((s['mariadb_threads'] or 0 for s in Sm), default=None), 'loadavg_max': max((s['loadavg1'] for s in Sm), default=None)})
L = [x[2] for x in LAT]; W_ = [x[2] for x in LAT if x[1] == 'ecriture']
codes = {}; [codes.__setitem__(str(e[2]), codes.get(str(e[2]), 0) + 1) for e in ERR]
res = {'banc': 'Apache 2.4.58 prefork + mod_php 8.3.6 + MariaDB 10.11.14, HTTPS local, client sur la même machine (4 vCPU, 15 Go)', 'utilisateurs_simultanes': N, 'duree_s': round(dur, 1),
       'requetes': len(L), 'debit_req_s': round(len(L) / dur, 1), 'p50_ms': q(L, .5), 'p95_ms': q(L, .95), 'p99_ms': q(L, .99), 'max_ms': round(max(L), 1) if L else None, 'p95_ecriture_ms': q(W_, .95),
       'erreurs': len(ERR), 'taux_erreur': round(len(ERR) / max(1, len(L)), 5), 'codes_erreur': codes,
       'derive_p95_premiere_vs_derniere_minute_ms': [minutes[1]['p95_ms'] if len(minutes) > 2 else None, minutes[-2]['p95_ms'] if len(minutes) > 2 else None],
       'mem_max_mo': max(s['mem_mo'] for s in S), 'mariadb_threads_max': max(s['mariadb_threads'] or 0 for s in S), 'apache_proc_max': max(s['apache_proc'] for s in S), 'loadavg_max': max(s['loadavg1'] for s in S), 'par_minute': minutes}
json.dump(res, open(OUT, 'w'), ensure_ascii=False, indent=1); print(json.dumps({k: v for k, v in res.items() if k != 'par_minute'}, ensure_ascii=False))
