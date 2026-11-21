# Journal des échecs de commande — session P0 du 21/11/2026

Chaque échec survenu pendant la session est consigné ici. Pour chacun : la cause, son effet sur les résultats et son statut.

| # | Commande | Symptôme | Cause | Effet sur les résultats | Statut |
|---|---|---|---|---|---|
| E1 | `xxd` (inspection de l'en-tête des fichiers reçus) | `command not found` | Outil absent de l'environnement | Aucun ; inspection refaite en Python | Résolu |
| E2 | `unzip -l …CAPTURES….part01` | `End-of-central-directory signature not found` | Volume 1 d'une archive découpée en tranches d'octets ; le répertoire central est dans le dernier volume | Les archives ne sont lisibles qu'une fois complètes. C2 : les 4 volumes reçus, réassemblage conforme (SHA-256 `279660f0…9411`). Captures : seul part01 a été reçu | Résolu pour C2. **Ouvert pour les captures** (part02 et suivants non reçus) |
| E3 | Extraction de part01 par script (`x.py`) | `ValueError: not enough values to unpack` | Le script supposait des noms de fichier de forme `vue__page` ; l'archive C2 a une arborescence | Aucun ; script corrigé (`x2.py`, chemins conservés, contrôle CRC) | Résolu |
| E4 | `python3 -I generer.py … --verifier` | `ModuleNotFoundError: programmer_ithakya` | Le mode `-I` retire le dossier du script du chemin d'import, alors que le générateur importe ses modules voisins | Aucun ; relancé sans `-I`, sur une copie jetable : 315 fichiers comparés, 0 écart | Résolu |
| E5 | Démarrage de `mariadbd` | `The socket file path is too long (> 107)` puis `Can't create UNIX socket` | Chemin du socket dans le dossier de travail au-delà de la limite Unix de 107 caractères | Aucun ; socket déplacé vers `/tmp/claude-0/mdb/m.sock` | Résolu |
| E6 | `SELECT @@transaction_isolation` | `ERROR 1193 Unknown system variable` | MariaDB 10.11 expose `@@tx_isolation` (l'alias MySQL 8 n'existe pas) | Aucun ; relevé fait avec `@@tx_isolation` = `REPEATABLE-READ` | Résolu. **Point de compatibilité à vérifier** : aucun code PHP de C2/C3 n'utilise cette variable (recherche négative) |
| E7 | Balayage de stabilité C2 (`stabilite.cjs`, 148 cas) | Délai de 600 s dépassé au premier plan, passage en arrière-plan | Durée réelle de 22 min 17 s | Aucun ; achevé avec le code 0 et les 148 résultats écrits | Résolu |
| E8 | Première mesure V1 (`v1.cjs`) | Mesure non valable : lecture à 5 s au lieu du repère de 39 s | L'avance par `currentTime` était annulée par la protection anti-avance du lecteur | Mesure écartée ; refaite en lecture continue à vitesse normale | Résolu |
| E9 | Lecture de `empreintes()` par `sed` | `syntax error in expression (error token is "1185")` | Deux fonctions commençant par `def empreintes`, d'où deux numéros de ligne | Aucun ; lecture par numéros explicites | Résolu |
| E10 | Contrôle d'intégrité C2 → C3, première version | 0/37 « identiques hors `?sha=` » | La normalisation laissait un `?sha=` vide | Corrigé : 37/37 pages identiques hors `?sha=`, texte visible identique 37/37 | Résolu |
| E11 | Banc F10-B, cas T12 (session révoquée) | Verdict automatique « ÉCART » (403 au lieu de 401) | Après révocation, le serveur renouvelle la session, et le jeton CSRF échoue avant le contrôle d'authentification | Contre-test T12b : session sans utilisateur, puis écriture refusée en 401. Aucune écriture acceptée | Résolu (conforme) |
| E12 | Premier test V1 sur C3 (`v1c3.cjs`) | 0 XP après réponse | Protocole : le Long était lancé par script, hors interface et sans Court. Le contrôle identique sur C2 donne aussi 0 XP | Remplacé par le parcours réel par l'interface : 85 XP / 42 Points sur C2 et sur C3 | Résolu (artefact de protocole, pas une régression) |

Les échecs E1 à E12 sont résolus. Deux points restent ouverts au titre des pièces ou des vérifications :

- **E2 (captures)** : volumes 2 et suivants de `ITHAKYA_W360_C2_CAPTURES_20261121` non reçus.
- **E6** : la compatibilité MariaDB 11.8 et OVH reste non vérifiée.
