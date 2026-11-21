#!/usr/bin/env python3
"""RF-14 / RF-18 — Génération reproductible des pages publiées à partir de la source commune.

Usage : python3 generer.py <dossier source> <dossier site> [--verifier]

Source :
  gabarit/univers.html        gabarit commun des quatre univers membres
  gabarit/socle/*.html        parties partagées par Signature, Progression et Soleil XL
  univers/<id>.json           variantes explicites de chaque univers (emplacements) + chemin publié
  composants/*.html           composants partagés insérés par {{> composant/nom}} (en-tête, pied, états…)
  pages/*.html                pages globales (Une, Mon ITHAKYA, Communauté, Lounge, Univers…) — chemin publié = nom
  catalogue/catalogue.json    catalogue membre (RF-19), publié tel quel en assets/data/catalogue.json
Marqueurs : {{> nom}} (emplacement de l'univers, ou socle/…, composant/…), {{univers}} (identifiant de l'univers
  courant), {{racine}} (préfixe relatif vers la racine du site : '' ou '../').
Après génération, les références ?sha= des CSS/JS sont recalculées (cache navigateur).
--verifier : n'écrit rien ; compare la génération aux fichiers publiés et liste les différences (code 1 si écart).
"""
import hashlib, html, json, os, re, sys, glob

MARQ = re.compile(r'\{\{>(\??) ([^}]+)\}\}')


def lire(p):
    with open(p, encoding='utf8') as fichier:
        return fichier.read()


class Source:
    def __init__(self, src):
        self.src = src
        self.composants = {os.path.splitext(os.path.basename(p))[0]: lire(p) for p in glob.glob(os.path.join(src, 'composants', '*.html'))}

    def resoudre(self, texte, valeurs, contexte, pile=()):
        def rempl(m):
            optionnel = m.group(1) == '?'
            morceaux = m.group(2).strip().split()
            nom, params = morceaux[0], dict(x.split('=', 1) for x in morceaux[1:])
            if nom in pile:
                raise SystemExit(f'boucle d’inclusion : {" > ".join(pile + (nom,))}')
            ctx = contexte
            if nom.startswith('socle/'):
                v = lire(os.path.join(self.src, 'gabarit', 'socle', nom[6:] + '.html'))
            elif nom.startswith('gabarit/'):
                v = lire(os.path.join(self.src, 'gabarit', nom[8:] + '.html'))
            elif nom.startswith('composant/'):
                if nom[10:] not in self.composants:
                    raise SystemExit(f'composant absent : {nom}')
                v = self.composants[nom[10:]]
                ctx = dict(contexte, **params)
                # {{>? suite}} : partie de gabarit désignée par le paramètre suite=…, sinon rien.
                v = v.replace('{{>? suite}}', '{{> gabarit/' + params['suite'] + '}}' if params.get('suite') else '')
                # {{courant-x}} : attribut aria-current sur la destination active du composant.
                v = re.sub(r'\{\{courant-([a-z0-9-]+)\}\}', lambda c: ' aria-current="page"' if params.get('actif') == c.group(1) else '', v)
                # Paramètre non fourni : valeur vide.
                v = re.sub(r'\{\{([a-z][a-z0-9-]*)\}\}', lambda c: c.group(0) if c.group(1) in ctx else '', v)
            else:
                if nom not in valeurs:
                    if optionnel:
                        return ''
                    raise SystemExit(f'emplacement sans valeur pour {contexte.get("univers")} : {nom}')
                v = valeurs[nom]
            return self.resoudre(v, valeurs, ctx, pile + (nom,))
        out = MARQ.sub(rempl, texte)
        for k, v in contexte.items():
            out = out.replace('{{' + k + '}}', v)
        return out


BOUCLE = re.compile(r'\{\{#each ([a-z_]+)((?: [a-z_.]+=[^ }]+)*)\}\}(.*?)\{\{/each\}\}', re.S)
SI = re.compile(r'\{\{#(if|sinon) \.([a-z_.]+)\}\}(.*?)\{\{/\1\}\}', re.S)
CHAMP = re.compile(r'\{\{\.([a-z_.]+)\}\}')


def valeur(item, chemin):
    for k in chemin.split('.'):
        item = item.get(k) if isinstance(item, dict) else None
    return item


def donnees(texte, cat):
    """Boucles simples sur le catalogue : {{#each contenus type=programme univers=pop}}…{{/each}} ; dans le corps,
    {{.champ}} (échappé HTML), {{#if .champ}}…{{/if}}, {{#sinon .champ}}…{{/sinon}}. Une valeur de filtre peut lister
    plusieurs choix séparés par des virgules ; « - » désigne l'absence de valeur."""
    def rendre(item, corps):
        corps = SI.sub(lambda m: m.group(3) if bool(valeur(item, m.group(2))) == (m.group(1) == 'if') else '', corps)
        return CHAMP.sub(lambda m: html.escape(str(valeur(item, m.group(1)) if valeur(item, m.group(1)) is not None else ''), quote=True), corps)
    def boucle(m):
        liste = cat.get(m.group(1), [])
        filtres = [f.split('=', 1) for f in m.group(2).split()]
        def garde(it):
            for k, v in filtres:
                val = valeur(it, k)
                choix = v.split(',')
                if (val is None and '-' not in choix) or (val is not None and str(val) not in choix):
                    return False
            return True
        return ''.join(rendre(it, m.group(3)) for it in liste if garde(it))
    return BOUCLE.sub(boucle, texte)


def media_dans_paquet(site, chemin):
    """Vérifie seulement les fichiers de CE paquet, jamais leur disponibilité distante.

    Les chemins sont relatifs à site/ ; pas de suivi de chemin absolu ou traversant.
    """
    if not chemin or not isinstance(chemin, str):
        return False
    normalise = os.path.normpath(chemin.replace('\\', '/'))
    if normalise.startswith('../') or normalise == '..' or os.path.isabs(normalise):
        return False
    racine = os.path.realpath(site)
    cible = os.path.realpath(os.path.join(racine, normalise))
    return cible.startswith(racine + os.sep) and os.path.isfile(cible)



def media_disponible(site, contenu):
    """Recette privée R4 : fichier référencé présent, sans dossier d'autorisation.

    Ne vérifie ni droits de diffusion ni qualité/décodage du média. La validation
    juridique et éditoriale relève d'une étape distincte avant publication.
    """
    return isinstance(contenu, dict) and media_dans_paquet(site, contenu.get('media'))


LIBELLE_CONTEXTE = {'signature': 'Sciences & Tech', 'soleil': 'Sciences & Tech · Le courant', 'progression': 'Sport & Aventure', 'pop': 'Pop Culture', 'culture': 'Culture & Création', 'societe': 'Société & Impact'}


def enrichir(cat, site=None):
    """Champs d'affichage dérivés du catalogue (préfixe _), calculés à la génération : la source reste sans doublon."""
    noms = {u['id']: u for u in cat.get('univers', [])}
    def duree(c):
        if c.get('duree_s'):
            d = int(round(c['duree_s'])); return f'{d} s' if d < 90 else f'{d // 60} min' + (f' {d % 60:02d}' if d % 60 else '')  # L20 : arrondi à la seconde
        if c.get('duree_envisagee_min'):
            return f"format envisagé · {c['duree_envisagee_min']} min"
        return ''
    for c in cat.get('contenus', []):
        u = noms.get(c.get('univers')) or {}
        # S3 : le libellé affiché est celui du territoire de l'œuvre historique (Signature, Progression, Soleil XL ne sont plus des univers principaux)
        c['_univers_nom'] = LIBELLE_CONTEXTE.get(c.get('univers')) or u.get('nom', 'ITHAKYA'); c['_devise'] = u.get('devise', '')
        c['_duree'] = duree(c)
        t, st = c.get('type'), c.get('statut')
        if st == 'indisponible':
            c['_statut'], c['_statut_libelle'], c['_action'] = 'indisponible', 'Temporairement indisponible', ''
        elif st == 'projet':
            # Respecter la suspension d'une ressource, y compris quand il s'agit d'un teaser.
            c['_statut'], c['_statut_libelle'], c['_action'] = 'projet', c.get('statut_libelle') or 'Projet éditorial', ''
        elif t == 'programme':
            c['_statut'], c['_statut_libelle'], c['_action'] = 'projet', 'Projet éditorial', ''
        elif t == 'extrait':
            dossier = 'dossier' in (c.get('sous_type') or '')
            c['_statut'] = 'dossier' if dossier else 'extrait'
            c['_statut_libelle'] = 'Dossier consultable · extrait de ' + c['_duree'] if dossier else 'Extrait disponible'
            c['_action'] = ('Ouvrir le dossier et l’extrait · ' if dossier else 'Lire l’extrait · ') + c['_duree']
        elif t == 'court':
            c['_statut'], c['_statut_libelle'], c['_action'] = 'disponible', 'Film disponible', 'Lancer le Court · ' + c['_duree']
        elif t == 'long':
            c['_statut'], c['_statut_libelle'], c['_action'] = 'disponible', 'Film disponible', 'Voir le Long · ' + c['_duree']
        else:
            c['_statut'], c['_statut_libelle'], c['_action'] = 'disponible', 'Film disponible', 'Voir · ' + c['_duree']
        # Statut éditorial déclaré ≠ présence physique d'un MP4.
        # Aucun justificatif additionnel requis pour les essais privés.
        # Les fiches restent consultables même sans fichier vidéo. Ne jamais promettre une lecture absente.
        media = c.get('media')
        present = media_disponible(site, c) if site else None
        c['_media_etat'] = ('present_dans_paquet' if present else 'absent_du_paquet') if media else 'sans_media'
        if media and present is False and st not in ('indisponible', 'projet'):
            c['_statut'] = 'media_manquant'
            c['_statut_libelle'] = 'Fiche consultable · vidéo non disponible'
            c['_action'] = 'Consulter la fiche · ' + c['_duree']
        # Fluidité UX360 R2 : lorsqu'un film historique manque physiquement,
        # le bouton « consulter la fiche » va VRAIMENT à la fiche (et non dans
        # un lecteur historique inactif). Le chemin original reste au catalogue.
        historique = c.get('oeuvre') or c.get('univers')
        fiche = ('oeuvres/' + historique + '.html#formats') if historique in ('signature', 'pop', 'progression', 'soleil') else ''
        c['_lien'] = fiche if t in ('court', 'long') and media and present is False and fiche else (c.get('page') or '')
        if t in ('court', 'long') and media and present is False and fiche and st not in ('indisponible','projet'):
            c['_action'] = 'Consulter la fiche'
        long = next((x for x in cat['contenus'] if x['id'] == f"{historique}.long"), None)  # M2 : Long de la même œuvre
        c['_long_lien'] = ((fiche if fiche and long and long.get('media') and not media_disponible(site, long) else long.get('page','')) if long else '')
    for u in cat.get('univers', []):
        court = next((c for c in cat['contenus'] if c['id'] == u['id'] + '.court'), {})
        u['_court_duree'] = court.get('_duree', ''); u['_court_lien'] = court.get('page', '')
    # S1 : champs d'affichage des cinq territoires (accueil et page « Les univers »)
    for x in cat.get('territoires', []):
        mes = sorted([w for w in cat.get('oeuvres', []) if x['id'] in (w.get('territoires') or []) and w.get('statut') != 'retiree'], key=lambda y: (not y.get('historique'), y.get('ordre', 99)))
        x['_nb'] = len(mes); x['_oeuvres_libelle'] = ('1 œuvre' if len(mes) == 1 else f'{len(mes)} œuvres') if mes else 'Programmation en préparation'
        vedette = next((w for w in mes if w.get('historique')), None)
        court = next((c for c in cat['contenus'] if vedette and c['id'] == vedette['univers'] + '.court'), {})
        x['_court_duree'] = court.get('_duree', '')
        x['_vedette'] = vedette['titre'] if vedette else ''
        # UX360 : si la vidéo n'est pas livrée, accéder directement à la fiche
        # plutôt que faire transiter le visiteur par un ancien lecteur inactif.
        fichier_present = bool(court and court.get('media') and media_disponible(site, court))
        x['_court_lien'] = (court.get('page', '') if fichier_present else
                           'oeuvres/' + vedette['univers'] + '.html#formats' if vedette else '')
        x['_court_action'] = (('Voir le Court · ' + x['_vedette'] + ' · ' + x['_court_duree']) if fichier_present else
                              ('Formats et repères · ' + x['_vedette'] if vedette else ''))
    return cat


def empreintes(site, textes):
    """Recalcule ?sha= pour chaque CSS/JS du site référencé dans les pages générées."""
    h = {}
    for a in glob.glob(os.path.join(site, 'assets', '**', '*.*'), recursive=True):
        if a.endswith(('.js', '.css', '.json')):
            h[os.path.basename(a)] = hashlib.sha256(open(a, 'rb').read()).hexdigest()[:12]
    def rempl(m):
        return m.group(1) + '?sha=' + h.get(m.group(1), m.group(2))
    return {p: re.sub(r'([A-Za-z0-9._-]+\.(?:js|css|json))\?sha=([A-Za-z0-9-]+)', lambda m: rempl(m) if os.path.basename(m.group(1)) in h else m.group(0), t) for p, t in textes.items()}


BLOC_STYLE = re.compile(r'<style((?:\s+[a-z-]+(?:="[^"]*")?)*)>(.*?)</style>', re.S)
BLOC_SCRIPT = re.compile(r'<script((?:\s+[a-z-]+(?:="[^"]*")?)*)>(.*?)</script>', re.S)


def externaliser(pages, site):
    """RF-87 — Les blocs <style> et <script> identiques dans au moins deux pages d'univers deviennent des fichiers communs
    (assets/gabarit/<nature>-<empreinte>), mis en cache une fois pour tous les univers. Ordre et position conservés ;
    les blocs de données (type application/json) restent dans la page ; les url() relatives des feuilles sont recalculées."""
    fichiers = {}
    def compte(rx):
        n = {}
        for t in pages.values():
            for m in rx.finditer(t):
                n[m.group(2)] = n.get(m.group(2), 0) + 1
        return n
    n_style, n_script = compte(BLOC_STYLE), compte(BLOC_SCRIPT)
    def url_css(css):
        def r(m):
            u = m.group(2)
            if re.match(r'^(data:|https?:|/|#)', u): return m.group(0)
            return 'url(' + m.group(1) + '../../' + (u[3:] if u.startswith('../') else 'demos/' + u) + m.group(1) + ')'
        return re.sub(r'url\((["\']?)([^)"\']+)\1\)', r, css)
    def style(m):
        attrs, css = m.group(1), m.group(2)
        if n_style.get(css, 0) < 2 or len(css) < 400: return m.group(0)
        nom = 'style-' + hashlib.sha256(css.encode()).hexdigest()[:12] + '.css'
        fichiers['assets/gabarit/' + nom] = url_css(css)
        ident = re.search(r'\sid="[^"]*"', attrs)
        return '<link rel="stylesheet"' + (ident.group(0) if ident else '') + ' href="../assets/gabarit/' + nom + '">'
    def script(m):
        attrs, js = m.group(1), m.group(2)
        if 'src=' in attrs or ('type=' in attrs and 'javascript' not in attrs and 'module' not in attrs): return m.group(0)
        if n_script.get(js, 0) < 2 or len(js) < 400: return m.group(0)
        nom = 'script-' + hashlib.sha256(js.encode()).hexdigest()[:12] + '.js'
        fichiers['assets/gabarit/' + nom] = js
        return '<script' + attrs + ' src="../assets/gabarit/' + nom + '"></script>'
    sortie = {p: BLOC_SCRIPT.sub(script, BLOC_STYLE.sub(style, t)) for p, t in pages.items()}
    return sortie, fichiers



