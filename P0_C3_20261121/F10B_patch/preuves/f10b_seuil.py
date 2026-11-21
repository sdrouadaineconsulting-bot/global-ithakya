"""F10B-1 : preuve du plafond de débit (seuil 1/h) + revue administrateur (confirmer, annuler). MariaDB.
Usage : python3 -I f10b_seuil.py <base> <dossier_mires> <invitation_admin> <sortie.json>"""
import sys, json, secrets, time
BASE_ARG, MIRES, INVIT, OUTF = sys.argv[1:5]
sys.argv = [sys.argv[0], BASE_ARG]
exec(open(__file__.rsplit('/', 1)[0] + '/f10b.py').read().split('if __name__ == "__main__":')[0])
fr = frames(MIRES + '/court21.mp4'); R = {}

def lire(c, content, ctx):
    c.progress('court_started', context=ctx); c.media(content)
    play_clock(c, content, fr, 21000)
    st, js = c.progress('court_finished', {'coverage': 1}, context=ctx)
    rev = ((js.get('progress') or {}).get('credit_review') or {}).get('court_finished') or {}
    return st, rev.get('status'), js.get('error')

u = Client().register('rate' + secrets.token_hex(3))
R['lecture_1'] = dict(zip(('http', 'statut', 'erreur'), lire(u, 'signature.court', 'signature'))); R['score_1'] = u.score()
R['lecture_2'] = dict(zip(('http', 'statut', 'erreur'), lire(u, 'progression.court', 'progression'))); R['score_2'] = u.score()

adm = Client(); adm.call('session')
st, js = adm.call('register', {'login': 'adm' + secrets.token_hex(3), 'display_name': 'Admin banc', 'password': 'phrase de passe admin banc ' + secrets.token_hex(4), 'invitation': INVIT})
adm.user = js.get('user'); R['admin'] = {'http': st, 'role': (adm.user or {}).get('role')}
st, js = adm.call('lecture_reviews', extra='&page=1')
items = [i for i in js.get('items', []) if i['member_id'] == u.user['id']]
R['revues_visibles'] = [(i['oeuvre'], i['event'], i['review']['status'], i['review'].get('risks')) for i in items]

def decider(item, decision):
    rv = item['review']
    return adm.call('lecture_decide', {'owner_id': adm.user['id'], 'member_id': u.user['id'], 'oeuvre': item['oeuvre'], 'event': item['event'],
        'review_key': rv['key'], 'expected_revision': rv['revision'], 'decision_key': secrets.token_hex(16), 'decision': decision,
        'proof_ref': 'banc-F10B-1', 'reason': 'Revue de banc du plafond de débit F10B-1'})

pend = next((i for i in items if i['review']['status'] == 'pending'), None)
conf = next((i for i in items if i['review']['status'] == 'confirmed'), None)
if pend:
    st, js = decider(pend, 'confirmed'); R['confirmation_admin'] = {'http': st, 'erreur': js.get('error')}; R['score_apres_confirmation'] = u.score()
if conf:
    st, js = decider(conf, 'cancelled'); R['annulation_admin'] = {'http': st, 'erreur': js.get('error')}; R['score_apres_annulation'] = u.score()
v = Client().register('vis' + secrets.token_hex(3))
st, js = v.call('lecture_reviews', extra='&page=1'); R['membre_non_admin_revues'] = {'http': st, 'erreur': js.get('error')}
R['verdict'] = ('CONFORME' if R['lecture_1']['statut'] == 'confirmed' and R['lecture_2']['statut'] == 'pending' and R['lecture_2']['http'] == 200
    and R['score_2'][0] == 5 and R.get('score_apres_confirmation', (0,))[0] == 10 and R.get('score_apres_annulation', (0,))[0] == 5
    and R['membre_non_admin_revues']['http'] == 403 else 'ECART')
json.dump(R, open(OUTF, 'w'), ensure_ascii=False, indent=1); print(json.dumps(R, ensure_ascii=False))
