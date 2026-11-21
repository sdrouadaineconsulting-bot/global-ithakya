"""Contrôle de préservation des contenus entre deux candidates extraites (lecture seule).
Usage : python3 -I controle_contenus.py <dossier_A> <dossier_B> <sortie.json>
- médias (vidéo, image, sous-titres, polices) : empreinte SHA-256 identique exigée ;
- HTML : texte visible + attributs textuels (alt, title, aria-label, placeholder, content) identiques exigés ;
- JS : ensemble des chaînes littérales contenant au moins un mot (texte d'interface) comparé ;
- JSON : comparaison structurelle, clés techniques d'empreinte (source_sha256, sha, sha256) ignorées puis signalées ;
- CSS et autres : différences listées pour qualification."""
import sys, os, re, json, hashlib, html as H
A, B, OUT = sys.argv[1:4]
MEDIA = re.compile(r'\.(mp4|webm|m3u8|ts|mp3|m4a|ogg|wav|vtt|srt|jpg|jpeg|png|webp|avif|gif|svg|ico|woff2?|ttf|otf|pdf)$', re.I)
def files(r):
    out = {}
    for d, _, fs in os.walk(r):
        for f in fs:
            p = os.path.join(d, f); out[os.path.relpath(p, r)] = p
    return out
def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()
def visible(s):
    attrs = ' '.join(re.findall(r'\b(?:alt|title|aria-label|placeholder|content)="([^"]*)"', s))
    s = re.sub(r'(?is)<(script|style)[^>]*>.*?</\1>', ' ', s); s = re.sub(r'<[^>]+>', ' ', s)
    return re.sub(r'\s+', ' ', H.unescape(s + ' ' + attrs)).strip()
def chaines(s):
    lit = re.findall(r"'((?:[^'\\\n]|\\.){3,})'|\"((?:[^\"\\\n]|\\.){3,})\"|`((?:[^`\\]|\\.){3,})`", s)
    return {x for t in lit for x in t if x and re.search(r'[A-Za-zÀ-ÿ]{3,}\s+[A-Za-zÀ-ÿ]', x)}
TECH = {'source_sha256', 'sha', 'sha256', 'media_sha256', 'version'}
def norm(o, ign):
    if isinstance(o, dict): return {k: norm(v, ign) for k, v in o.items() if not (k in TECH and ign.append(k) is None)}
    if isinstance(o, list): return [norm(v, ign) for v in o]
    return o
fa, fb = files(A), files(B)
res = {'fichiers_A': len(fa), 'fichiers_B': len(fb), 'ajoutes': sorted(set(fb) - set(fa)), 'retires': sorted(set(fa) - set(fb)),
       'medias_total': sum(1 for f in fa if MEDIA.search(f)), 'medias_identiques': 0, 'medias_modifies': [],
       'html_modifies': [], 'js_modifies': [], 'json_modifies': [], 'autres_modifies': []}
for f in sorted(set(fa) & set(fb)):
    pa, pb = fa[f], fb[f]
    if MEDIA.search(f):
        if sha(pa) == sha(pb): res['medias_identiques'] += 1
        else: res['medias_modifies'].append(f)
        continue
    if sha(pa) == sha(pb): continue
    ta, tb = open(pa, encoding='utf-8', errors='replace').read(), open(pb, encoding='utf-8', errors='replace').read()
    if f.endswith('.html'):
        res['html_modifies'].append({'fichier': f, 'texte_visible_identique': visible(ta) == visible(tb)})
    elif f.endswith('.js'):
        ca, cb = chaines(ta), chaines(tb)
        res['js_modifies'].append({'fichier': f, 'chaines_retirees': sorted(ca - cb)[:10], 'chaines_ajoutees': sorted(cb - ca)[:10]})
    elif f.endswith('.json'):
        ign = []
        try: same = norm(json.loads(ta), ign) == norm(json.loads(tb), ign)
        except Exception as e: same = 'illisible: ' + str(e)[:60]
        res['json_modifies'].append({'fichier': f, 'identique_hors_empreintes': same, 'cles_techniques_ignorees': sorted(set(ign))})
    else:
        res['autres_modifies'].append(f)
json.dump(res, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps({k: (v if not isinstance(v, list) else len(v)) for k, v in res.items()}, ensure_ascii=False))
for k in ('html_modifies', 'js_modifies', 'json_modifies'):
    for x in res[k]: print(k, json.dumps(x, ensure_ascii=False)[:300])
print('autres :', res['autres_modifies'])