def optimiser_images_lecteurs(pages):
    """R6 — Chargement différé discret des images secondaires des quatre parcours
    historiques. Ne touche ni aux cinq premières images, ni aux images prioritaires,
    ni aux scripts, lecteurs, commandes, identifiants, chemins ou états membres.
    On évite une refonte/réduction des modules au nom de la seule volumétrie JS.
    """
    pages = dict(pages)
    for chemin in ('demos/01-signature.html', 'demos/02-pop-culture.html',
                   'demos/03-progression.html', 'demos/05-soleil-xl.html'):
        page = pages.get(chemin)
        if page is None: continue
        rang = 0
        def optimiser(m):
            nonlocal rang
            rang += 1
            balise = m.group(0)
            if rang <= 5 or 'loading=' in balise or re.search(r'fetchpriority\s*=\s*["\']high', balise, re.I):
                return balise
            fin = balise.rfind('>')
            suffixe = ' loading="lazy"' + ('' if 'decoding=' in balise else ' decoding="async"')
            return balise[:fin] + suffixe + balise[fin:]
        pages[chemin] = re.sub(r'<img\b[^>]*>', optimiser, page, flags=re.I)
    return pages


def neutraliser_pilotes_absents(pages, catalogue, site):
    """Désactiver les lecteurs des pilotes si leur MP4 est absent du paquet.

    Une présence locale permet le test de lecture en recette privée, sans
    déclaration ni référence documentaire supplémentaire.
    """
    contenus = {c['id']: c for c in catalogue.get('contenus', [])}
    cibles = {'programme.html': [('programmeVideo', 'pop.pilote')],
              'programme-soleil-xl.html': [('programmeVideo', 'soleil.extrait'), ('soleilPilotVideo', 'soleil.pilote')]}
    for nom, liste in cibles.items():
        texte = pages.get(nom)
        if not texte: continue
        for identifiant, cle in liste:
            c = contenus[cle]
            rx = re.compile(r'<video\b[^>]*\bid="'+re.escape(identifiant)+r'"[^>]*>', re.S|re.I)
            m = rx.search(texte)
            if not m: raise ValueError('R3 vidéo du programme absente : '+nom+'/'+identifiant)
            tag = m.group(0)
            if not media_disponible(site, c):
                # Pas de lecteur sans média présent : conserver la provenance
                # de l'URL source sans activation trompeuse.
                tag = re.sub(r'\s(?:src|data-premium-src)="[^"]*"', '', tag)
                if 'data-r3-lecture-suspendue' not in tag:
                    tag = tag[:-1]+' data-r3-lecture-suspendue="true">'
            else:
                original = re.search(r'data-r163-original-src="([^"]+)"', tag)
                if original and not re.search(r'(?<![\w-])src="', tag):
                    tag = tag[:-1]+' src="'+original.group(1)+'">'
                tag = tag.replace(' data-r163-missing-from-package="true"','')
            texte = texte[:m.start()]+tag+texte[m.end():]
            # L'affichage du programme doit suivre le média réellement présent :
            # ne jamais laisser un avis « fichier absent » après activation du lecteur.
            disponible = media_disponible(site, c)
            etats = {
                ('pop.pilote', ''): (
                    'La vidéo de deux minutes est accessible en recette privée. L’affiche, la narration et les références restent consultables.',
                    'La vidéo de deux minutes n’est pas intégrée à cette archive. L’affiche, la narration et les références restent consultables.'),
                ('soleil.extrait', ''): (
                    'L’extrait de 30 secondes est accessible dans le lecteur de cette page. Le récit et les références restent consultables.',
                    'L’extrait de 30 secondes n’est pas intégré à cette archive. Le récit et les références restent consultables.'),
                ('soleil.extrait', 'lecture'): (
                    'La lecture commence à votre demande et s’arrête à la fin de l’extrait. Cet extrait ne rapporte ni XP ni Points.',
                    'L’extrait n’est pas encore intégré. Sa narration et ses références restent consultables ; aucun XP ni Point n’est attribué.'),
                ('soleil.pilote', ''): (
                    'Pilote de 2 minutes : lecture accessible dans cette page ; narration et références consultables ci-dessous.',
                    'Pilote de 2 minutes : fichier vidéo absent de cette archive ; narration et références consultables ci-dessous.'),
            }
            for (contenu_id, variante), (present, absent) in etats.items():
                if contenu_id != cle: continue
                condition = (r'(?=[^>]*data-video-status-for="'+re.escape(cle)+r'")'
                             + (r'(?=[^>]*data-video-status-variant="'+variante+r'")' if variante
                                else r'(?![^>]*data-video-status-variant=)'))
                rx_etat = re.compile(r'(<p\b'+condition+r'[^>]*>)(.*?)(</p>)', re.S|re.I)
                if len(rx_etat.findall(texte)) != 1:
                    raise ValueError('R7 statut vidéo introuvable ou ambigu : '+nom+'/'+cle+'/'+variante)
                texte = rx_etat.sub(lambda match: match.group(1)+(present if disponible else absent)+match.group(3), texte, count=1)
        pages[nom]=texte
    return pages


def sous_titres_declares(contenu, site):
    """Ne jamais inventer un VTT : admettre uniquement un chemin déclaré ou
    le VTT existant dont le nom est exactement celui du MP4 de ce contenu.
    """
    explicit = contenu.get('sous_titres')
    candidats = ([explicit] if explicit else [])
    video = contenu.get('media')
    if video and video.lower().endswith('.mp4'):
        candidats.append('media/subtitles/' + os.path.basename(video)[:-4] + '.vtt')
    return [dict(chemin=c, present_dans_paquet=media_dans_paquet(site, c),
                 provenance=('catalogue' if c == explicit else 'nom_identique_video'))
            for c in dict.fromkeys(candidats) if c and (c == explicit or media_dans_paquet(site, c))]


def contrat_av03(catalogue, site):
    """Contrat éditorial de passation AV-03. Aucune promesse reconstruite sans source."""
    univers = {u['id']: u for u in catalogue.get('univers', [])}
    index = {c['id']: c for c in catalogue.get('contenus', [])}
    sorties = {}
    for key in ('signature', 'pop', 'progression', 'soleil'):
        court, long = index[key + '.court'], index[key + '.long']
        monde = univers[key]
        sorties[key] = {
            'identifiant': key, 'titre': court['titre'], 'univers': monde['nom'],
            'sujet_court': court.get('promesse', ''), 'promesse_court': court.get('promesse', ''),
            'question_approfondissement': monde.get('question_edition', ''),
            'valeur_ajoutee_long': long.get('apport', ''),
            'continuer_libelle': 'Découvrir le Long · ' + str(long.get('duree_s', '')) + ' s',
            'court': {k: court.get(k) for k in ('id', 'titre', 'page', 'media', 'affiche', 'duree_s', 'statut')},
            'long': {k: long.get(k) for k in ('id', 'titre', 'page', 'media', 'affiche', 'duree_s', 'statut')},
            'quiz': {'question': (long.get('quiz') or {}).get('question', ''), 'statut': 'facultatif'},
            'contribution': {'page': 'communaute.html?univers=' + key,
                'question': monde.get('question_edition', ''), 'etat': 'facultative'},
            'sources': long.get('sources', []),
            'droits': {'etat': 'a_verifier_pour_la_beta', 'provenance_catalogue':
                long.get('detail', {}).get('droits') if isinstance(long.get('detail'), dict) else None},
            'statut_validation': 'texte_catalogue_existant_a_revalider_av03',
            # Contrôle d'existence local seulement, sans preuve de droits ou de décodage.
            'medias': {
                'court': {
                    'video': court.get('media'),
                    'video_dans_paquet': media_dans_paquet(site, court.get('media')), 'video_disponible': media_disponible(site, court),
                    'affiche': court.get('affiche'),
                    'affiche_dans_paquet': media_dans_paquet(site, court.get('affiche')),
                    'sous_titres': sous_titres_declares(court, site),
                },
                'long': {
                    'video': long.get('media'),
                    'video_dans_paquet': media_dans_paquet(site, long.get('media')), 'video_disponible': media_disponible(site, long),
                    'affiche': long.get('affiche'),
                    'affiche_dans_paquet': media_dans_paquet(site, long.get('affiche')),
                    'sous_titres': sous_titres_declares(long, site),
                },
            },
            'statut_disponibilite_medias': 'verifie_presence_fichiers_locale_uniquement',
            'statut_droits': 'a_valider',
            'statut_sous_titres': 'presence_locale_verifiee_sans_validation_artistique',

            'origine': 'source/catalogue/catalogue.json, textes déjà présents; aucune invention',
        }
    return sorties


def volet_av03(n):
    """Bloc accessible, distinct des étiquettes de récompenses ; toutes données échappées."""
    esc = lambda x: html.escape(str(x or ''), quote=True)
    c = n['court']; l = n['long']; title = n['titre']; u = n['univers']
    court_present = n['medias']['court']['video_disponible']
    long_present = n['medias']['long']['video_disponible']
    if not court_present and not long_present:
        media_notice = 'Court et Long en attente de leurs fichiers vidéo. Les fiches restent consultables.'
    elif not court_present:
        media_notice = 'Court en attente de son fichier vidéo. Le Long reste accessible.'
    elif not long_present:
        media_notice = 'Long en attente de son fichier vidéo. Le Court reste accessible.'
    else:
        media_notice = ''
    return (f'<section class="r13a-narration" aria-label="Comprendre le Court et le Long de {esc(u)}" '
        f'data-av03-id="{esc(n["identifiant"])}" data-av03-statut="catalogue-a-valider" '
        f'data-av03-court-fichier="{"present" if n["medias"]["court"]["video_disponible"] else "absent"}" '
        f'data-av03-long-fichier="{"present" if long_present else "absent"}">'
        '<p class="r13a-eyebrow">Cette histoire, à votre rythme</p>'
        f'<h2>{esc(title)} : ce que racontent les deux formats</h2>'
        '<div class="r13a-parcours">'
        f'<div><strong>Court · {esc(_duree(c["duree_s"]))}</strong><p>{esc(n["promesse_court"])}</p></div>'
        f'<div><strong>Long · {esc(_duree(l["duree_s"]))}</strong><p>{esc(n["valeur_ajoutee_long"])}</p></div>'
        '</div>'
        f'<p class="r13a-question"><b>À approfondir :</b> {esc(n["question_approfondissement"])}</p>'
        '<div class="r13a-actions"><button type="button" data-av03-long>'
        + ('Découvrir le Long librement ↗' if long_present else 'Explorer la fiche du Long ↗') + '</button>'
        '<a href="../mon-ithakya.html#decouvertes">Mes découvertes gardées</a>'
        f'<a href="../communaute.html?univers={esc(n["identifiant"])}&amp;oeuvre=ith-{esc({"signature":"signature-lien","pop":"pop-moment","progression":"progression-elan","soleil":"soleil-courant"}[n["identifiant"]])}">Échanger autour de ce sujet</a>'
        f'<a href="../oeuvres/{esc(n["identifiant"])}.html">Fiche de l’œuvre et crédits ↗</a>'
        f'<a href="../territoires/{ {"signature": "sciences-tech", "soleil": "sciences-tech", "progression": "sport-aventure", "pop": "pop-culture"}[n["identifiant"]] }.html">Retour au territoire ↗</a></div>'
        + (f'<p class="r13a-media-reserve" role="status">{media_notice}</p>' if media_notice else '')
        + '<small>Le Quiz est facultatif. Informations éditoriales issues du catalogue.</small>'
        '</section>')



def fiches_oeuvres(cat, site, S):
    """R15: one canonical shared source, one work fiche per actual Court/Long pair.
    No inferred author names, rights, or playable media.
    """
    def esc(t): return html.escape(str(t or ''), quote=True)
    uidx = {u['id']: u for u in cat.get('univers', [])}
    cidx = {c['id']: c for c in cat.get('contenus', [])}
    template = lire(os.path.join(S.src, 'gabarit', 'fiche-oeuvre.html')).replace(
        '{{> composant/attenzia-p1}}', lire(os.path.join(S.src, 'composants', 'attenzia-p1.html')))
    out = {}
    fil_editorial = {'signature':'pop', 'pop':'progression', 'progression':'soleil', 'soleil':'signature'}
    _terr = {x['id']: x for x in cat.get('territoires', [])}
    terr_ctx = {'signature': _terr['sciences-tech'], 'soleil': _terr['sciences-tech'], 'progression': _terr['sport-aventure'], 'pop': _terr['pop-culture']}
    # L8 — relations éditoriales motivées par les sujets du catalogue, jamais par une activité simulée.
    passerelles = {
       'signature': 'Après les circulations invisibles entre le Sahara et l’Amazonie, regardez ce qui précède un moment de scène : les personnes et les gestes que le public ne voit pas.',
       'pop': 'Derrière une scène comme derrière un geste sportif, il y a une préparation, des décisions et un collectif souvent invisibles.',
       'progression': 'Du geste qui se prépare sur le terrain aux phénomènes du Soleil, changez d’échelle pour observer ce qui agit avant d’être visible.',
       'soleil': 'Après les liens entre le Soleil et la Terre, suivez un autre trajet invisible : celui des poussières du Sahara jusqu’à l’Amazonie.',
    }
    for uid in ('signature', 'pop', 'progression', 'soleil'):
        u = uidx[uid]; court = cidx[uid + '.court']; long = cidx[uid + '.long']
        following = fil_editorial[uid]; next_u = uidx[following]; next_c = cidx[following+'.court']
        cp, lp = media_disponible(site, court), media_disponible(site, long)
        ch = court.get('personne') or {}
        # The historical names are explicitly illustrative: do not expose as authentic credits.
        auth = 'Attribution en cours de validation ; aucun portrait ni nom illustratif ne vaut crédit réel.' if ch.get('statut') != 'créateur attesté' else esc(ch.get('nom'))
        createur_etat = (('Création attestée : ' + esc(ch.get('nom'))) if ch.get('statut') == 'créateur attesté' and ch.get('nom') else
                        'Les crédits de création restent à confirmer. Aucun portrait illustratif n’est présenté comme l’auteur de cette œuvre.')
        v = {
          'ID': uid, 'OEUVRE_SOCIALE': 'ith-' + {'signature':'signature-lien','pop':'pop-moment','progression':'progression-elan','soleil':'soleil-courant'}[uid], 'NOM': esc(u['nom']), 'DEVISE': esc(u['devise']),
          'TITRE': esc(court['titre']), 'SOUS_TITRE': esc(long.get('sous_titre') or u['thematique']),
          'MANIFESTE': esc(u.get('manifeste')), 'COURT_PROMESSE': esc(court.get('promesse')),
          'LONG_PROMESSE': esc(long.get('apport')), 'COURT_DUREE': str(court.get('duree_s') or '?'),
          'LONG_DUREE': str(long.get('duree_s') or '?'),
          'IMAGE': esc('../' + (court.get('affiche') or u['image_entree'])),
          'COURT_LIEN': esc('../' + court['page']), 'LONG_LIEN': esc('../' + long['page']),
          'UNIVERS_LIEN': esc('../' + u['page']),
          'TERR_ID': terr_ctx[uid]['id'], 'TERR_NOM': esc(terr_ctx[uid]['nom']), 'TERR_LIEN': esc('../' + terr_ctx[uid]['page']),  # S4 : fil et retours vers le territoire
          'QUESTION': esc(u.get('question_edition')), 'CREDIT': auth,
          'CREATEUR_ETAT': createur_etat, 'SUITE_RAIS0N': esc(passerelles[uid]),
          'STATUT_COURT': ('Fichier vidéo présent dans cette archive' if cp else 'Vidéo absente de cette archive · fiche et affiche consultables'),
          'STATUT_LONG': ('Fichier vidéo présent dans cette archive' if lp else 'Vidéo absente de cette archive · approfondissement éditorial consultable'),
          'ACCESS_COURT': 'Lecture du Court' if cp else 'Consulter l’espace Court',
          'ACCESS_LONG': 'Regarder le Long' if lp else 'Explorer l’espace Long',
          # R6 : éviter deux actions de lecture trompeuses lorsque les films ne sont pas intégrés.
          # La fiche conserve son récit et une entrée facultative vers le parcours historique ;
          # les deux liens directs de lecture réapparaissent automatiquement avec les MP4.
          'COURT_ACTION_HTML': ('<a class="ith15-cta" href="' + esc('../' + court['page']) + '">Lire le Court <span aria-hidden="true">↗</span></a>') if cp else '',
          'HERO_CTA': ('<a class="ith15-cta" href="' + esc('../' + court['page']) + '">Regarder le Court <span aria-hidden="true">↗</span></a>') if cp else '<a class="ith15-cta" href="#formats">Découvrir les deux formats <span aria-hidden="true">↓</span></a>',
          'HERO_LONG': ('<a href="' + esc('../' + long['page']) + '">Voir le Long ↗</a>') if lp else '',
          'LONG_ACTION_HTML': ('<a class="ith15-cta" href="' + esc('../' + long['page']) + '">Voir le Long <span aria-hidden="true">↗</span></a>') if lp else '',
          'SUITE_NOM': esc(next_u['nom']), 'SUITE_DEVISE': esc(next_u['devise']),
          'SUITE_TITRE': esc(next_c['titre']), 'SUITE_MANIFESTE': esc(next_u['manifeste']),
          'SUITE_LIEN': '../oeuvres/'+following+'.html',
          'SUITE_IMAGE': esc('../'+(next_c.get('affiche') or next_u['image_entree'])),
        }
        text=template
        for k,val in v.items(): text=text.replace('%%'+k+'%%',val)
        out['oeuvres/'+uid+'.html'] = S.resoudre(text, {}, {'univers':uid, 'racine':'../'})
    return out

