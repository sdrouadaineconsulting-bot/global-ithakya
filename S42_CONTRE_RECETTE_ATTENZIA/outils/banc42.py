"""S42 — harnais de contre-recette indépendante ATTENZIA (banc local Apache 2.4 / mod_php 8.3 / MariaDB 10.11, HTTPS 127.0.0.1:8443).
Faits de progression insérés en SQL = SIMULATION déclarée (périodes closes). Tout le calcul, le garde et la persistance passent par l'API réelle."""
import json, subprocess, secrets, datetime, requests, os, time
B = 'https://127.0.0.1:8443'; API = B + '/api/ithakya-pilote.php'; CA = '/etc/ssl/ithakya/c.pem'
CFG = '/var/www/ithakya/ithakya-pilote-prive/config.php'
HERE = os.path.dirname(os.path.abspath(__file__)); GEN = os.path.join(os.path.dirname(HERE), 'gen_config.php')
PW = 'Phrase-de-recette-S42-admin'; BOOT = 'b2' * 32
def sql(q, db='ithakya_banc'):
    return subprocess.run(['mariadb', '-uroot', '-N', '-B', db, '-e', q], capture_output=True, text=True, check=True).stdout.strip()
def config(env='local', **over):
    base = {'limites_recette': 50}; base.update(over)
    subprocess.run(['php', GEN, CFG, env, json.dumps(base)], check=True)
    subprocess.run(['chown', 'www-data', CFG], check=True); os.chmod(CFG, 0o600)
    subprocess.run(['apache2ctl', 'graceful'], capture_output=True); time.sleep(2.5)
class C:
    def __init__(s):
        s.s = requests.Session(); s.s.trust_env = False; s.s.verify = CA; s.csrf = None; s.get('session')
    def _c(s, r):
        try:
            j = r.json()
            if isinstance(j, dict) and j.get('csrf'): s.csrf = j['csrf']
        except Exception: pass
        return r
    def get(s, action, **p): return s._c(s.s.get(API, params={'action': action, **p}, timeout=60))
    def post(s, action, body):
        h = {'Origin': B, 'Content-Type': 'application/json'}
        if s.csrf: h['X-CSRF-Token'] = s.csrf
        return s._c(s.s.post(API, params={'action': action}, data=json.dumps(body), headers=h, timeout=60))
    def login(s, login, pw=PW):
        r = s.post('login', {'login': login, 'password': pw}); s.get('session'); return r
def admin(login='adm42', invitation=BOOT):
    c = C(); r = c.post('register', {'login': login, 'display_name': 'Admin S42', 'password': PW, 'invitation': invitation, 'avatar': 'ocean', 'interests': []})
    if r.status_code not in (200, 201): c.login(login)
    c.get('session'); return c
def member(login):
    c = C(); r = c.post('register', {'login': login, 'display_name': 'Membre S42', 'password': PW, 'avatar': 'ocean', 'interests': []})
    if r.status_code not in (200, 201): c.login(login)
    c.get('session'); return c
def reset_atz():
    """Nettoyage du banc : instantanés, journal, limites, progression et TOUS les comptes de recette (préfixe sx) avec leurs lignes dépendantes."""
    sub = "(SELECT id FROM itp_users WHERE login LIKE 'sx%')"
    q = ["SET FOREIGN_KEY_CHECKS=0"] + [f"DELETE FROM {t} WHERE user_id IN {sub}" for t in ('itp_entries', 'itp_progress', 'itp_thread_reads', 'itp_states', 'itp_recovery', 'itp_progress2', 'itp_reads', 'itp_work_progress')]
    q += ["DELETE FROM itp_reports WHERE reporter_id IN " + sub if False else "SELECT 1", "DELETE FROM itp_work_progress", "DELETE FROM itp_progress2", "DELETE FROM itp_limits", "DELETE FROM itp_users WHERE login LIKE 'sx%'", "SET FOREIGN_KEY_CHECKS=1"]
    sql(';'.join(q))
    for t in ('itp_atz_snapshots', 'itp_atz_audit', 'itp_atz_garde'):
        try: sql(f"DELETE FROM {t}")
        except subprocess.CalledProcessError: pass
    assert sql("SELECT COUNT(*) FROM itp_users WHERE login LIKE 'sx%'") == '0'
def ts(y, w, d=1, h=12): return int(datetime.datetime.fromisocalendar(y, w, d).replace(hour=h, tzinfo=datetime.timezone.utc).timestamp())
def seed(rows, prefix='sx'):
    """rows: liste de dict {steps:{...}, ctx, work, quiz, note_k, idea, t_maj, created}"""
    L = []
    for r in rows:
        uid = secrets.token_hex(16); d = {'steps': r.get('steps', {})}
        for k in ('quiz', 'note_k', 'idea', 'field_at_ms'):
            if k in r: d[k] = r[k]
        t = r.get('t_maj') or max([v for v in d['steps'].values()] + [r.get('created', 0) + 60])
        cr = r.get('created', t - 86400)
        L.append("INSERT INTO itp_users(id,login,display_name,password_hash,avatar,interests,role,created_at) VALUES('%s','%s%s','Recette','x','ocean','[]','member',%d)" % (uid, prefix, uid[:12], cr))
        L.append("INSERT INTO itp_work_progress(user_id,work_id,universe_id,data,updated_at) VALUES('%s','%s','%s','%s',%d)" % (uid, r.get('work', 'ith-pop-moment'), r.get('ctx', 'pop'), json.dumps(d), t))
    for i in range(0, len(L), 400): sql(';'.join(L[i:i + 400]))
def figer(adm, serie, cle):
    r = adm.post('attenzia_instantane_creer', {'serie': serie, 'cle': cle}); b = r.json() if r.headers.get('content-type', '').startswith('application/json') else {}
    return r.status_code, b
def lire(adm, i):
    r = adm.get('attenzia_instantane', id=i); return r.status_code, (r.json() if r.status_code == 200 else r.json())
