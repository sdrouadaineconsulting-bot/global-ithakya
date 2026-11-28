"""Régénère, à partir de 07_outils/oeuvres.json et des qualifications ffprobe présentes :
06_manifeste/manifeste.json, qualification.csv, RAPPORT_MANQUANTS.md,
05_editorial/<ID>.md, 05_editorial/<ID>.quiz.json, 05_editorial/socle_univers.json.
Toute valeur mesurée vient de ffprobe ; sinon la valeur déclarée par la source est reprise et marquée « source »."""
import csv, glob, hashlib, json, os
from fractions import Fraction

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
J = lambda *p: os.path.join(ROOT, *p)
DATA = json.load(open(J('07_outils', 'oeuvres.json'), encoding='utf-8'))
COMMUNITY_RATIO = 0.50   # ATTENZIA_METRICS_POLICY.communityMinCompletionRatio du socle V4.9


def tc(sec, fps=None):
    if fps:
        fr = round(sec * fps); f = fr % round(fps); s = int(fr // round(fps))
        return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}:{f:02d}"
    s = int(round(sec)); return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"


def mesure(oid):
    p = J('06_manifeste', 'ffprobe', f'{oid}.json')
    if not os.path.exists(p):
        return None
    d = json.load(open(p)); fmt = d['format']
    v = next(s for s in d['streams'] if s['codec_type'] == 'video')
    au = [s for s in d['streams'] if s['codec_type'] == 'audio']
    st = [s for s in d['streams'] if s['codec_type'] == 'subtitle']
    fps = Fraction(v.get('avg_frame_rate') or v['r_frame_rate'])
    frames = int(v.get('nb_read_packets') or v.get('nb_frames') or 0)
    sha = open(J('06_manifeste', 'sha256', f'{oid}.sha256')).read().split()[0]
    return {
        'fichier': os.path.basename(fmt['filename']), 'conteneur': fmt.get('format_name'),
        'duree_s': float(fmt['duration']), 'images': frames, 'cadence': f"{float(fps):.3f}",
        'duree_tc': tc(frames / float(fps), float(fps)) if frames and fps else tc(float(fmt['duration'])),
        'resolution': f"{v['width']}x{v['height']}", 'rapport_affichage': v.get('display_aspect_ratio'),
        'codec_video': f"{v['codec_name']} {v.get('profile', '')}".strip(), 'pix_fmt': v.get('pix_fmt'),
        'codec_audio': ', '.join(f"{a['codec_name']} {a.get('channels', '?')} can. {a.get('sample_rate', '?')} Hz" for a in au) or 'aucun',
        'langues_audio': [a.get('tags', {}).get('language', 'und') for a in au],
        'sous_titres_internes': [s.get('tags', {}).get('language', 'und') for s in st],
        'debit_kbps': round(int(fmt.get('bit_rate', 0)) / 1000), 'poids_octets': int(fmt['size']), 'sha256': sha,
    }


def declinaisons(oid):
    d = J('02_declinaisons', oid); a = J('03_affiches_miniatures', oid)
    rel = lambda p: os.path.relpath(p, ROOT)
    rep = J('02_declinaisons', oid, f'{oid}_repli.mp4')
    out = {
        'mp4_repli': rel(rep) if os.path.exists(rep) else None,
        'hls_master': rel(J(d, 'hls', 'master.m3u8')) if os.path.exists(J(d, 'hls', 'master.m3u8')) else None,
        'webvtt': [rel(p) for p in sorted(glob.glob(J('04_sous_titres', f'{oid}.*.vtt')))],
        'affiche': rel(J(a, 'affiche.jpg')) if os.path.exists(J(a, 'affiche.jpg')) else None,
        'affiche_dynamique': rel(J(a, 'affiche_dynamique.mp4')) if os.path.exists(J(a, 'affiche_dynamique.mp4')) else None,
        'miniatures': [rel(p) for p in sorted(glob.glob(J(a, 'miniature_*.jpg')))],
    }
    # nom de fichier au format du socle (../assets/video/<20 hex>.mp4) : 20 premiers caractères du SHA-256 du MP4 de repli
    out['socle_fichier'] = (hashlib.sha256(open(rep, 'rb').read()).hexdigest()[:20] + '.mp4') if os.path.exists(rep) else None
    return out