M2_ID = re.compile(r'^[a-z0-9][a-z0-9-]{2,47}$')
M2_HEX = re.compile(r'^#[0-9A-Fa-f]{6}$')
M2_HISTORIQUES = {'signature': 'ith-signature-lien', 'pop': 'ith-pop-moment', 'progression': 'ith-progression-elan', 'soleil': 'ith-soleil-courant'}
M2_TERRITOIRES = {'sciences-tech': 'signature', 'culture-creation': 'culture', 'sport-aventure': 'progression', 'societe-impact': 'societe', 'pop-culture': 'pop'}
M2_CONTEXTES = tuple(M2_HISTORIQUES) + ('culture', 'societe')
M2_PAGES_UNIVERS = {'signature': 'demos/01-signature.html', 'pop': 'demos/02-pop-culture.html', 'progression': 'demos/03-progression.html', 'soleil': 'demos/05-soleil-xl.html'}


def m2_territoires(cat):
    """S1 — Registre des cinq territoires contrôlé à la génération (mêmes règles que le serveur) : exactement cinq identifiants
    dans l'ordre officiel, contexte technique conforme, libellés présents ; chaque œuvre déclare des territoires connus, sans
    doublon, dont le principal porte le contexte technique de l'œuvre (une œuvre = un contexte = un parcours = un gain).
    Toute entrée non conforme ARRÊTE la génération. Retourne (liste ordonnée des territoires, index par identifiant)."""
    liste = sorted(cat.get('territoires', []), key=lambda x: x.get('ordre', 0))
    if [x.get('id') for x in liste] != list(M2_TERRITOIRES):
        raise ValueError('S1 : les cinq territoires officiels doivent figurer dans l’ordre : ' + ', '.join(M2_TERRITOIRES))
    for k, x in enumerate(liste, 1):
        if x.get('ordre') != k or x.get('contexte') != M2_TERRITOIRES[x['id']]: raise ValueError('S1 : ordre ou contexte invalide pour ' + x['id'])
        if x.get('page') != 'territoires/' + x['id'] + '.html': raise ValueError('S1 : page invalide pour ' + x['id'])
        for champ in ('nom', 'manifeste', 'question_edition'):
            if not isinstance(x.get(champ), str) or not x[champ].strip(): raise ValueError('S1 : ' + champ + ' absent pour ' + x['id'])
    idx = {x['id']: x for x in liste}
    for w in cat.get('oeuvres', []):
        t = w.get('territoires')
        if not isinstance(t, list) or not t or len(set(t)) != len(t) or any(x not in idx for x in t):
            raise ValueError('S1 : territoires invalides pour l’œuvre ' + str(w.get('id')))
        if not w.get('historique') and M2_TERRITOIRES[t[0]] != w.get('univers'):
            raise ValueError('S1 : le territoire principal de ' + w['id'] + ' (' + t[0] + ') ne porte pas son contexte (' + str(w.get('univers')) + ')')
    return liste, idx


def m2_oeuvres(cat):
    """Registre M2 contrôlé à la génération (mêmes règles que le serveur) : identifiant stable et unique, univers public,
    5 idées tant que M1 n'est pas arbitré, Court et Long déclarés au catalogue avec durée, médias distincts entre œuvres.
    Toute entrée non conforme ARRÊTE la génération (aucune œuvre publiée par approximation)."""
    contenus = {c['id']: c for c in cat.get('contenus', [])}
    vus, medias, sortie = set(), {}, []
    for w in cat.get('oeuvres', []):
        i = w.get('id', '')
        if i in vus: raise ValueError('M2 : identifiant d’œuvre en double : ' + i)
        vus.add(i)
        if w.get('historique'):
            if M2_HISTORIQUES.get(w.get('univers')) != i: raise ValueError('M2 : œuvre historique non reconnue : ' + i)
            continue
        if not M2_ID.match(i) or i in M2_HISTORIQUES.values(): raise ValueError('M2 : identifiant hors format : ' + i)
        if w.get('univers') not in M2_CONTEXTES: raise ValueError('M2 : univers non public pour ' + i)
        if w.get('statut') not in ('disponible', 'essai_prive', 'retiree'): raise ValueError('M2 : statut inconnu pour ' + i)
        if w.get('idees') != 5: raise ValueError('M2 : ' + i + ' déclare ' + str(w.get('idees')) + ' idées ; la règle des cinq idées reste en vigueur (M1 non arbitré)')
        court, long = contenus.get(i + '.court'), contenus.get(i + '.long')
        if not court or not long or court.get('oeuvre') != i or long.get('oeuvre') != i: raise ValueError('M2 : Court/Long absents ou non rattachés pour ' + i)
        if not court.get('duree_s') or not long.get('duree_s'): raise ValueError('M2 : durée absente pour ' + i)
        if len(long.get('chapitres') or []) != 5: raise ValueError('M2 : ' + i + ' : cinq idées horodatées attendues dans le Long')
        for c in (court, long):
            m = c.get('media_sha256') or c.get('media')
            if m in medias: raise ValueError('M2 : média de ' + c['id'] + ' déjà déclaré par ' + medias[m])
            medias[m] = i
        if (w.get('ambiance') or {}).get('accent') and not M2_HEX.match(w['ambiance']['accent']): raise ValueError('M2 : couleur invalide pour ' + i)
        sortie.append((w, court, long))
    return sortie


def m2_duree(s):
    s = int(round(float(s))); return f'{s} s' if s < 90 else f'{s // 60} min' + (f' {s % 60:02d}' if s % 60 else '')


def m2_carte(href, titre, createur, promesse, dc, dl, ident, img, tag, aussi='', prefix='../'):
    """Carte d'œuvre de la programmation (fiche d'univers et page de territoire) : texte échappé, état personnel complété par le script."""
    esc = lambda x: html.escape(str(x if x is not None else ''), quote=True)
    return (f'<li class="m2-carte" data-oeuvre="{esc(ident)}"><a href="{esc(href)}">'
            + (f'<img src="{prefix}{esc(img)}" alt="" width="320" height="180" loading="lazy" decoding="async">' if img else '')
            + f'<span class="m2-carte-texte"><strong>{esc(titre)}</strong><span>{esc(createur)}</span><span>{esc(promesse)}</span>'
            + f'<span class="m2-carte-durees">Court {m2_duree(dc) if dc else "—"} · Long {m2_duree(dl) if dl else "—"}</span>'
            + (f'<span class="m2-carte-tag">{esc(tag)}</span>' if tag else '')
            + (f'<span class="m2-carte-aussi">{esc(aussi)}</span>' if aussi else '')
            + '<span class="m2-carte-etat" data-etat-oeuvre></span></span></a></li>')


def pages_oeuvres_m2(cat, site, S):
    """Pages d'œuvre M2 et blocs « programmation » des fiches d'univers. Textes échappés, données de la page en JSON
    sans balise fermante possible. Les mires et fichiers de test portent un bandeau explicite."""
    esc = lambda t: html.escape(str(t if t is not None else ''), quote=True)
    oeuvres = m2_oeuvres(cat)
    if not oeuvres:
        return {}, {}
    gab = lire(os.path.join(S.src, 'gabarit', 'oeuvre-m2.html')).replace(
        '{{> composant/attenzia-p1}}', lire(os.path.join(S.src, 'composants', 'attenzia-p1.html')))
    univ = {u['id']: u for u in cat.get('univers', [])}
    _, terr = m2_territoires(cat)
    contenus = {c['id']: c for c in cat.get('contenus', [])}
    registre = {w['id']: w for w in cat.get('oeuvres', [])}
    def duree(s):
        s = int(round(float(s))); return f'{s} s' if s < 90 else f'{s // 60} min' + (f' {s % 60:02d}' if s % 60 else '')
    def horloge(s):
        s = int(round(float(s))); return f'{s // 60}:{s % 60:02d}'
    pages, progs = {}, {}
    par_univers = {}
    for w, court, long in oeuvres:
        par_univers.setdefault(w['univers'], []).append((w, court, long))
    for w, court, long in oeuvres:
        tp = terr[w['territoires'][0]]; cr = w.get('createur') or {}; cred = w.get('credits') or {}
        aussi = [terr[x]['nom'] for x in w['territoires'][1:]]
        idees = ''.join(f'<li><button type="button" class="m2-idee" data-idee-n="{c["n"]}" data-debut="{esc(c["debut_s"])}" aria-label="Lire l’idée {c["n"]}, {esc(c["titre"])}, à {horloge(c["debut_s"])}">'
                        f'<span class="m2-idee-n">{c["n"]}</span><span>{esc(c["titre"])}</span><time>{horloge(c["debut_s"])}</time></button></li>' for c in long['chapitres'])
        choix = ''.join(f'<button type="button" data-idee="{c["n"]}">{esc(c["titre"])}</button>' for c in long['chapitres'])
        quiz = long.get('quiz')
        quiz_html = ('<fieldset class="m2-quiz" id="m2-quiz"><legend>Quiz facultatif · ' + esc(quiz['question']) + '</legend>'
                     + ''.join(f'<button type="button" data-reponse="{k}">{esc(r)}</button>' for k, r in enumerate(quiz['reponses']))
                     + (f'<p class="m2-quiz-explication" id="m2-quiz-explication" hidden>{esc(quiz["explication"])}</p>' if quiz.get('explication') else '') + '</fieldset>') if quiz else ''
        lignes = [('Œuvre originale', cred.get('titre_original')), ('Auteur·rice', cred.get('auteurs')), ('Licence', cred.get('licence')),
                  ('Source officielle', cred.get('source_url')), ('Musique et son', cred.get('musique')), ('Modifications', cred.get('modifications')),
                  ('Langue et sous-titres', cred.get('langue')), ('Réserves', cred.get('reserves_droits')), ('Réception artistique', cred.get('reception'))]
        def dd(v):
            if isinstance(v, list): v = ' · '.join(map(str, v))
            v = str(v or 'Non renseigné')
            return f'<a href="{esc(v)}" rel="noopener noreferrer">{esc(v)}</a>' if v.startswith('https://') else esc(v)
        credits_html = ''.join(f'<div><dt>{esc(k)}</dt><dd>{dd(v)}</dd></div>' for k, v in lignes)
        if cred.get('licence_url'):
            credits_html += f'<div><dt>Texte de la licence</dt><dd><a href="{esc(cred["licence_url"])}" rel="noopener noreferrer license">{esc(cred["licence_url"])}</a></dd></div>'
        nature = w.get('nature')
        bandeau = ('<p class="m2-bandeau" role="note"><strong>Mire de banc.</strong> Contenu technique de recette M2, sans valeur artistique : '
                   'il ne représente aucune création ni œuvre réelle.</p>') if nature == 'banc' else (
                  '<p class="m2-bandeau" role="note"><strong>Essai privé.</strong> Œuvre en réception : lecture technique locale, réception artistique non prononcée.</p>' if w.get('statut') == 'essai_prive' else '')
        soeurs = par_univers[w['univers']]; k = [x[0]['id'] for x in soeurs].index(w['id'])
        suivante = soeurs[(k + 1) % len(soeurs)][0] if len(soeurs) > 1 else None
        amb = w.get('ambiance') or {}
        donnees = {'oeuvre': w['id'], 'univers': w['univers'], 'titre': w.get('titre'), 'idees': 5,
                   'court': {'id': court['id'], 'duree_s': court['duree_s']}, 'long': {'id': long['id'], 'duree_s': long['duree_s'],
                   'chapitres': [{'n': c['n'], 'titre': c['titre'], 'debut_s': c['debut_s']} for c in long['chapitres']]},
                   'quiz': bool(quiz), 'nature': nature or 'oeuvre', 'statut': w.get('statut')}
        valeurs = {
            'TITRE': esc(w.get('titre')), 'SOUS_TITRE': esc(w.get('sous_titre')), 'ID': esc(w['id']), 'UNIVERS': esc(w['univers']),
            'UNIVERS_NOM': esc(tp.get('nom')), 'UNIVERS_LIEN': '../' + tp['page'], 'AUSSI': (f'<p class="m2-aussi">Aussi présentée dans : {esc(" · ".join(aussi))}. Une seule œuvre, un seul parcours.</p>' if aussi else ''),
            'PROGRAMMATION_LIEN': '../' + tp['page'] + '#programmation', 'MON_LIEN': '../mon-ithakya.html?oeuvre=' + esc(w['id']) + '#mes-oeuvres',
            'CREATEUR': (f'<a href="../createurs/{esc(cr["id"])}.html">{esc(cr.get("nom"))}</a>' if cr.get('id') else esc(cr.get('nom'))), 'CREATEUR_ROLE': esc(cr.get('role')), 'PROMESSE_COURT': esc(court.get('promesse')),
            'APPORT_LONG': esc(long.get('apport')), 'LONG_TITRE': esc(long.get('sous_titre') or long.get('titre')), 'QUESTION': esc(w.get('question')),
            'AFFICHE': '../' + esc(w.get('affiche') or court.get('affiche') or ''), 'AFFICHE_LONG': '../' + esc(long.get('affiche') or w.get('affiche') or ''), 'AFFICHE_ALT': esc('Affiche : ' + str(w.get('titre'))),
            'COURT_MEDIA': '../' + esc(court.get('media')), 'LONG_MEDIA': '../' + esc(long.get('media')),
            'COURT_ID': esc(court['id']), 'LONG_ID': esc(long['id']), 'COURT_S': esc(court['duree_s']), 'LONG_S': esc(long['duree_s']),
            'COURT_DUREE': duree(court['duree_s']), 'LONG_DUREE': duree(long['duree_s']), 'IDEES': idees, 'IDEES_CHOIX': choix, 'QUIZ': quiz_html,
            'CREDITS': credits_html, 'BANDEAU_NATURE': bandeau,
            'ETAT_INITIAL': 'Lecture libre. Connectez-vous pour retrouver votre parcours de cette œuvre.',
            'AMBIANCE': (f'--m2-accent:{amb["accent"]};' if amb.get('accent') else ''),
            'SUIVANTE': (f'<a href="../oeuvres/{esc(suivante["id"])}.html">Œuvre suivante : {esc(suivante.get("titre"))} →</a>' if suivante else ''),
            'DONNEES': json.dumps(donnees, ensure_ascii=False).replace('<', '\\u003c'),
        }
        t = gab
        for kx, vx in valeurs.items():
            t = t.replace('%%' + kx + '%%', vx)
        if '%%' in t: raise ValueError('M2 : marqueur non remplacé dans la page de ' + w['id'] + ' : ' + re.search(r'%%[A-Z_]+%%', t).group(0))
        pages['oeuvres/' + w['id'] + '.html'] = S.resoudre(t, {}, {'univers': w['univers'], 'racine': '../'})
    for uid, liste in par_univers.items():
        if uid not in M2_HISTORIQUES: continue   # culture, societe : programmation portée par la page du territoire
        hist = registre.get(M2_HISTORIQUES[uid]) or {}
        court_h = contenus.get(uid + '.court', {}); long_h = contenus.get(uid + '.long', {})
        cartes = [(f'../{M2_PAGES_UNIVERS[uid]}', hist.get('titre') or court_h.get('titre'), (hist.get('createur') or {}).get('nom') or 'Œuvre d’ouverture de l’univers',
                   court_h.get('promesse'), court_h.get('duree_s'), long_h.get('duree_s'), M2_HISTORIQUES[uid], court_h.get('affiche'), '')]
        for w, court, long in liste:
            tag = 'Mire de banc' if w.get('nature') == 'banc' else ('Essai privé' if w.get('statut') == 'essai_prive' else '')
            cartes.append((f'../oeuvres/{w["id"]}.html', w.get('titre'), (w.get('createur') or {}).get('nom'), court.get('promesse'), court['duree_s'], long['duree_s'], w['id'], w.get('affiche') or court.get('affiche'), tag))
        items = ''.join(m2_carte(href, tt, cr, pr, dc, dl, i, img, tag) for href, tt, cr, pr, dc, dl, i, img, tag in cartes)
        progs[uid] = ('<section class="m2-programmation" id="programmation" aria-labelledby="m2-prog-titre"><link rel="stylesheet" href="../assets/css/ithakya-m2-oeuvre.css?sha=0">'
                      f'<p class="ith15-kicker">La programmation · {esc(univ[uid].get("nom"))}</p><h2 id="m2-prog-titre">Plusieurs œuvres, un même regard</h2>'
                      f'<p>Chaque œuvre a son créateur, son Court, son Long et votre propre parcours. Vous passez de l’une à l’autre librement.</p><ul class="m2-cartes">{items}</ul></section>'
                      '<script src="../assets/js/ithakya-m2-programmation.js?sha=0" defer></script>')
    # S5·CR-04 — fiche créateur : une porte de découverte (œuvres, territoires, crédits, droits). Statut affiché tel quel, jamais promu.
    gab_cr = lire(os.path.join(S.src, 'gabarit', 'createur.html'))
    groupes = {}
    for w, court, long in oeuvres:
        c0 = w.get('createur') or {}
        if c0.get('id'): groupes.setdefault(c0['id'], []).append((w, court, long))
    libelle_statut = {'créateur attesté': 'Création attestée', 'mire de banc': 'Mire de banc : aucune création réelle', 'profil de démonstration': 'Profil de démonstration : illustratif'}
    for cid, liste in groupes.items():
        c0 = liste[0][0]['createur']; sk = c0.get('statut') or 'non renseigné'
        w0 = liste[0][0]; tp0 = terr[w0['territoires'][0]]
        cartes = ''.join(m2_carte('../oeuvres/' + w['id'] + '.html', w.get('titre'), '', court.get('promesse'), court['duree_s'], long['duree_s'], w['id'], w.get('affiche') or court.get('affiche'),
                                  'Mire de banc' if w.get('nature') == 'banc' else ('Essai privé' if w.get('statut') == 'essai_prive' else '')) for w, court, long in liste)
        tids = []
        for w, _, _ in liste:
            for x in w['territoires']:
                if x not in tids: tids.append(x)
        autres = ('<p class="ithc-note">Aucune autre œuvre reçue pour ce créateur pour l’instant. <a href="../' + esc(tp0['page']) + '#programmation">Retour à la programmation de ' + esc(tp0['nom']) + '</a>.</p>' if len(liste) == 1 else
                  '<p class="ithc-note">Choisissez librement : chaque œuvre garde son Court, son Long et votre propre parcours.</p>')
        cred_html = ''.join('<div><dt>' + esc(w.get('titre')) + '</dt><dd>' + esc((w.get('credits') or {}).get('licence') or 'Licence non renseignée') + ' · langue : ' + esc((w.get('credits') or {}).get('langue') or 'non renseignée')
                            + ' · droits : ' + esc(((w.get('droits') or {}).get('etat')) or 'état non renseigné') + '</dd></div>' for w, _, _ in liste)
        bandeau = '' if sk == 'créateur attesté' else '<p class="m2-bandeau" role="note"><strong>' + esc(libelle_statut.get(sk, 'Statut à confirmer')) + '.</strong> Cette fiche ne présente pas une personne ou une création attestée.</p>'
        vals = {'ID': esc(cid), 'NOM': esc(c0.get('nom')), 'ROLE': esc(c0.get('role')), 'STATUT': esc(libelle_statut.get(sk, 'Statut à confirmer')), 'STATUT_CLE': esc(sk),
                'PRESENTATION': esc(c0.get('presentation') or 'Présentation à recevoir : aucun texte n’est inventé en attendant.'), 'BANDEAU': bandeau,
                'TERR_ID': esc(w0['territoires'][0]), 'TERR_NOM': esc(tp0['nom']), 'TERR_PAGE': esc(tp0['page']), 'CONTEXTE': esc(w0['univers']),
                'TITRE_OEUVRES': 'Une œuvre' if len(liste) == 1 else f'{len(liste)} œuvres', 'CARTES': cartes, 'AUTRES': autres,
                'TERRITOIRES': ' · '.join('<a href="../' + esc(terr[x]['page']) + '">' + esc(terr[x]['nom']) + '</a>' for x in tids), 'CREDITS': cred_html}
        t2 = gab_cr
        for kx, vx in vals.items(): t2 = t2.replace('%%' + kx + '%%', vx)
        if '%%' in t2: raise ValueError('Créateur : marqueur non remplacé : ' + re.search(r'%%[A-Z_]+%%', t2).group(0))
        pages['createurs/' + cid + '.html'] = S.resoudre(t2, {}, {'univers': w0['univers'], 'racine': '../'})
    return pages, progs


