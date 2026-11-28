# Récupération manuelle des 7 masters — procédure par œuvre

État au 2026-11-28 : **1 fichier récupéré sur 7** (W360-ST-COURT, copie de diffusion Vimeo 2160p — voir `02_qualification/QUALIFICATION_W360-ST-COURT.md`) (journal : `02_qualification/journal_recherche_20261128.json`).
Une fois un fichier obtenu : le déposer dans `01_masters/<ID>.<ext>` sans le modifier, puis lancer `sh 07_outils/preparer.sh <ID>` (contrôle ffprobe, durée à l'image près, résolution, codecs, débit, pistes audio, SHA-256, déclinaisons).

| ID | Œuvre | Fichier recherché | Voie de récupération |
|---|---|---|---|
| W360-ST-COURT | One Revolution per Minute — Erik Wernquist | Fichier déposé sur Vimeo : 3840x1620, 6 min 21 s | **Téléchargement officiel ouvert.** Sur https://vimeo.com/869858712, connecté à un compte Vimeo, bouton « Télécharger » sous le lecteur ; choisir la meilleure qualité proposée (« Original » si listé, sinon 4K). Depuis cet environnement : autoriser `vimeo.com` et `player.vimeo.com` ; l'exigence d'une session Vimeo connectée n'est pas vérifiée. |
| W360-GT-FILM | Priorities — Gints Zilbalodis | Fichier déposé sur Vimeo : 2048x856, 9 min 25 s | **Diffusion par intégration Vimeo validée** (code de l’auteur, `03_integration/`). Master facultatif : demande via https://vimeo.com/gints. |
| W360-ST-LONG | D’étranges signaux radios… — Balade Mentale | Master 21 min 50 s, VF | Aucun téléchargement YouTube. Demande à la chaîne Balade Mentale (contact professionnel de l'onglet « À propos » de la chaîne, non relevé ici ; Instagram @baladementale). |
| W360-SA-COURT | WHY I FLY — Jean-Baptiste Chandelier | Master 3 min 28 s, VF ; versions voix off EN, DE, IT, ES créditées | Demande à l'auteur (Instagram / Facebook @jbchandelier). Demander aussi les quatre versions linguistiques. |
| W360-SA-LONG | Weightless — Jean-Baptiste Chandelier | Master 5 min 49 s | Même contact que ci-dessus. Musique créditée : « My Silver Lining » (First Aid Kit). |
| W360-PC-COURT | VALD — PROZACZOPIXAN (clip officiel) | Master 4 min 03 s | Demande à Echelon Records ou à Bien Vu (Instagram @bienvuprods). |
| W360-PC-LONG | Intro Pandemonium Paris La Défense Arena : Hollywood en sueur ! | Master 8 min 49 s | Demande à Echelon Records (production) ou à BienVu productions (réalisation). |

Distinguer master et copie de diffusion : un fichier fourni par l'auteur ou la production (ProRes, DNxHR, H.264 haut débit d'export) est un master ; un fichier issu d'une plateforme (téléchargement Vimeo autre que « Original », export YouTube Studio) est une copie de diffusion et doit être déclaré comme tel dans `07_outils/oeuvres.json` (`statut_master`).

Les fiches éditoriales, quiz, WebVTT et le manifeste restent dans le paquet `ITHAKYA_PREMIUM_W360_PACK_AUDIOVISUEL_7_OEUVRES_20261128.zip` (non refaits).