rows, man, manquants = [], [], []
for o in DATA['oeuvres']:
    m = mesure(o['id']); dc = declinaisons(o['id'])
    statut = 'qualifié' if m else o['statut_master']
    duree = m['duree_s'] if m else o['duree_source_s']
    entry = {k: o[k] for k in ('id', 'univers_socle', 'format', 'titre_exact', 'titre_programme', 'createur', 'credits',
                               'url_source', 'plateforme', 'date_publication', 'langue_originale', 'mecanisme_telechargement')}
    entry.update({
        'statut_master': statut, 'master': m, 'declinaisons': dc,
        'source_declare': {'duree_s': o['duree_source_s'], 'resolution': o['resolution_source'],
                           'note': o.get('duree_source_note'), 'sous_titres': o['sous_titres_source']},
        'attenzia': {'editorialDurationSec': round(duree, 3), 'communityThresholdSec': round(duree * COMMUNITY_RATIO, 3),
                     'origine_duree': 'mesure ffprobe' if m else 'déclarée par la source'},
        'note_k': {'collecte': 'après le Court, dans le flux Court → Note K → Long du socle' if o['format'] == 'Court' else 'non collectée sur ce format dans le flux du socle',
                   'statut': 'signal éditorial uniquement, découplé de l’XP, des Points et des récompenses (RM-03 / SOC-02)'},
        'passerelle': o.get('passerelle'), 'mots_cles': o['mots_cles'],
    })
    if 'grande_traversee' in o:
        entry['grande_traversee'] = o['grande_traversee']
    man.append(entry)
    rows.append({
        'ID': o['id'], 'Univers': o['univers_socle'], 'Format': o['format'], 'Titre exact': o['titre_exact'],
        'Crédits': ' ; '.join(o['credits']), 'Publication': o['date_publication'],
        'Durée': (f"{m['duree_tc']} ({m['images']} images à {m['cadence']} i/s, {m['duree_s']:.3f} s, mesure)" if m else f"{tc(o['duree_source_s'])} ({o['duree_source_s']} s, source)"),
        'Résolution native': m['resolution'] if m else f"{o['resolution_source']} (source)",
        'Cadence': m['cadence'] if m else 'non mesurée', 'Codec vidéo': m['codec_video'] if m else 'non mesuré',
        'Codec audio': m['codec_audio'] if m else 'non mesuré', 'Débit (kbit/s)': m['debit_kbps'] if m else 'non mesuré',
        'Poids (octets)': m['poids_octets'] if m else 'non mesuré', 'Langue originale': o['langue_originale'],
        'Pistes audio': ', '.join(m['langues_audio']) if m else 'non mesurées',
        'Sous-titres': ' ; '.join(f"{s['langue']} ({s['type']})" for s in o['sous_titres_source']) or 'aucun publié',
        'SHA-256': m['sha256'] if m else 'sans objet (master absent)',
        'Provenance': f"{o['plateforme']} · {o['url_source']} · {o['mecanisme_telechargement']}", 'Statut master': statut,
    })
    if not m:
        manquants.append(o)