def pages_territoires(cat, site, S):
    """S1 — Une page par territoire (territoires/<id>.html), toujours produite : les cinq univers sont publics même lorsqu'ils
    n'ont pas encore d'œuvre. La programmation liste les œuvres historiques et les œuvres du registre inscrites dans le territoire
    (principal ou secondaire) ; un territoire sans œuvre le dit, sans en inventer. Textes échappés, JSON sans balise fermante."""
    esc = lambda x: html.escape(str(x if x is not None else ''), quote=True)
    liste, idx = m2_territoires(cat)
    gab = lire(os.path.join(S.src, 'gabarit', 'territoire.html'))
    contenus = {c['id']: c for c in cat.get('contenus', [])}
    nouvelles = {w['id']: (w, c, l) for w, c, l in m2_oeuvres(cat)}
    avec_oeuvres = {tid for w in cat.get('oeuvres', []) if w.get('statut') != 'retiree' for tid in w['territoires']}
    regards = {
        'sciences-tech': [('alex', 'Alex', 'Expert équipement')],
        'culture-creation': [('camille', 'Camille', 'Artiste-photographe'), ('lea', 'Léa', 'Autrice visuelle')],
        'sport-aventure': [('thomas', 'Thomas', 'Coach outdoor')],
        'societe-impact': [('nora', 'Nora', 'Journaliste société')],
        'pop-culture': [('maya', 'Maya', 'Créatrice culture live')],
    }
    prolongements = {
        'culture-creation': ('programme.html', 'Les coulisses d’une création collective',
                             'Le dossier du Moment, en Pop Culture, suit le travail qui précède l’entrée en scène.'),
        'societe-impact': ('oeuvres/signature.html', 'Ce que l’air transporte au-delà des frontières',
                           'La fiche du Lien, en Sciences & Tech, prolonge la piste des aérosols du Studio.'),
    }
    pages = {}
    for k, x in enumerate(liste):
        cartes, ids = [], []
        for w in sorted(cat.get('oeuvres', []), key=lambda y: (not y.get('historique'), y.get('ordre', 99))):
            if x['id'] not in w['territoires'] or w.get('statut') == 'retiree': continue
            principal = idx[w['territoires'][0]]
            aussi = '' if w['territoires'][0] == x['id'] else 'Territoire principal : ' + principal['nom']
            if w.get('historique'):
                ctx = w['univers']; court, long = contenus.get(ctx + '.court', {}), contenus.get(ctx + '.long', {})
                cartes.append(m2_carte('../oeuvres/' + ctx + '.html', w.get('titre') or court.get('titre'), 'Œuvre historique de la plateforme',
                                       court.get('promesse'), court.get('duree_s'), long.get('duree_s'), w['id'], court.get('affiche'), '', aussi))
            elif w['id'] in nouvelles:
                _, court, long = nouvelles[w['id']]
                tag = 'Mire de banc' if w.get('nature') == 'banc' else ('Essai privé' if w.get('statut') == 'essai_prive' else '')
                cartes.append(m2_carte('../oeuvres/' + w['id'] + '.html', w.get('titre'), (w.get('createur') or {}).get('nom'), court.get('promesse'),
                                       court['duree_s'], long['duree_s'], w['id'], w.get('affiche') or court.get('affiche'), tag, aussi))
            else: continue
            ids.append(w['id'])
        if cartes:
            titre, corps = ('Une œuvre à explorer' if len(ids) == 1 else 'Plusieurs œuvres à explorer'), (
                '<p>Consultez les fiches, les crédits et les pistes pour prolonger votre découverte. Les vidéos ne sont proposées que lorsqu’elles sont réellement disponibles.</p>'
                '<ul class="m2-cartes">' + ''.join(cartes) + '</ul>')
        else:
            # UX360 R5 — un état vide ne doit jamais bloquer la découverte :
            # les passerelles vers des œuvres existantes précèdent le détail éditorial.
            # Le détail reste consultable à la demande et n'ajoute aucun geste au parcours principal.
            ouverts = [y for y in liste if y['id'] != x['id'] and y['id'] in avec_oeuvres]
            passerelles = ''.join('<li><a href="../territoires/' + esc(y['id']) + '.html"><strong>' + esc(y['nom']) + '</strong><span>' + esc(y['manifeste']) + '</span></a></li>' for y in ouverts[:3])
            if x['id'] in prolongements:
                lien, libelle, contexte = prolongements[x['id']]
                passerelles = (f'<li><a href="../{esc(lien)}"><strong>{esc(libelle)}</strong>'
                                f'<span>{esc(contexte)}</span></a></li>' + passerelles)
            titre, corps = 'Programmation en préparation', (
                '<div class="terr-vide terr-prefiguration" data-etat="en-preparation">'
                '<p class="terr-vide-etat">Aucune œuvre programmée ici pour le moment.</p>'
                + ('<h3>À découvrir maintenant</h3><ul class="terr-passerelles">' + passerelles + '</ul>' if passerelles else '')
                + '<details class="terr-modalites"><summary>Comment fonctionne la programmation ?</summary>'
                '<p>Chaque œuvre associe un Court, un Long facultatif et son créateur. Les contenus ne sont annoncés qu’après réception, qualification et vérification des droits.</p>'
                '<p class="terr-question-rappel">' + esc(x['question_edition']) + '</p></details>'
                '<p><a href="../univers.html">Voir les cinq territoires</a> · <a href="../communaute.html?territoire=' + esc(x['id']) + '">Communauté</a></p></div>')
        prec, suiv = liste[(k - 1) % len(liste)], liste[(k + 1) % len(liste)]
        profils = ''.join(
            '<aside class="p2-regard-territoire">'
            f'<img src="../assets/portraits-demo/{cle}-human-demo.webp" width="72" height="72" alt="" loading="lazy" decoding="async">'
            '<div><p class="p2-surtitre">Profil de démonstration</p>'
            f'<p><strong>{esc(nom)}</strong> · {esc(metier)}</p>'
            f'<a class="p2-lien" href="../univers.html#portrait-{cle}">Lire le regard de {esc(nom)} <span aria-hidden="true">↗</span></a>'
            '</div></aside>' for cle, nom, metier in regards.get(x['id'], ())
        )
        visuel = x.get('image_entree')
        entree_visuelle = ''
        if visuel:
            entree_visuelle = (f'<figure class="terr-image"><img src="../{esc(visuel)}" alt="" width="960" height="540" decoding="async" fetchpriority="high">'
                               f'<a class="terr-image-lien" href="#programmation"><span class="terr-sr">Voir la programmation de {esc(x["nom"])}</span></a></figure>')
        elif x['id'] in ('culture-creation', 'societe-impact'):
            tuiles = ''.join(
                f'<a href="../univers.html#portrait-{cle}"><img src="../assets/portraits-p3/{cle}-384.webp" alt="" width="384" height="384" decoding="async">'
                f'<span>{esc(nom)} <span aria-hidden="true">↗</span></span></a>' for cle, nom, _ in regards[x['id']]
            )
            entree_visuelle = ('<figure class="terr-image p3-mosaique-territoire"><div class="p3-mosaique-regards">'
                               + tuiles + '</div><figcaption>Regards de créateurs illustratifs</figcaption></figure>')
        valeurs = {
            'ID': esc(x['id']), 'NOM': esc(x['nom']), 'CONTEXTE': esc(x['contexte']), 'NUMERO': str(k + 1), 'MANIFESTE': esc(x['manifeste']), 'QUESTION': esc(x['question_edition']),
            'HEROS_IMAGE': entree_visuelle,
            'PROG_TITRE': titre, 'PROG_CORPS': corps, 'REGARD_ILLUSTRATIF': profils,
            'PRECEDENT': f'<a href="../{esc(prec["page"])}">← {esc(prec["nom"])}</a>', 'SUIVANT': f'<a href="../{esc(suiv["page"])}">{esc(suiv["nom"])} →</a>',
            'DONNEES': json.dumps({'territoire': x['id'], 'contexte': x['contexte'], 'oeuvres': ids}, ensure_ascii=False).replace('<', '\\u003c'),
        }
        texte = gab
        for kx, vx in valeurs.items(): texte = texte.replace('%%' + kx + '%%', vx)
        if '%%' in texte: raise ValueError('S1 : marqueur non remplacé dans la page de ' + x['id'] + ' : ' + re.search(r'%%[A-Z_]+%%', texte).group(0))
        pages[x['page']] = S.resoudre(texte, {}, {'univers': x['contexte'], 'racine': '../'})
    return pages


