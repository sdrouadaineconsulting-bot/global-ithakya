"""Comparaison au pixel C2 / C3, mêmes dimensions et états (captures.cjs). Usage : python3 -I diff_pixels.py <dossier_captures> <sortie.json>
Écart = part des pixels dont une composante diffère de plus de 16 niveaux. Une image de différence est écrite pour chaque écart."""
import sys, os, json
from PIL import Image, ImageChops
D, OUT = sys.argv[1], sys.argv[2]
a_dir, b_dir = os.path.join(D, 'C2'), os.path.join(D, 'C3'); diff_dir = os.path.join(D, 'diff'); os.makedirs(diff_dir, exist_ok=True)
res = {'comparees': 0, 'identiques': 0, 'differentes': [], 'manquantes_C2': [], 'manquantes_C3': []}
noms = sorted(set(os.listdir(a_dir)) | set(os.listdir(b_dir)))
for n in noms:
    pa, pb = os.path.join(a_dir, n), os.path.join(b_dir, n)
    if not os.path.exists(pa): res['manquantes_C2'].append(n); continue
    if not os.path.exists(pb): res['manquantes_C3'].append(n); continue
    A, B = Image.open(pa).convert('RGB'), Image.open(pb).convert('RGB'); res['comparees'] += 1
    if A.size != B.size: res['differentes'].append({'capture': n, 'motif': f'taille {A.size} / {B.size}'}); continue
    d = ImageChops.difference(A, B)
    if not d.getbbox(): res['identiques'] += 1; continue
    m = d.convert('L').point(lambda v: 255 if v > 16 else 0)
    px = sum(1 for v in m.getdata() if v); part = px / (A.size[0] * A.size[1])
    if px == 0: res['identiques'] += 1; continue
    m.save(os.path.join(diff_dir, n))
    res['differentes'].append({'capture': n, 'pixels': px, 'part_pct': round(100 * part, 4), 'zone': m.getbbox()})
json.dump(res, open(OUT, 'w'), ensure_ascii=False, indent=1)
print({k: (v if not isinstance(v, list) else len(v)) for k, v in res.items()})
for x in res['differentes']: print(x)