os.makedirs(J('06_manifeste'), exist_ok=True)
json.dump({'paquet': 'ITHAKYA_PREMIUM_W360_PACK_AUDIOVISUEL_7_OEUVRES_20261128', 'date': '2026-11-28',
           'oeuvres': man, 'createurs': DATA['createurs']}, open(J('06_manifeste', 'manifeste.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=2)
with open(J('06_manifeste', 'qualification.csv'), 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter=';'); w.writeheader(); w.writerows(rows)

with open(J('06_manifeste', 'RAPPORT_MANQUANTS.md'), 'w', encoding='utf-8') as f:
    f.write(f"# Rapport des fichiers manquants\n\n{len(manquants)} master(s) manquant(s) sur {len(DATA['oeuvres'])}.\n\n")
    f.write("| ID | Œuvre | Mécanisme proposé par la source | Cause | Action |\n|---|---|---|---|---|\n")
    for o in manquants:
        f.write(f"| {o['id']} | {o['titre_programme']} | {o['mecanisme_telechargement']} | {o['cause_manquant']} | "
                f"Déposer le fichier dans `01_masters/{o['id']}.<ext>` puis lancer `sh 07_outils/preparer.sh {o['id']}` |\n")
    f.write("\nAucune œuvre substituée. Aucun remontage. Les déclinaisons, affiches, miniatures, empreintes SHA-256 et "
            "mesures ffprobe de ces œuvres seront produites par `07_outils/preparer.sh` dès réception des fichiers.\n")

# Fiches éditoriales + quiz
os.makedirs(J('05_editorial'), exist_ok=True)
byid = {o['id']: o for o in DATA['oeuvres']}
for o in DATA['oeuvres']:
    c = DATA['createurs'].get(o['createur'], {})
    p = o.get('passerelle', {})
    lien = byid.get(p.get('vers') or p.get('depuis'), {}).get('titre_programme')
    md = [f"# {o['titre_programme']}", "",
          f"**{o['format']}** · {o['univers_socle']} · {o['createur']} · publié le {o['date_publication']} · "
          f"{tc(o['duree_source_s'])} (durée source) · [source]({o['url_source']})", "",
          "## Synopsis", "", o['synopsis'], "",
          "## Crédits", ""] + [f"- {x}" for x in o['credits']] + ["",
          "## Profil du créateur", "", c.get('profil', 'Non renseigné.'), ""] + \
         ([f"Incertitude : {c['incertitude']}", ""] if c.get('incertitude') else []) + \
         ["Sources : " + ", ".join(f"[{i + 1}]({u})" for i, u in enumerate(c.get('sources', []))), "",
          "## Repères de découverte", ""] + [f"- {x}" for x in o['reperes']] + ["",
          "## Passerelle", "", (f"{'Vers' if p.get('vers') else 'Depuis'} : **{lien}**. " if lien else "") + p.get('texte', ''), "",
          "## Quiz", ""]
    for k, q in o['quiz'].items():
        md += [f"**{'Défi rapide' if k == 'quick' else 'Défi communauté'}** — {q['question']}", ""]
        md += [f"- {'✔ ' if key == q['correct'] else ''}{lab}" for key, lab in q['options']]
        md += ["", f"_{q['explanation']}_", ""]
    md += ["## Recherche et programmation", "", "Mots-clés : " + ", ".join(o['mots_cles']),
           f"Langue originale : {o['langue_originale']} · Dialogue : {o['dialogue']}",
           "Sous-titres publiés par la source : " + (' ; '.join(f"{s['langue']} ({s['type']}) → {s['repris']}" for s in o['sous_titres_source']) or 'aucun'), ""]
    if o.get('versions_linguistiques_signalees'):
        md += [f"Versions linguistiques : {o['versions_linguistiques_signalees']}", ""]
    if 'grande_traversee' in o:
        g = o['grande_traversee']
        md += ["## La Grande Traversée", "", f"Fonctionnement : {g['fonctionnement']}.", "", f"Cinq personnages : {g['cinq_personnages']}", ""]
    open(J('05_editorial', f"{o['id']}.md"), 'w', encoding='utf-8').write('\n'.join(md))
    json.dump(o['quiz'], open(J('05_editorial', f"{o['id']}.quiz.json"), 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

# Données au format des univers du socle (lecture seule du socle : rien n'y est écrit)
ini = lambda n: ''.join(w[0] for w in n.replace('-', ' ').split()[:2]).upper()
socle = {}
for u in ('Sciences & Tech', 'Sport & Aventure', 'Pop Culture & Divertissement'):
    co = next(o for o in DATA['oeuvres'] if o['univers_socle'] == u and o['format'] == 'Court')
    lo = next(o for o in DATA['oeuvres'] if o['univers_socle'] == u and o['format'] == 'Long')
    dlab = lambda s: f"{round(s / 60)} min" if s >= 90 else f"{s} s"
    socle[u] = {
        'court': co['titre_programme'], 'long': lo['titre_programme'],
        'items': [[co['titre_programme'], 'Court', dlab(co['duree_source_s']), ini(co['createur']), co['createur'], u, 'Programmation W360'],
                  [lo['titre_programme'], 'Long', dlab(lo['duree_source_s']), ini(lo['createur']), lo['createur'], u, 'Programmation W360']],
        'lead': {'initials': ini(co['createur']), 'name': co['createur'], 'role': co['credits'][0], 'summary': co['passerelle']['texte']},
        'quiz': {'quick': co['quiz']['quick'], 'community': lo['quiz']['community']},
        'media': {'court': (f"../assets/video/{declinaisons(co['id'])['socle_fichier']}" if declinaisons(co['id'])['socle_fichier'] else None),
                  'long': (f"../assets/video/{declinaisons(lo['id'])['socle_fichier']}" if declinaisons(lo['id'])['socle_fichier'] else None)},
    }
json.dump({'_doc': "Champs alignés sur les objets d'univers et ITHAKYA_MEDIA_LIBRARY de la démo 07 (V4.9). 'media' reste null tant que le MP4 de repli n'est pas produit. Les clés 'icon', 'accent' et 'bg' du socle ne sont pas fournies (choix de design).",
           'univers': socle, 'grande_traversee': next(m for m in man if m['id'] == 'W360-GT-FILM')},
          open(J('05_editorial', 'socle_univers.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(f"manifeste : {len(man)} œuvres, {len(man) - len(manquants)} qualifiée(s), {len(manquants)} manquante(s)")