def generer(src, site):
    S = Source(src)
    sorties = {}
    gab = lire(os.path.join(src, 'gabarit', 'univers.html'))
    catalogue_source = json.load(open(os.path.join(src, 'catalogue', 'catalogue.json'), encoding='utf8'))
    histoires_av03 = contrat_av03(catalogue_source, site)
    for f in sorted(glob.glob(os.path.join(src, 'univers', '*.json'))):
        u = json.load(open(f, encoding='utf8'))
        prof = u['publie'].count('/')
        sorti = S.resoudre(gab, u['emplacements'], {'univers': u['univers'], 'racine': '../' * prof,
            'r13a-narratif': volet_av03(histoires_av03[u['univers']])})
        sorties[u['publie']] = sorti
    univ = {p: t for p, t in sorties.items() if p.startswith('demos/')}
    pages_univ, communs = externaliser(univ, site)
    sorties.update(optimiser_images_lecteurs(pages_univ)); sorties.update(communs)
    cat = os.path.join(src, 'catalogue', 'catalogue.json')
    data = json.load(open(cat, encoding='utf8')) if os.path.exists(cat) else {}
    public = json.loads(json.dumps(data))
    data = enrichir(data, site)
    for p in sorted(glob.glob(os.path.join(src, 'pages', '**', '*.html'), recursive=True)):
        rel = os.path.relpath(p, os.path.join(src, 'pages'))
        page = S.resoudre(lire(p), {}, {'univers': '', 'racine': '../' * rel.count('/')})
        if rel == 'traversee.html':
            for uid in ('signature', 'pop', 'progression'):
                c = next(x for x in catalogue_source['contenus'] if x['id']==uid+'.court')
                present = media_disponible(site,c)
                prefix = uid.upper()
                notice = ('' if present else '<span class="r163-media-pending" role="status">Vidéo absente de cette archive. Consultez l’œuvre, son histoire et ses sources sur la fiche suivante.</span>')
                link = ('demos/'+{'signature':'01-signature', 'pop':'02-pop-culture', 'progression':'03-progression'}[uid]+'.html?view=court&amp;traversee=regards'
                        if present else 'oeuvres/'+uid+'.html')
                # Attributes are fixed from the controlled catalogue, not from a visitor query.
                page=page.replace('%%TRAVERSEE_MEDIA_'+prefix+'%%',notice).replace('%%TRAVERSEE_LIEN_'+prefix+'%%',link)
        if rel == 'index.html':
            court = next(c for c in catalogue_source['contenus'] if c['id']=='signature.court')
            film_present = media_disponible(site, court)
            # Décision de navigation à partir des octets locaux, pas du champ catalogue 'disponible'.
            action = ('<a class="button button-light" id="ux79-voir-court" href="demos/01-signature.html?view=court#courtVideo">Découvrir un Court <span aria-hidden="true">↗</span></a>'
                      if film_present else
                      '<a class="button button-light r166-l6-premier-film" href="oeuvres/signature.html" aria-label="Explorer l’œuvre Le lien"><img src="media/posters/ITHAKYA_POSTER_SIGNATURE_COURT_960X540.webp" alt="" width="62" height="62" decoding="async"><span>Explorer l’œuvre</span><span aria-hidden="true">↗</span></a>')
            if page.count('%%HOME_COURT_ACTION%%') != 1:
                raise ValueError('Place de la première action d’accueil modifiée')
            page = page.replace('%%HOME_COURT_ACTION%%', action)
            # L7 : les deux liens explicatifs de l'accueil ne doivent jamais aboutir
            # directement à un lecteur privé de fichier. Au retour des MP4 AV-05,
            # les chemins lecteur sont automatiquement restaurés à la génération.
            long_film = next(c for c in catalogue_source['contenus'] if c['id']=='signature.long')
            long_present = media_disponible(site, long_film)
            positions = {
                '%%EXEMPLE_COURT_LIEN%%': 'demos/01-signature.html?view=court#courtVideo' if film_present else 'oeuvres/signature.html#formats',
                '%%EXEMPLE_LONG_LIEN%%': 'demos/01-signature.html?view=long#longVideo' if long_present else 'oeuvres/signature.html#formats',
                '%%EXEMPLE_COURT_ACTION%%': 'Voir le Court · 21 s' if film_present else 'À propos du Court · 21 s',
                '%%EXEMPLE_LONG_ACTION%%': 'Voir le Long · 60 s' if long_present else 'À propos du Long · 60 s',
            }
            for marqueur, destination in positions.items():
                if page.count(marqueur) != 1:
                    raise ValueError('Lien de comparaison Court/Long absent ou ambigu : '+marqueur)
                page = page.replace(marqueur, destination)
        if rel == 'programme.html':
            pop_long = next(c for c in catalogue_source['contenus'] if c['id'] == 'pop.long')
            if not media_disponible(site, pop_long):
                page = page.replace('href="demos/02-pop-culture.html?view=long">← Revenir au Long',
                                    'href="oeuvres/pop.html#formats">← Retrouver la fiche Court/Long')
        if rel == 'programme-soleil-xl.html':
            soleil_long = next(c for c in catalogue_source['contenus'] if c['id'] == 'soleil.long')
            soleil_extrait = next(c for c in catalogue_source['contenus'] if c['id'] == 'soleil.extrait')
            if not media_disponible(site, soleil_long):
                page = page.replace('href="demos/05-soleil-xl.html?view=long">Consulter le Long, ses textes et ses références',
                                    'href="oeuvres/soleil.html#formats">Consulter la fiche Court/Long et ses références')
                page = page.replace('href="demos/05-soleil-xl.html" class="text-link">Retrouver le parcours « Le courant »',
                                    'href="oeuvres/soleil.html#formats" class="text-link">Consulter la fiche Court/Long')
            if not media_disponible(site, soleil_extrait):
                page = page.replace('href="#programmeVideo" class="text-link">Retrouver le lecteur de l’extrait',
                                    'href="#fabrication" class="text-link">Lire les références de l’extrait')
        sorties[rel] = donnees(page, data)
    sorties.update(fiches_oeuvres(catalogue_source, site, S))
    # M2 (prototype privé) : une page par œuvre non historique du registre « oeuvres », et la programmation de chaque
    # univers dans sa fiche. Sans œuvre nouvelle au catalogue, rien n'est produit ni modifié (sortie identique à FC2).
    m2_pages, m2_progs = pages_oeuvres_m2(data, site, S)
    sorties.update(m2_pages)
    sorties.update(pages_territoires(data, site, S))
    for uid, bloc in m2_progs.items():
        cle = 'oeuvres/' + uid + '.html'
        if cle in sorties and bloc:
            if sorties[cle].count('<nav class="ith15-bas"') != 1:
                raise ValueError('Emplacement de la programmation absent ou ambigu : ' + cle)
            sorties[cle] = sorties[cle].replace('<nav class="ith15-bas"', bloc + '<nav class="ith15-bas"', 1)
    # R13 lot 3 : les JS de progression édités disposent d'une source canonique,
    # reconstruite comme les pages ; les autres ressources historiques restent inchangées.
    for f in sorted(glob.glob(os.path.join(src, 'assets_statiques', '**', '*'), recursive=True)):
        if os.path.isfile(f):
            sorties['assets/' + os.path.relpath(f, os.path.join(src, 'assets_statiques'))] = lire(f)
    collection = json.loads(sorties['assets/avatars/p1/collection.json'])
    if any(not re.fullmatch(r'avp[0-9]{3}', ident) or f'assets/avatars/p1/{ident}.svg' not in sorties for ident in collection):
        raise ValueError('P1 : identifiant ou illustration de variante invalide')
    sorties['assets/js/ithakya-avatars-p1.js'] = 'window.ITH_AVATARS_P1 = ' + json.dumps(collection, ensure_ascii=False).replace('<', '\\u003c') + ';\n'
    portraits_p2 = json.loads(sorties['assets/avatars/p2/collection.json'])
    for ident, item in portraits_p2.items():
        if (not re.fullmatch(r'avq2[0-9]{2}', ident)
                or not re.fullmatch(r'av[0-9]{4}', item['parent'])
                or not os.path.isfile(os.path.join(site, 'assets/avatars', item['parent'] + '.svg'))
                or not all(os.path.isfile(os.path.join(site, 'assets/avatars/p2', f'{ident}-{taille}.webp'))
                           for taille in (64, 128, 256, 512))):
            raise ValueError('P2 : référence de portrait invalide : ' + ident)
    sorties['assets/js/ithakya-avatars-p2.js'] = 'window.ITH_AVATARS_P2 = ' + json.dumps(portraits_p2, ensure_ascii=False).replace('<', '\\u003c') + ';\n'
    hist = 'assets/js/ithakya-historique-catalogue-20261013.js'
    if hist in sorties:  # L20 : identité et durée des films depuis le catalogue
        ref_o, cur_o = oeuvres_actuelles(src)
        sorties[hist] = historique_catalogue(sorties[hist], ref_o, cur_o)
    # R14 : réutiliser les pilotes existants comme sources uniques des modules exploratoires.
    # Les copies distribuées dans site/assets sont générées ; pas de moteur parallèle.
    pilotroot = os.path.join(os.path.dirname(src), 'pilotes_isoles', 'assets')
    for js in sorted(glob.glob(os.path.join(pilotroot, 'js', 'pilote-*.js'))):
        sorties['assets/js/' + os.path.basename(js)] = lire(js)
    css_pilote = os.path.join(pilotroot, 'css', 'pilotes.css')
    if os.path.isfile(css_pilote):
        sorties['assets/css/ithakya-exploration.css'] = lire(css_pilote)
    # R13-F : les deux API PHP suivent désormais la même discipline canonique
    # que les fichiers du site. Les secrets et configurations privées n'entrent
    # JAMAIS dans cette génération.
    for f in sorted(glob.glob(os.path.join(src, 'serveur', '*.php'))):
        sorties['api/' + os.path.basename(f)] = lire(f)
    # Contrat AV-03 : interfaçage future production, textes déjà documentés dans le catalogue.
    # Ne crée ni média ni promesse d'activation de contenu absent.
    sorties['assets/data/contrat-narratif-av03.json'] = json.dumps(
        {'schema': 'ITHAKYA-AV03-v2', 'validation_editoriale': 'en_attente_work_av03',
         'elements': histoires_av03}, ensure_ascii=False, indent=2) + '\n'
    # PROGRAMMATION PRIVÉE — registre central validé, aucune publication automatique.
    # Tout ajout, retrait ou modification d'œuvre se propage sur toutes les pages
    # au prochain cycle de génération, sans éditer leurs sources HTML.
    from programmer_ithakya import load as _load_prog, published as _export_prog
    from pathlib import Path as _PathProg
    _registre = _load_prog(_PathProg(src) / 'programmation/registre.json', _PathProg(site))
    sorties['assets/data/programmation.json'] = json.dumps(
        _export_prog(_registre, _PathProg(site)), ensure_ascii=False, indent=2) + '\n'
    for _url, _html in list(sorties.items()):
        if not _url.endswith('.html') or _url == 'programmation.html':
            continue
        _root = '../' * _url.count('/')
        if '</head>' not in _html or '</body>' not in _html:
            continue
        if 'ithakya-programmation-live.js' in _html:
            continue
        _html = _html.replace('</head>',
            f'<link rel="stylesheet" href="{_root}assets/css/ithakya-programmation-live.css?sha=0">\n</head>', 1)
        _html = _html.replace('</body>',
            f'<script src="{_root}assets/js/ithakya-programmation-live.js?sha=0" data-root="{_root}" defer></script>\n</body>', 1)
        sorties[_url] = _html
    if data:
        # Les notes internes (réserves, origine des données) restent dans la source et ne sont pas publiées.
        def nettoyer(x):
            if isinstance(x, dict): return {k: nettoyer(v) for k, v in x.items() if k not in ('reserve', 'origine', 'question_origine', 'avertissement', 'autorisation_diffusion')}
            if isinstance(x, list): return [nettoyer(v) for v in x]
            return x
        sorties['assets/data/catalogue.json'] = json.dumps(nettoyer(enrichir(public, site)), ensure_ascii=False, indent=1) + '\n'
    return sorties


def etape_w360(sorties, src):
    """W360 — livraison des feuilles de style hors chemin critique de rendu.
    Données : source/w360/critique.json (outil w360_critique.cjs : règles RÉELLEMENT utilisées au chargement, mesurées dans un navigateur sur la pile réelle).
    Pour chaque séquence de feuilles locales consécutives de l'en-tête (séparées uniquement par un <style> en ligne) :
      1. une copie « critique » (mêmes règles, même ordre) est insérée en ligne juste avant la première feuille ;
      2. chaque feuille d'origine RESTE à sa place dans le document (la cascade finale est donc identique) mais est déclarée media="print" avec son adresse en data-href : assets/w360-css.js
         démarre son téléchargement APRÈS l'affichage du contenu principal (pour ne pas lui disputer la bande passante), puis les active toutes ensemble : elles ne bloquent plus le premier rendu ;
      3. un <noscript> reprend les feuilles d'origine (navigation sans JavaScript).
    Aucune règle de style n'est modifiée ni supprimée ; si la structure d'une page ne correspond plus aux données, la page n'est pas touchée.
    Désactivation : supprimer source/w360/critique.json ou W360_DESACTIVER=1 (retour exact à l'état V1 FINAL)."""
    f = os.path.join(src, 'w360', 'critique.json')
    if not os.path.isfile(f) or os.environ.get('W360_DESACTIVER') == '1':
        return sorties
    donnees = json.load(open(f, encoding='utf-8'))['pages']
    rx = re.compile(r'<link\b[^>]*>|<style\b[^>]*>[\s\S]*?</style>', re.I)
    for page, groupes in sorted(donnees.items()):
        html = sorties.get(page)
        if not html or '</head>' not in html or 'data-w360' in html:
            continue
        fin = html.index('</head>'); tete = html[:fin]
        runs, cur = [], []
        for m in rx.finditer(tete):
            t = m.group(0)
            if t[:6].lower() == '<style':
                if cur: runs.append(cur)
                cur = []
                continue
            if not re.search(r'\brel=["\']stylesheet["\']', t, re.I) or re.search(r'\bmedia=', t, re.I):
                continue
            h = re.search(r'\bhref=["\']([^"\']+)["\']', t)
            if not h or re.match(r'^(https?:)?//', h.group(1), re.I):
                continue
            cur.append((m.start(), m.end(), h.group(1), t))
        if cur: runs.append(cur)
        if [[x[2] for x in r] for r in runs] != [g['hrefs'] for g in groupes]:
            print('W360 : structure différente, page inchangée', page)
            continue
        for run, g in reversed(list(zip(runs, groupes))):
            originaux = ''.join(x[3] for x in run)
            apres = '<noscript>' + re.sub(r'\sid="[^"]*"', '', originaux) + '</noscript>'   # repli sans JavaScript : sans attribut id (pas d'identifiant dupliqué dans le document)
            tete = tete[:run[-1][1]] + apres + tete[run[-1][1]:]
            for (a, b, h, t) in reversed(run):
                tete = tete[:a] + re.sub(r'\bhref=', 'data-href=', t.replace('<link', '<link media="print" data-w360="1"', 1), count=1) + tete[b:]
            css = g['css'].replace('</style', '<\\/style')
            if css:
                tete = tete[:run[0][0]] + '<style data-w360="critique">' + css + '</style>' + tete[run[0][0]:]
        racine = '../' * page.count('/')
        sorties[page] = tete + '<script defer src="' + racine + 'assets/w360-css.js"></script>\n' + html[fin:]
    return sorties


def etape_w360_quatre(sorties, src):
    """W360 v2.2 — voir source/outils/w360_quatre_univers.py (retrait côté présentation, créateurs/œuvres/données conservés)."""
    import importlib.util
    chemin = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'w360_quatre_univers.py')
    if not os.path.isfile(chemin):
        return sorties
    spec = importlib.util.spec_from_file_location('w360_quatre_univers', chemin); mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod.appliquer(sorties, src)


def etape_w360_lcp(sorties, src):
    """W360 — priorité de chargement de l'image LCP (élément le plus grand du premier écran), identifiée par mesure (Lighthouse, source/w360/lcp.json).
    Seuls des ATTRIBUTS de chargement sont ajoutés à une balise <img> existante : fetchpriority="high" et, pour une image du premier écran, retrait de loading="lazy".
    Ni l'image, ni son cadrage, ni ses dimensions, ni son texte alternatif ne sont modifiés."""
    f = os.path.join(src, 'w360', 'lcp.json')
    if not os.path.isfile(f) or os.environ.get('W360_DESACTIVER') == '1':
        return sorties
    for page, items in sorted(json.load(open(f, encoding='utf-8'))['pages'].items()):
        html = sorties.get(page)
        if not html:
            continue
        for it in items:
            m = re.search(r'<img\b[^>]*\bsrc="' + re.escape(it['src']) + r'"[^>]*>', html)
            if not m:
                print('W360 lcp : image introuvable', page, it['src'])
                continue
            tag = m.group(0); neuf = tag
            if 'fetchpriority=' not in neuf:
                neuf = neuf.replace('<img', '<img fetchpriority="high"', 1)
            if it.get('retirer_lazy'):
                neuf = re.sub(r'\sloading="lazy"', '', neuf)
            html = html[:m.start()] + neuf + html[m.end():]
        sorties[page] = html
    return sorties


