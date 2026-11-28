# 01_masters — fichiers sources (vides à la livraison)

Déposer ici chaque master, sans le modifier, sous son identifiant :

| Fichier attendu | Œuvre |
|---|---|
| `W360-ST-COURT.<ext>` | One Revolution per Minute — Erik Wernquist (Vimeo 869858712 ; téléchargement activé par le propriétaire ; résolution déclarée 3840x1620) |
| `W360-ST-LONG.<ext>` | D’étranges signaux radios en provenance de l’espace — Balade Mentale (YouTube rznAp00VGSg) |
| `W360-SA-COURT.<ext>` | WHY I FLY — Jean-Baptiste Chandelier (YouTube O7ss--t2hgI) |
| `W360-SA-LONG.<ext>` | Weightless — Jean-Baptiste Chandelier (YouTube Oos4ojutOMM) |
| `W360-PC-COURT.<ext>` | VALD - PROZACZOPIXAN (Clip officiel) — Bien Vu Production (YouTube qjzD3LkrDSQ) |
| `W360-PC-LONG.<ext>` | Intro Pandemonium Paris la Defense Arena : Hollywood en sueur ! — BienVu productions (YouTube am3TxSNeVYI) |
| `W360-GT-FILM.<ext>` | Priorities — Gints Zilbalodis (Vimeo 93124212 ; résolution déclarée 2048x856) |

Puis : `sh 07_outils/preparer.sh` (tous) ou `sh 07_outils/preparer.sh W360-ST-COURT` (un seul).
Un master est un fichier fourni par l'ayant droit ou issu du mécanisme de téléchargement proposé par la source.
Une copie de diffusion (ré-encodage de plateforme) n'est pas un master : la signaler comme telle dans `07_outils/oeuvres.json` (champ `statut_master`).
