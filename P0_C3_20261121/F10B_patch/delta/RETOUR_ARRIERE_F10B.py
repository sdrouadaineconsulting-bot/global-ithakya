"""Delta C2 <-> C3 (W360, 21/11/2026). Usage : python3 -I RETOUR_ARRIERE_C3.py <dossier_candidate> vers-c2|vers-c3
Remplace uniquement les fichiers listés dans DELTA_C2_C3.json après contrôle de l'empreinte de départ ; refuse sinon."""
import json, hashlib, shutil, sys, os
ici = os.path.dirname(os.path.abspath(__file__)); cible, sens = sys.argv[1], sys.argv[2]
d = json.load(open(os.path.join(ici, 'DELTA_C2_C3.json'), encoding='utf8'))
src, dep, arr = ('avant', 'apres', 'avant') if sens == 'vers-c2' else ('apres', 'avant', 'apres')
h = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
for e in d['fichiers']:
    p = os.path.join(cible, e['fichier']); a = h(p)
    if a not in (e[dep], e[arr]): sys.exit('Empreinte de départ inattendue : ' + e['fichier'])
for e in d['fichiers']:
    shutil.copy2(os.path.join(ici, src, e['fichier']), os.path.join(cible, e['fichier']))
    assert h(os.path.join(cible, e['fichier'])) == e[arr], e['fichier']
print(f"{len(d['fichiers'])} fichiers remis à l'état {'C2' if sens == 'vers-c2' else 'C3'}")