def etape_w360_premium(sorties, src):
    """W360 — couches de présentation insérées en ligne à la fin de l'en-tête de chaque page (aucune requête réseau supplémentaire) :
    - source/w360/premium.css : continuité de navigation (transitions entre pages, en-tête et barre de navigation stables) ;
    - source/w360/ergonomie.css : lisibilité et surface de toucher des composants d'interface.
    Aucun contenu n'est touché. Désactivation : supprimer le fichier concerné ou W360_DESACTIVER=1."""
    if os.environ.get('W360_DESACTIVER') == '1':
        return sorties
    for nom in ('premium', 'ergonomie', 'quatre'):
        f = os.path.join(src, 'w360', nom + '.css')
        if not os.path.isfile(f):
            continue
        css = re.sub(r'/\*.*?\*/', '', open(f, encoding='utf-8').read(), flags=re.S)
        css = re.sub(r'\s+', ' ', css).strip()
        balise = 'data-w360="%s"' % nom
        for page, html in sorted(sorties.items()):
            if not page.endswith('.html') or '</head>' not in html or balise in html:
                continue
            if nom == 'quatre' and not re.search(r'class="[^"]*(?:xp360-door-grid|ithu-choix-rapide|s4-terr|p4d-envies)', html):
                continue   # uniquement les pages qui utilisent ces composants
            sorties[page] = html.replace('</head>', '<style %s>%s</style></head>' % (balise, css), 1)
    return sorties


STYLE_CORPS = re.compile(r'<link\b[^>]*\brel="stylesheet"[^>]*>|<style\b[^>]*>.*?</style>', re.S | re.I)


def styles_en_tete(texte):
    """L19 / P0 stabilité — Les feuilles (<link rel=stylesheet>) et blocs <style> placés dans <body> sont remontés
    à la fin de <head>, dans leur ordre d'origine. Cause racine mesurée : le navigateur peint le contenu situé avant
    une feuille de corps, puis le restyle à son arrivée (décalage de mise en page, CLS 0,2254 sur l'accueil).
    L'ordre relatif de TOUTES les sources de style est conservé : la cascade est identique par construction
    (vérifié par comparaison des styles calculés). Les blocs situés dans <noscript> ou <template> restent en place."""
    fin_tete = texte.find('</head>')
    if fin_tete < 0:
        return texte
    tete, corps = texte[:fin_tete], texte[fin_tete:]
    remontes, morceaux, pos = [], [], 0
    for m in STYLE_CORPS.finditer(corps):
        avant = corps[:m.start()].lower()
        if (avant.count('<noscript') > avant.count('</noscript>') or avant.count('<template') > avant.count('</template>')
                or len(re.findall(r'<script\b', avant)) > avant.count('</script>')):  # chaîne JS contenant du HTML
            continue
        morceaux.append(corps[pos:m.start()]); remontes.append(m.group(0)); pos = m.end()
    if not remontes:
        return texte
    morceaux.append(corps[pos:])
    return tete + '\n'.join(remontes) + '\n' + ''.join(morceaux)


UNIVERS_PAGES = {'demos/01-signature.html': 'signature', 'demos/02-pop-culture.html': 'pop',
                 'demos/03-progression.html': 'progression', 'demos/05-soleil-xl.html': 'soleil'}
UNIVERS_NOMS = [('signature', r'SIGNATURE|Signature|01-signature|oeuvres/signature'), ('pop', r'POP|Pop Culture|02-pop-culture|oeuvres/pop'),
                ('progression', r'PROGRESSION|Progression|03-progression|oeuvres/progression'), ('soleil', r'SOLEIL|Soleil XL|05-soleil-xl|oeuvres/soleil')]


def _num(v):
    return str(int(v)) if float(v).is_integer() else str(v)


def _horloge(s):
    n = int(s); return f'{n // 60}:{n % 60:02d}'


def _duree(d, long_form=False):
    """Même règle que l'affichage du catalogue (enrichir) : « 21 s » sous 90 s, sinon « 9 min » / « 9 min 05 »."""
    d = int(round(d))
    if d < 90:
        return f'{_num(d)} secondes' if long_form else f'{_num(d)} s'
    return f'{int(d) // 60} min' + (f' {int(d) % 60:02d}' if int(d) % 60 else '')


def oeuvres_actuelles(src):
    """Durées et cinq idées par univers, lues dans le catalogue (source unique) ; référence de repérage L19."""
    cat = {x['id']: x for x in json.load(open(os.path.join(src, 'catalogue', 'catalogue.json'), encoding='utf8'))['contenus']}
    ref = json.load(open(os.path.join(src, 'catalogue', 'references_gabarits_l19.json'), encoding='utf8'))
    cur = {}
    for u in ('signature', 'pop', 'progression', 'soleil'):
        lo, co = cat[u + '.long'], cat[u + '.court']
        ch = lo.get('chapitres') or []
        if len(ch) != 5:  # cinq idées par Long : règle produit (ITP_CONTEXTS côté serveur)
            raise SystemExit(f'catalogue : {u}.long doit compter exactement 5 chapitres (trouvé {len(ch)})')
        starts = [c['debut_s'] for c in ch]
        if starts != sorted(starts) or starts[0] != 0 or starts[-1] >= lo['duree_s']:
            raise SystemExit(f'catalogue : chapitres de {u}.long non ordonnés ou hors durée ({starts}, durée {lo["duree_s"]})')
        cur[u] = {'court_s': co['duree_s'], 'long_s': lo['duree_s'], 'chapitres': [{'s': c['debut_s'], 't': c['titre']} for c in ch],
                  'court_sha256': co.get('media_sha256') or ref[u]['court_sha256'], 'long_sha256': lo.get('media_sha256') or ref[u]['long_sha256']}
    return ref, cur


def chapitres_dans_page(texte, r, c):
    """L20 — Les cinq idées du Long (temps, titres) viennent du catalogue. Avec un catalogue identique à la référence,
    la page est inchangée à l'octet près (vérifié par generer.py --verifier)."""
    R, C = r['chapitres'], c['chapitres']
    ends_r = [x['s'] for x in R[1:]] + [r['long_s']]; ends_c = [x['s'] for x in C[1:]] + [c['long_s']]
    for i, (a, b) in enumerate(zip(R, C), 1):
        rs, cs, ra, ca = _num(a['s']), _num(b['s']), _horloge(a['s']), _horloge(b['s'])
        def btn(m):
            blk = m.group(0).replace(f'data-ith76-start="{rs}" data-ith76-chapter="{i}"', f'data-ith76-start="{cs}" data-ith76-chapter="{i}"')
            blk = blk.replace(f'Lire l’idée {i}, {a["t"]}, à {ra}', f'Lire l’idée {i}, {b["t"]}, à {ca}').replace(f'Lire l’idée {i} à {ra}', f'Lire l’idée {i} à {ca}')
            blk = blk.replace(f'Idée {i} · {ra}', f'Idée {i} · {ca}')
            return blk.replace(a['t'], b['t']) if a['t'] != b['t'] else blk
        texte = re.sub(r'<button[^>]*data-ith76-start="' + re.escape(rs) + r'" data-ith76-chapter="' + str(i) + r'".*?</button>', btn, texte, flags=re.S)
        texte = texte.replace(f'Idée {i} · {ra}', f'Idée {i} · {ca}')
        dump = lambda s: json.dumps(s, ensure_ascii=False)
        texte = texte.replace(f'{{"s": {rs}, "e": {_num(ends_r[i - 1])}, "t": {dump(a["t"])}}}', f'{{"s": {cs}, "e": {_num(ends_c[i - 1])}, "t": {dump(b["t"])}}}')
        texte = texte.replace(f'{{"s": {rs}, "t": {dump(a["t"])}}}', f'{{"s": {cs}, "t": {dump(b["t"])}}}')
        texte = texte.replace(f'{{"n": {i}, "t": {dump(a["t"])}, "at": "{ra}", "s": {rs}}}', f'{{"n": {i}, "t": {dump(b["t"])}, "at": "{ca}", "s": {cs}}}')
    return texte


DUREE_MOT = re.compile(r'\b(Court|COURT|Long|LONG|Aller plus loin)([^<"\n]{0,25}?)\b(\d+(?:\.\d+)?)( à (\d+))?([ \u00a0])(s|secondes)\b')


def durees_dans_page(texte, ref, cur, univers=None):
    """L20 — Les durées affichées viennent du catalogue. L'univers d'une mention est celui de la page, sinon le dernier
    nom d'univers cité dans les 400 caractères précédents ; sans univers identifiable, la mention est une fourchette."""
    def rempl(m):
        kind = 'court_s' if m.group(1).lower() == 'court' else 'long_s'
        u = univers
        if not u:
            ctx = texte[max(0, m.start() - 400):m.start()]; best = -1
            for uid, rx in UNIVERS_NOMS:
                for mm in re.finditer(rx, ctx):
                    if mm.start() > best: best, u = mm.start(), uid
        long_form = m.group(7) == 'secondes'; sep = m.group(6)
        fmt = lambda d: _duree(d, long_form).replace(' ', sep, 1) if d < 90 else _duree(d, long_form).replace(' ', sep)
        if u:
            if float(m.group(3)) != float(ref[u][kind]):
                return m.group(0)  # valeur étrangère à la référence : inchangée
            return m.group(1) + m.group(2) + fmt(cur[u][kind])
        vals = sorted({cur[x][kind] for x in cur}); rvals = sorted({ref[x][kind] for x in ref if not x.startswith('_')})
        attendu = (str(rvals[0]) + (' à ' + str(rvals[-1]) if len(rvals) > 1 else ''))
        trouve = m.group(3) + (m.group(4) or '')
        if trouve != attendu:
            return m.group(0)
        if len(vals) == 1:
            return m.group(1) + m.group(2) + fmt(vals[0])
        a, b = fmt(vals[0]), fmt(vals[-1])
        if vals[-1] < 90:
            a = a[:-len(sep + ('secondes' if long_form else 's'))]
        return m.group(1) + m.group(2) + a + ' à ' + b
    return DUREE_MOT.sub(rempl, texte)


def empreintes_medias(texte, ref, cur):
    """L20 — Empreinte SHA-256 de chaque film (data-media-sha256, reprise) et son préfixe de cache (?sha=) : celles du
    catalogue (media_sha256, écrit par outils_reprise/integrer_av05_l20.py) remplacent celles de référence."""
    for u in cur:
        for k in ('court_sha256', 'long_sha256'):
            a, b = ref[u][k], cur[u][k]
            if a != b:
                texte = texte.replace(a, b).replace('?sha=' + a[:12], '?sha=' + b[:12])
    return texte


def historique_catalogue(texte, ref, cur):
    """L20 — Catalogue historique des films (identité et durée attendues par la reprise d'onglet) dérivé du catalogue."""
    m = re.search(r'(window\.ITHAKYA_HISTORY_CATALOG=)(\[.*?\])(\.concat)', texte, re.S)
    if not m:
        raise SystemExit('catalogue historique : structure inattendue')
    items = json.loads(m.group(2))
    page_u = {p.split('/')[-1][:-5]: u for p, u in UNIVERS_PAGES.items()}
    for it in items:
        u = page_u.get(it.get('page')); kind = (it.get('kind') or '').lower()
        if u and kind in ('court', 'long'):
            it['sha256'] = cur[u][kind + '_sha256']
            d = cur[u][kind + '_s']; it['duration'] = int(d) if float(d).is_integer() else d
    return texte[:m.start(2)] + json.dumps(items, ensure_ascii=False, separators=(',', ':')) + texte[m.end(2):]


def oeuvres_dans_pages(pages, src):
    ref, cur = oeuvres_actuelles(src)
    out = {}
    for p, t in pages.items():
        u = UNIVERS_PAGES.get(p)
        if u:
            t = chapitres_dans_page(t, ref[u], cur[u])
        out[p] = empreintes_medias(durees_dans_page(t, ref, cur, u), ref, cur)
    return out


LIEN_CSS = re.compile(r'<link\b[^>]*\brel="stylesheet"[^>]*>')
URL_CSS = re.compile(r'url\(\s*(["\']?)([^)"\']+)\1\s*\)')


def surcouche_m08(pages, src):
    """M09 — parité source/site : les apports M01–M08 (sections « Monde », feuilles d'avatars, panneaux M02) avaient été
    publiés directement dans site/ sans source. Ils sont désormais déclarés dans source/composants/surcouche_m08.json et
    insérés en dernière passe, après une ancre de lignes UNIQUE ; toute ancre absente ou ambiguë fait échouer la génération."""
    chemin = os.path.join(src, 'composants', 'surcouche_m08.json')
    if not os.path.isfile(chemin):
        return pages
    regles = json.load(open(chemin, encoding='utf8'))['regles']
    for r in regles:
        p = r['page']
        if p not in pages:
            raise ValueError('Surcouche M08 : page absente ' + p)
        lignes = pages[p].split('\n')
        norm = [re.sub(r'\?sha=[0-9a-f]+', '?sha=', x) for x in lignes]
        a, n = r['apres'], len(r['apres'])
        pos = [k for k in range(len(norm) - n + 1) if norm[k:k + n] == a]
        if len(pos) != 1:
            raise ValueError(f'Surcouche M08 : ancre {"absente" if not pos else "ambiguë"} dans {p} : {a[-1][:80]!r}')
        k = pos[0] + n
        pages[p] = '\n'.join(lignes[:k] + r['inserer'] + lignes[k:])
    return pages


def surcouche_m14(pages, src):
    """M14 : les apports M12–M14 (portraits de préproduction, bloc mémoire, feuilles de finition) avaient été publiés dans
    site/ sans source, par une réécriture des pages qui altérait aussi l'ordre des attributs. Ils sont déclarés dans
    source/composants/surcouche_m14.json (fragments dans source/composants/m14/) et insérés en dernière passe, avant une
    ancre UNIQUE ; toute ancre absente ou ambiguë fait échouer la génération."""
    chemin = os.path.join(src, 'composants', 'surcouche_m14.json')
    if not os.path.isfile(chemin):
        return pages
    for r in json.load(open(chemin, encoding='utf8'))['regles']:
        p, ancre = r['page'], r['avant']
        if p not in pages:
            raise ValueError('Surcouche M14 : page absente ' + p)
        if pages[p].count(ancre) != 1:
            raise ValueError(f'Surcouche M14 : ancre {"absente" if ancre not in pages[p] else "ambiguë"} dans {p} : {ancre!r}')
        if 'fragments' in r:
            bloc = ''.join(lire(os.path.join(src, 'composants', f)).rstrip('\n') + '\n' for f in r['fragments'])
        else:
            bloc = '\n'.join(r['liens']) + '\n'
        pages[p] = pages[p].replace(ancre, bloc + ancre, 1)
    return pages


def entree_active(pages, src):
    """A2 : l'entrée de navigation (Découvrir · Participer · Gagner · Mon ITHAKYA) dont dépend la page est marquée aria-current
    dans la navigation commune, d'après la carte source/composants/m14/entrees_carte.json (même carte que le repère de page).
    Échec explicite si le marqueur de l'entrée est absent ou ambigu."""
    chemin = os.path.join(src, 'composants', 'm14', 'entrees_carte.json')
    if not os.path.isfile(chemin):
        return pages
    for p, (eid, _lib, _comp) in json.load(open(chemin, encoding='utf8')).items():
        if p not in pages and os.path.isfile(os.path.join(src, 'ux360_overlay', p)):
            continue
        if p not in pages:
            raise ValueError('Carte des entrées : page absente ' + p)
        marque = f'data-a2="{eid}"'
        if pages[p].count(marque) != 1:
            raise ValueError(f'Entrée active : marqueur {"absent" if marque not in pages[p] else "ambigu"} dans {p} : {marque!r}')
        pages[p] = pages[p].replace(marque, marque + ' aria-current="true"', 1)
    return pages


def harmonie_p2(pages, css, portraits):
    """Même langage visuel, avec une ambiance par usage et un accent par territoire."""
    version = hashlib.sha256(css.encode('utf8')).hexdigest()[:12]
    version_portraits = hashlib.sha256(portraits.encode('utf8')).hexdigest()[:12]
    ambiances = {
        'index.html': 'accueil', 'univers.html': 'territoires', 'communaute.html': 'communaute',
        'mon-ithakya.html': 'profil', 'lounge.html': 'lounge', 'traversee.html': 'traversee',
        'programmation.html': 'programmation', 'programme.html': 'programme', 'programme-soleil-xl.html': 'programme',
        'recherche.html': 'recherche', '404.html': 'recherche', 'cest-quoi.html': 'guide',
        'mentions-legales.html': 'mentions',
    }
    par_dossier = {'demos': 'lecture', 'oeuvres': 'oeuvres', 'territoires': 'territoires',
                   'exploration': 'exploration', 'createurs': 'oeuvres'}
    for page, contenu in pages.items():
        ambiance = ambiances.get(page, par_dossier.get(page.split('/')[0], 'guide'))
        corps = re.sub(r'<body(?=[ >])', f'<body data-p2-espace="{ambiance}"', contenu, count=1)
        racine = '../' * page.count('/')
        feuille = f'<link rel="stylesheet" href="{racine}assets/css/ithakya-p2-harmonie.css?sha={version}">\n'
        registre = f'<script defer src="{racine}assets/js/ithakya-avatars-p2.js?sha={version_portraits}"></script>\n'
        pages[page] = corps.replace('</head>', feuille + registre + '</head>', 1)
    return pages


