# ITHAKYA PREMIUM W360 — Pack audiovisuel 7 œuvres — 2026-11-28

Statut : **0 master sur 7 récupéré**. Préparation éditoriale complète ; préparation audiovisuelle outillée et testée, en attente des fichiers.

## Contenu

| Dossier | Contenu | État |
|---|---|---|
| `01_masters/` | Masters sources, conservés séparément | Vide : voir `06_manifeste/RAPPORT_MANQUANTS.md` |
| `02_declinaisons/` | HLS adaptatif (fMP4, H.264, échelle par largeur, images-clés à 2 s) et MP4 de repli | Produit par `07_outils/preparer.sh` |
| `03_affiches_miniatures/` | Affiche (10 % de la durée), affiche dynamique 6 s muette, miniatures à 25/50/75 % | Produit par `07_outils/preparer.sh` |
| `04_sous_titres/` | WebVTT publiés par les sources : Why I Fly FR et EN-US (manuels, auteur) ; One Revolution per Minute EN (auto-généré Vimeo) | 3 pistes |
| `05_editorial/` | 7 fiches (synopsis, crédits, profil du créateur, repères, passerelle, quiz, métadonnées), 7 quiz JSON, `socle_univers.json` au format des univers du socle | Complet |
| `06_manifeste/` | `manifeste.json` (médias, ATTENZIA, Note K, Grande Traversée), `qualification.csv`, `RAPPORT_MANQUANTS.md`, `SHA256SUMS` | Complet ; mesures ffprobe à venir |
| `07_outils/` | `oeuvres.json` (source unique), `preparer.sh`, `hls_master.py`, `manifeste.py` | Testé |

## Règles appliquées

- Aucune œuvre substituée, aucun remontage ni raccourcissement : chaque déclinaison couvre la durée intégrale du master (vérifié sur un master de test : 288 images en entrée, 288 en sortie sur le MP4 et chaque variante HLS).
- Proportions et cadence natives conservées ; audio sans normalisation (dynamique d'origine).
- Aucun doublage produit. Les sous-titres sont désactivés par défaut dans le HLS (VO conservée).
- Toute valeur non mesurée est marquée « source » (déclarée par la plateforme) ; aucune valeur inventée.
- Socle global-ithakya consulté en lecture seule ; aucun fichier du socle modifié.

## Points ouverts

1. Masters à fournir (7). One Revolution per Minute : téléchargement activé par le propriétaire sur Vimeo, mais vimeo.com est refusé par la politique réseau de l'environnement d'exécution.
2. La Grande Traversée : les cinq personnages ne figurent ni dans la commande ni dans le socle ; champs laissés vides.
3. Pistes FR auto-générées (Balade Mentale, Intro Pandemonium) disponibles à la source, non reprises : transcription non relue.
4. Why I Fly : voix off EN, DE, IT, ES créditées ; seule la version FR en ligne est identifiée.
5. Weightless : musique « My Silver Lining » (First Aid Kit) créditée.

## Utilisation

    sh 07_outils/preparer.sh            # qualifie et décline tous les masters déposés, puis régénère le manifeste
    python3 07_outils/manifeste.py      # régénère seulement manifeste, tableau, rapport et fiches

Prérequis : ffmpeg/ffprobe (7+ recommandé), python3, sha256sum.