def continuite_p3(pages, src, css):
    """Ajoute le repère éditorial et la suite propres aux 29 pages documentées."""
    parcours = json.loads(lire(os.path.join(src, 'catalogue', 'parcours-p3.json')))
    absentes = parcours.keys() - pages.keys()
    if absentes:
        raise ValueError('Parcours P3 absent : ' + ', '.join(sorted(absentes)))
    version = hashlib.sha256(css.encode('utf8')).hexdigest()[:12]
    signes = {'Horizon': 'horizon', 'Seuil': 'seuil', 'Trace': 'trace',
              'Présence': 'presence', 'Résonance': 'resonance'}
    for page, entree in parcours.items():
        contenu = pages[page]
        racine = '../' * page.count('/')
        signe = signes[entree['signe']]
        href = racine + entree['destination']
        feuille = f'<link rel="stylesheet" href="{racine}assets/css/ithakya-p3-convergence.css?sha={version}">\n'
        bloc = (f'<aside class="p3-fil" data-p3-signe="{signe}" aria-labelledby="p3-fil-repere">'
                f'<div><p id="p3-fil-repere" class="p3-fil-repere">{html.escape(entree["signe"])}</p>'
                f'<p>{html.escape(entree["texte"])}</p></div>'
                f'<a href="{html.escape(href, quote=True)}">{html.escape(entree["action"])} <span aria-hidden="true">↗</span></a>'
                '</aside>\n')
        if contenu.count('</main>') != 1:
            raise ValueError('P3 : zone principale absente ou ambiguë : ' + page)
        contenu = re.sub(r'<body(?=[ >])', f'<body data-p3-signe="{signe}"', contenu, count=1)
        pages[page] = contenu.replace('</head>', feuille + '</head>', 1).replace('</main>', bloc + '</main>', 1)
    return pages


def css_en_lots(pages, site, sorties):
    """L20 / performance — Chaque séquence de feuilles locales de <head> non séparées par un bloc <style> devient un lot
    unique (assets/css/lot-<empreinte>.css), concaténé dans le même ordre : la cascade est identique par construction
    (vérifié par comparaison des styles calculés). url() relatives réécrites vers le dossier du lot ; @charset retiré.
    Séquence laissée intacte si une feuille contient @import, porte un media autre que « all », ou est absente."""
    lots, out = {}, {}
    def contenu(rel):
        return sorties[rel] if rel in sorties else (lire(os.path.join(site, rel)) if os.path.isfile(os.path.join(site, rel)) else None)
    for p, t in pages.items():
        fin = t.find('</head>')
        if fin < 0:
            out[p] = t; continue
        tete, corps = t[:fin], t[fin:]
        racine = '../' * p.count('/')
        jetons = list(re.finditer(r'<style\b.*?</style>|' + LIEN_CSS.pattern, tete, re.S))
        seqs, cur = [], []
        for m in jetons:
            if m.group(0).startswith('<style'):
                if cur: seqs.append(cur); cur = []
            else:
                cur.append(m)
        if cur: seqs.append(cur)
        remplacements = []
        for seq in seqs:
            if len(seq) < 2: continue
            parts, ok = [], True
            for m in seq:
                tag = m.group(0); href = re.search(r'href="([^"]+)"', tag)
                media = re.search(r'media="([^"]+)"', tag)
                if not href or (media and media.group(1).strip() != 'all') or re.match(r'^(https?:)?//', href.group(1)):
                    ok = False; break
                rel = os.path.normpath(os.path.join(os.path.dirname(p), href.group(1).split('?')[0])).replace(os.sep, '/')
                css = contenu(rel)
                if css is None or '@import' in css:
                    ok = False; break
                base = os.path.dirname(rel)
                def rebase(u, base=base):
                    v = u.group(2).strip()
                    if re.match(r'^(data:|https?:|//|/|#)', v): return u.group(0)
                    cible = os.path.normpath(os.path.join(base, v.split('#')[0].split('?')[0])).replace(os.sep, '/')
                    suite = v[len(v.split('#')[0].split('?')[0]):]
                    return 'url(' + u.group(1) + os.path.relpath(cible, 'assets/css').replace(os.sep, '/') + suite + u.group(1) + ')'
                css = re.sub(r'@charset\s+"[^"]*";\s*', '', css)
                parts.append(f'/* ── {rel} ── */\n' + URL_CSS.sub(rebase, css))
            if not ok: continue
            texte = '\n'.join(parts) + '\n'
            h = hashlib.sha256(texte.encode('utf8')).hexdigest()[:12]
            nom = f'assets/css/lot-{h}.css'; lots[nom] = texte
            remplacements.append((seq, f'<link rel="stylesheet" href="{racine}{nom}?sha={h}">'))
        for seq, balise in reversed(remplacements):  # de la fin vers le début : positions stables
            tete = tete[:seq[0].start()] + balise + ''.join(
                tete[seq[i].end():seq[i + 1].start()] for i in range(len(seq) - 1)) + tete[seq[-1].end():]
        out[p] = tete + corps
    return out, lots


def neutraliser_medias_absents(pages, catalogue, site):
    """UX360 : retirer le src du HTML quand le MP4 manque (et préserver la provenance).

    Sur la fiche historique, le script d'état média redirige le bouton de lecture
    vers la fiche éditoriale. Aucun droit, média, point, session ou route n'est créé.
    Dès l'intégration AV autorisée et une régénération, le src d'origine redevient actif.
    """
    contextes = {'signature':'demos/01-signature.html','pop':'demos/02-pop-culture.html',
                 'progression':'demos/03-progression.html','soleil':'demos/05-soleil-xl.html'}
    contenu = {c.get('id'): c for c in catalogue.get('contenus', [])}
    for univers, page in contextes.items():
        texte = pages.get(page)
        if not texte: continue
        for format in ('court', 'long'):
            c = contenu[univers+'.'+format]
            if media_disponible(site, c): continue
            vid = 'courtVideo' if format=='court' else 'longVideo'
            rex = re.compile(r'<video\b[^>]*\bid="'+vid+r'"[^>]*>',re.I|re.S)
            correspondance = rex.search(texte)
            if not correspondance:
                raise ValueError('Vidéo historique introuvable : '+page+' / '+vid)
            tag = correspondance.group(0)
            attr = re.search(r'(?<![\w-])src="([^"]+)"',tag)
            if attr:
                tag = tag.replace(attr.group(0),'data-r163-original-src="'+html.escape(attr.group(1),quote=True)+'"',1)
            if 'data-r163-missing-from-package=' not in tag:
                tag = tag[:-1]+' data-r163-missing-from-package="true">'
            texte = texte[:correspondance.start()]+tag+texte[correspondance.end():]
        # Conserver le parcours direct vers la fiche, sans glyph de lecture trompeur.
        if not media_disponible(site, contenu[univers+'.court']):
            texte = texte.replace('<span class="ux79-court-play">▶</span>',
                                  '<span class="ux79-court-play" aria-hidden="true">↗</span>')
            texte = re.sub(r'(<button\b[^>]*\bid="openCourt"[^>]*>)[^<]*(?=</button>)',
                           lambda m: re.sub(r'\saria-label="[^"]*"', '', m.group(1)) + 'Explorer la fiche du Court',
                           texte, count=1)
        pages[page]=texte
    return pages


def position_en_tete(chemin, texte):
    """L19 / P0 stabilité — Module de restauration de position (assets/js/ithakya-position-l19.js) chargé tôt dans <head>
    de chaque page, afin d'écouter « pagehide » et le « load » de toutes les pages. Idempotent."""
    if 'ithakya-position-l19.js' in texte or '</head>' not in texte:
        return texte
    racine = '../' * chemin.count('/')
    balise = f'<script defer src="{racine}assets/js/ithakya-position-l19.js?sha=0"></script>'  # defer : exécuté avant « load », sans bloquer le rendu
    if chemin in UNIVERS_PAGES:  # L20 : reprise du Long à la dernière position
        balise += f'\n<script defer src="{racine}assets/js/ithakya-reprise-l20.js?sha=0"></script>'
    if '<video' in texte or "createElement('video')" in texte or 'ith81-play' in texte:  # L21 : chaîne de lecture
        balise += f'\n<script defer src="{racine}assets/js/ithakya-lecture-l21.js?sha=0"></script>'
    return texte.replace('</head>', balise + '\n</head>', 1)


def rendus_declares(src):
    """L21 — Rendus de diffusion DÉCLARÉS au catalogue (champ « rendus » d'une œuvre : {"p540": true, "hls": true}), écrit
    par integrer_av05_l20.py --rendus. Clé = nom du fichier de référence sans extension. Vide aujourd'hui."""
    cat = json.load(open(os.path.join(src, 'catalogue', 'catalogue.json'), encoding='utf-8'))
    out = {}
    for c in cat.get('contenus', []):
        r = c.get('rendus')
        if isinstance(r, dict) and c.get('media'):
            out[os.path.splitext(os.path.basename(c['media']))[0]] = {k: bool(r[k]) for k in ('p540', 'hls') if k in r}
    return out


def rendus_en_tete(texte, rendus):
    """L21 — window.ITHAKYA_RENDUS, en tout début de <head> (avant le choix des sources) ; rien si aucun rendu déclaré."""
    if not rendus or 'ITHAKYA_RENDUS' in texte or '<head>' not in texte:
        return texte
    js = json.dumps(rendus, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return texte.replace('<head>', f'<head><script id="ithakya-rendus-l21">window.ITHAKYA_RENDUS={js};</script>', 1)


LISIBILITE = re.compile(r'<script id="ithakya-v9951-fs"[^>]*>.*?</script>', re.S)


def lisibilite_en_tete(texte):
    """L19 / P0 stabilité — Le script de lisibilité (texte < 12 px porté à 12 px) est placé à la fin de <head>, après les
    feuilles de style : sinon le contenu situé avant lui est peint en 9 px puis agrandi (décalage mesuré sur Pop Culture).
    En tête, il traite chaque nœud dès son insertion par le parseur (MutationObserver sur la racine), avant le rendu."""
    m = LISIBILITE.search(texte)
    fin = texte.find('</head>')
    if not m or fin < 0 or m.start() < fin:
        return texte
    sans = texte[:m.start()] + texte[m.end():]
    return sans.replace('</head>', m.group(0) + '\n</head>', 1)


def medias_dans_surcouche(nom, texte, genere, contenus, site):
    """Recoller les états média calculés aux pages UX360, qui conservent leur mise en page."""
    demos = {
        'demos/01-signature.html': 'signature', 'demos/02-pop-culture.html': 'pop',
        'demos/03-progression.html': 'progression', 'demos/05-soleil-xl.html': 'soleil',
    }
    programmes = {
        'programme.html': [('programmeVideo', 'pop.pilote')],
        'programme-soleil-xl.html': [('programmeVideo', 'soleil.extrait'), ('soleilPilotVideo', 'soleil.pilote')],
    }
    univers = demos.get(nom)
    if univers:
        garde = ('<button type="button" class="text-link ith10003-keep-early" '
                 'aria-pressed="false" disabled>Garder cette découverte</button>')
        texte, nombre = re.subn(r'(<span class="ux79-court-next">[^<]*</span>)',
                                lambda m: m[1] + garde, texte, count=1)
        if nombre != 1:
            raise ValueError('Emplacement du bouton Garder absent : ' + nom)
        court = media_disponible(site, contenus[univers + '.court'])
        long = media_disponible(site, contenus[univers + '.long'])
        if not (court and long):
            indisponible = 'Films indisponibles' if not (court or long) else (
                'Long indisponible' if court else 'Court indisponible')
            texte = re.sub(r'(<span class="ux79-court-next">)[^<]*',
                           lambda m: m[1] + indisponible, texte, count=1)
        if not court and 'id="r13-recits-titre"' in texte:
            texte = re.sub(r'(<button\b[^>]*\bid="openCourt"[^>]*>)[^<]*',
                           lambda m: re.sub(r'\saria-label="[^"]*"', '', m[1]) + 'Lire les repères',
                           texte, count=1)
    fiches = {'oeuvres/' + uid + '.html': (uid, route) for route, uid in demos.items()}
    if nom in fiches:
        uid, route = fiches[nom]
        for format_video in ('court', 'long'):
            if not media_disponible(site, contenus[uid + '.' + format_video]):
                continue
            label = format_video.title()
            lien = (f'<a class="recomp-action" href="../{route}?view={format_video}#{format_video}Video">'
                    f'Voir le {label} <span aria-hidden="true">↗</span></a>')
            note = f'<p class="ith15-etat" role="note">{label} indisponible.</p>'
            motif = re.escape(note)
            if format_video == 'court':
                motif += r'<a class="recomp-action" href="\.\./demos/[^"]+">.*?</a>'
            texte, remplacés = re.subn(motif, lambda _: lien, texte, count=1)
            if remplacés != 1:
                raise ValueError('État média attendu absent sur la fiche : ' + nom + ' / ' + format_video)
        texte = tete_fiche_disponible(texte, nom, site, contenus, uid)
    cibles = [('courtVideo', univers + '.court'), ('longVideo', univers + '.long')] if univers else programmes.get(nom, [])
    for identifiant, contenu in cibles:
        if not media_disponible(site, contenus[contenu]):
            continue
        balise = re.compile(r'<video\b[^>]*\bid="' + identifiant + r'"[^>]*>')
        source = balise.search(genere).group(0)
        texte = balise.sub(lambda _: source, texte, count=1)
        if univers:
            format_video = contenu.rsplit('.', 1)[1]
            texte = texte.replace(f'data-av03-{format_video}-fichier="absent"',
                                  f'data-av03-{format_video}-fichier="present"', 1)
        if identifiant == 'courtVideo':
            commande = re.compile(r'<button\b[^>]*\bid="openCourt"[^>]*>[^<]*</button>')
            bouton = commande.search(genere).group(0)
            texte = commande.sub(lambda _: bouton, texte, count=1)
            texte = texte.replace('<span class="ux79-court-play" aria-hidden="true">↗</span>',
                                  '<span class="ux79-court-play" aria-hidden="true">▶</span>', 1)
        if not univers:
            avis = re.compile(r'<p\b[^>]*data-video-status-for="' + re.escape(contenu) + r'"[^>]*>.*?</p>', re.S)
            nouveaux = iter(avis.findall(genere))
            texte = avis.sub(lambda _: next(nouveaux), texte)
    return texte


def medias_dans_tete(nom, texte, genere, contenus, site):
    """V6 / D1 — Recoller sur une page de la tête validée les états média calculés par le générateur.

    Sans effet tant qu'aucun média concerné n'est présent : la page figée est alors rendue à l'octet près.
    Dès qu'un fichier référencé au catalogue est présent, seuls les fragments qui dépendent du média sont
    repris de la page générée (balise <video>, commande du Court, mention de disponibilité, liens de fiche).
    Chaque reprise est stricte : un emplacement introuvable interrompt la génération au lieu d'être ignoré.
    """
    demos = {
        'demos/01-signature.html': 'signature', 'demos/02-pop-culture.html': 'pop',
        'demos/03-progression.html': 'progression', 'demos/05-soleil-xl.html': 'soleil',
    }
    programmes = {
        'programme.html': [('programmeVideo', 'pop.pilote')],
        'programme-soleil-xl.html': [('programmeVideo', 'soleil.extrait'), ('soleilPilotVideo', 'soleil.pilote')],
    }

    def reprendre(motif, page, drapeaux=0):
        modele = re.compile(motif, drapeaux)
        source = modele.search(genere)
        if source is None:
            raise ValueError('État média absent de la page générée : ' + nom + ' / ' + motif)
        page, nombre = modele.subn(lambda _: source.group(0), page, count=1)
        if nombre != 1:
            raise ValueError('État média absent de la tête validée : ' + nom + ' / ' + motif)
        return page

    univers = demos.get(nom)
    if univers:
        presents = [f for f in ('court', 'long') if media_disponible(site, contenus.get(univers + '.' + f))]
        # Disponibilité connue avant l'analyse des lecteurs, pour le premier rendu.
        if 'class="ith-w360-formats-nav"' in texte:
            texte, nombre = re.subn(r'(class="ith-w360-formats-nav" data-w360-formats=")[^"]*(")',
                                    lambda m: m[1] + ' '.join(presents) + m[2], texte, count=1)
            if nombre != 1:
                raise ValueError('Disponibilité des liens de formats absente de la tête validée : ' + nom)
        if presents:
            texte = reprendre(r'<span class="ux79-court-next">[^<]*</span>', texte)
        if 'court' in presents:
            texte = reprendre(r'<button\b[^>]*\bid="openCourt"[^>]*>[^<]*</button>', texte)
        if presents:
            # V7 : le panneau de récit suit l'état réel des fichiers (formulations du générateur, cf. narration AV-03).
            avis = re.compile(r'<p class="r13a-media-reserve" role="status">[^<]*</p>')
            mention = ('' if len(presents) == 2 else '<p class="r13a-media-reserve" role="status">'
                       + ('Long en attente de son fichier vidéo. Le Court reste accessible.' if 'court' in presents
                          else 'Court en attente de son fichier vidéo. Le Long reste accessible.') + '</p>')
            texte, nombre = avis.subn(lambda _: mention, texte, count=1)
            if nombre != 1:
                raise ValueError('Mention de réserve absente de la tête validée : ' + nom)
        if 'long' in presents:
            texte, nombre = re.subn(r'(<button type="button" data-av03-long>)Explorer la fiche du Long ↗(</button>)',
                                    lambda m: m[1] + 'Découvrir le Long librement ↗' + m[2], texte, count=1)
            if nombre != 1:
                raise ValueError('Commande du Long absente de la tête validée : ' + nom)
        for format_video in presents:
            texte = reprendre(r'<video\b[^>]*\bid="' + format_video + r'Video"[^>]*>', texte)
            absent = f'data-av03-{format_video}-fichier="absent"'
            if absent in texte:
                texte = texte.replace(absent, f'data-av03-{format_video}-fichier="present"', 1)
    fiches = {'oeuvres/' + uid + '.html': (uid, route) for route, uid in demos.items()}
    if nom in fiches:
        uid, route = fiches[nom]
        for format_video in ('court', 'long'):
            if not media_disponible(site, contenus.get(uid + '.' + format_video)):
                continue
            label = format_video.title()
            lien = (f'<a class="recomp-action" href="../{route}?view={format_video}#{format_video}Video">'
                    f'Voir le {label} <span aria-hidden="true">↗</span></a>')
            motif = re.escape(f'<p class="ith15-etat" role="note">{label} indisponible.</p>')
            if format_video == 'court':
                motif += r'<a class="recomp-action" href="\.\./demos/[^"]+">.*?</a>'
            texte, nombre = re.subn(motif, lambda _: lien, texte, count=1)
            if nombre != 1:
                raise ValueError('État média absent de la tête validée : ' + nom + ' / ' + format_video)
        texte = tete_fiche_disponible(texte, nom, site, contenus, uid)
    for identifiant, contenu in programmes.get(nom, []):
        if not media_disponible(site, contenus.get(contenu)):
            continue
        texte = reprendre(r'<video\b[^>]*\bid="' + identifiant + r'"[^>]*>', texte)
        avis = re.compile(r'<p\b[^>]*data-video-status-for="' + re.escape(contenu) + r'"[^>]*>.*?</p>', re.S)
        nouveaux = avis.findall(genere)
        if len(nouveaux) != len(avis.findall(texte)):
            raise ValueError('Mentions de disponibilité divergentes : ' + nom + ' / ' + contenu)
        suite = iter(nouveaux)
        texte = avis.sub(lambda _: next(suite), texte)
    return texte


def tete_fiche_disponible(texte, nom, site, contenus, uid):
    """P0 N-01 (21/11/2026) : la tête de fiche annonçait « Vidéo indisponible » alors que le Court et le Long
    étaient présents. La mention d'état est retirée uniquement dans ce cas ; aucun autre texte n'est modifié."""
    if not (media_disponible(site, contenus.get(uid + '.court')) and media_disponible(site, contenus.get(uid + '.long'))):
        return texte
    texte, nombre = re.subn(r'<p class="recomp-dispo">Vidéo indisponible</p>', '', texte, count=1)
    if nombre != 1 and '<p class="recomp-dispo">' in texte:
        raise ValueError('Mention de disponibilité inattendue sur la fiche : ' + nom)
    return texte


def proteger_navigation_critique(sorties):
    """Masquer la navigation partielle jusqu'à la lecture de son dernier lien."""
    regle = '.ithc-nav:not(:has(>a[data-a2=mon])){visibility:hidden}'
    ouverture = '<style data-w360="critique">'
    for nom, html in sorties.items():
        if not nom.endswith('.html') or 'pagefind' in nom.split('/') or regle in html:
            continue
        navigation = html.find('class="ithc-nav')
        debut = html.find(ouverture)
        if navigation < 0 or 'data-a2="mon"' not in html or debut < 0:
            continue
        fin = html.index('</style>', debut)
        if fin < navigation:
            sorties[nom] = html[:fin] + regle + html[fin:]


def raccorder_commandes_lecture(sorties):
    """Versionner les commandes utilisées par les quatre pages de lecture de la tête."""
    carnet = 'assets/js/ithakya-v9962-carnet.js'
    lecteur = 'assets/js/ithakya-w360-media-availability.js'
    css = 'assets/css/ithakya-w360-media-availability.css'
    versions = {f: hashlib.sha256(sorties[f].encode('utf8')).hexdigest()[:12]
                for f in (carnet, lecteur, css)}
    for page in ('01-signature', '02-pop-culture', '03-progression', '05-soleil-xl'):
        nom = 'demos/' + page + '.html'
        if nom not in sorties:
            continue
        texte = re.sub(r'(ithakya-v9962-carnet\.js\?sha=)[0-9a-f]+',
                       lambda m: m[1] + versions[carnet], sorties[nom])
        texte = texte.replace(f'href="../{css}"', f'href="../{css}?sha={versions[css]}"', 1)
        sorties[nom] = texte.replace(f'src="../{lecteur}"', f'src="../{lecteur}?sha={versions[lecteur]}"', 1)


def versionner_scripts(sorties, site):
    """P0 cache (21/11/2026) : chaque <script src> local reçoit ?sha=<12 premiers hex du SHA-256 de son contenu généré
    (ou publié s'il n'est pas régénéré) lorsqu'il est sans version ou que sa version ne correspond plus au contenu
    (162 références périmées constatées sur C2, dont ithakya-memoire.js). Reproductible ; aucun contenu ni logique modifiés.
    Les noms déjà empreintés (…-<12 hex>.js) et les URL externes sont laissés tels quels."""
    motif = re.compile(r'(<script\b[^>]*?\bsrc=")([^"?#:]+\.js)(?:\?sha=[0-9a-z]+)?(")')
    cache = {}
    def empreinte(rel):
        if rel not in cache:
            if rel in sorties:
                cache[rel] = hashlib.sha256(sorties[rel].encode('utf8')).hexdigest()[:12]
            else:
                chemin = os.path.join(site, rel)
                cache[rel] = hashlib.sha256(open(chemin, 'rb').read()).hexdigest()[:12] if os.path.isfile(chemin) else None
        return cache[rel]
    for page in [p for p in sorties if p.endswith('.html')]:
        base = os.path.dirname(page)
        def rempl(m):
            url = m.group(2)
            if url.startswith('/') or re.search(r'-[0-9a-f]{12}\.js$', url):
                return m.group(0)
            rel = os.path.normpath(os.path.join(base, url)).replace(os.sep, '/')
            h = empreinte(rel) if not rel.startswith('..') else None
            return m.group(1) + url + '?sha=' + h + m.group(3) if h else m.group(0)
        sorties[page] = motif.sub(rempl, sorties[page])


def main():
    src, site = sys.argv[1], sys.argv[2]
    verifier = '--verifier' in sys.argv
    sorties = generer(src, site)
    # Le catalogue est écrit avant le calcul des empreintes (il est lui-même référencé avec ?sha=).
    if not verifier:
        for p, t in sorties.items():
            if p.startswith('assets/'):
                os.makedirs(os.path.dirname(os.path.join(site, p)), exist_ok=True)
                cible = os.path.join(site, p)
                if not os.path.exists(cible) or open(cible, encoding='utf8').read() != t:
                    open(cible, 'w', encoding='utf8').write(t)
        # Finalisation R2 : conserver les scripts et styles historiques, même inactifs.
        # La génération ne réalise aucune suppression implicite ; un retrait exige une décision distincte.
    pages = {p: t for p, t in sorties.items() if p.endswith('.html')}
    pages = oeuvres_dans_pages(pages, src)   # L20 : durées et cinq idées depuis le catalogue
    with open(os.path.join(src, 'catalogue', 'catalogue.json'), encoding='utf8') as fichier:
        catalogue_medias = json.load(fichier)
    pages = neutraliser_medias_absents(pages, catalogue_medias, site)
    pages = neutraliser_pilotes_absents(pages, catalogue_medias, site)
    pages = {p: position_en_tete(p, t) for p, t in pages.items()}
    rendus = rendus_declares(src)   # L21
    pages = {p: rendus_en_tete(t, rendus) for p, t in pages.items()}
    pages = {p: t.replace('</head>', '<link rel="stylesheet" href="' + '../' * p.count('/') +
                           'assets/css/ithakya-p1-elevation.css?sha=0">\n</head>', 1) for p, t in pages.items()}
    pages = empreintes(site, pages)
    pages = {p: lisibilite_en_tete(styles_en_tete(t)) for p, t in pages.items()}
    pages, lots = css_en_lots(pages, site, sorties)   # L20 : feuilles regroupées par séquence (performance)
    pages = surcouche_m08(pages, src)   # M09 : apports M01–M08 désormais sourcés (parité source/site)
    pages = surcouche_m14(pages, src)   # M14 : apports M12–M14 désormais sourcés (parité source/site)
    pages = entree_active(pages, src)   # A2 : entrée de navigation active d'après la carte des entrées
    pages = harmonie_p2(pages, sorties['assets/css/ithakya-p2-harmonie.css'], sorties['assets/js/ithakya-avatars-p2.js'])
    pages = continuite_p3(pages, src, sorties['assets/css/ithakya-p3-convergence.css'])
    feuille_p4 = 'assets/css/ithakya-p4-cibles.css'
    version_p4 = hashlib.sha256(sorties[feuille_p4].encode('utf8')).hexdigest()[:12]
    pages = {page: contenu.replace('</head>', (
        f'<link rel="stylesheet" href="{"../" * page.count("/")}{feuille_p4}?sha={version_p4}">\n</head>'
    ), 1) for page, contenu in pages.items()}
    sorties.update(pages); sorties.update(lots)
    # UX360: overlay source-backed, preserving the former generator and templates.
    ux_overlay = os.path.join(src, 'ux360_overlay')
    if os.path.isdir(ux_overlay):
        contenus = {c['id']: c for c in catalogue_medias['contenus']}
        for ux_root, ux_dirs, ux_files in os.walk(ux_overlay):
            for ux_name in ux_files:
                ux_file = os.path.join(ux_root, ux_name)
                ux_key = os.path.relpath(ux_file, ux_overlay).replace(os.sep, '/')
                ux_texte = lire(ux_file)
                if ux_key in pages:
                    ux_texte = medias_dans_surcouche(ux_key, ux_texte, pages[ux_key], contenus, site)
                    ux_texte = rendus_en_tete(ux_texte, rendus)
                sorties[ux_key] = ux_texte

    # Premium J/K : les anciens lots CSS restent des ressources héritées.
    # Les pages utilisent les nouvelles empreintes ; aucune purge historique implicite.
    sorties = etape_w360_quatre(sorties, src)   # W360 v2.2 : suppression de l'univers « Culture & Création » (quatre univers), désactivable
    sorties = etape_w360_lcp(sorties, src)   # W360 : priorité de l'image LCP (attributs de chargement seulement)
    sorties = etape_w360(sorties, src)   # W360 : feuilles hors chemin critique (données mesurées ; sans effet si critique.json est absent)
    sorties = etape_w360_premium(sorties, src)   # W360 : continuité de navigation (transitions entre pages)
    # Convergence du 9 novembre : une couche sourcee, independante et reversible.
    # Aucun changement d'authentification, de donnees ou de regles de progression.
    import importlib.util as _convergence_import
    _convergence_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'w360_convergence.py')
    _convergence_spec = _convergence_import.spec_from_file_location('w360_convergence', _convergence_path)
    _convergence_module = _convergence_import.module_from_spec(_convergence_spec)
    _convergence_spec.loader.exec_module(_convergence_module)
    sorties = _convergence_module.appliquer(sorties, src)
    _integration_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "w360_integration.py")
    _integration_spec = _convergence_import.spec_from_file_location("w360_integration", _integration_path)
    _integration_module = _convergence_import.module_from_spec(_integration_spec)
    _integration_spec.loader.exec_module(_integration_module)
    sorties = _integration_module.appliquer(sorties, src)

    # Tête Work sauvegardée : préserver les raccordements postérieurs à J06.
    # Les anciennes surcouches restent intactes ; la tête est appliquée avant l'index.
    tete_work = os.path.join(src, 'w360_tete_validee')
    if os.path.isdir(tete_work):
        for tete_root, tete_dirs, tete_files in os.walk(tete_work):
            for tete_name in sorted(tete_files):
                if not tete_name.endswith(('.html', '.js', '.css', '.json')):
                    continue
                tete_file = os.path.join(tete_root, tete_name)
                tete_key = os.path.relpath(tete_file, tete_work).replace(os.sep, '/')
                tete_texte = lire(tete_file)
                if tete_name.endswith('.html') and tete_key in sorties:
                    # V6 / D1 : la tête reste figée, sauf les fragments qui dépendent d'un média présent.
                    tete_texte = medias_dans_tete(tete_key, tete_texte, sorties[tete_key],
                                                  {c['id']: c for c in catalogue_medias['contenus']}, site)
                sorties[tete_key] = tete_texte

    # V6 : pilotage éditorial (visuel d'accueil, œuvres externes). Sans publication validée : aucun effet.
    import w360_editorial as _editorial
    sorties = _editorial.appliquer(sorties, src, site)
    raccorder_commandes_lecture(sorties)

    # Index éditorial local : liste explicite, sans moteur ni dépendance externe.
    from recherche_statique import appliquer as _index_editorial
    sorties = _index_editorial(sorties, src)
    # La tête validée remplace certains blocs critiques produits par etape_w360.
    proteger_navigation_critique(sorties)
    versionner_scripts(sorties, site)   # P0 : versionnement reproductible des scripts locaux (cache navigateur)
    ecarts = 0
    for p, t in sorted(sorties.items()):
        cible = os.path.join(site, p)
        actuel = lire(cible) if os.path.exists(cible) else None
        if verifier:
            if actuel != t:
                ecarts += 1
                print('ÉCART', p, 'absent' if actuel is None else f'{len(actuel)} → {len(t)} car.')
            continue
        if actuel != t:
            os.makedirs(os.path.dirname(cible) or '.', exist_ok=True)
            open(cible, 'w', encoding='utf8').write(t)
            print('écrit', p, len(t))
    if verifier:
        print(f'{len(sorties)} fichiers générés comparés, {ecarts} écart(s)')
        sys.exit(1 if ecarts else 0)


if __name__ == '__main__':
    main()
