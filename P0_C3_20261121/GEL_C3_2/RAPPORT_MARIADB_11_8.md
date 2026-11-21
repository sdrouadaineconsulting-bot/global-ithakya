# Rapport de qualification MariaDB 11.8 — candidate C3.2 (21/11/2026)

**Verdict de compatibilité : VALIDÉ sur MariaDB 11.8.10, en environnement local isolé.**

Ce verdict ne vaut pas qualification de l'hébergement OVH : version réelle de MariaDB, version de PHP, droits SQL, limites mutualisées et HTTPS n'y ont pas été testés.

## 1. Version et environnement

| Élément | Valeur constatée | Preuve |
|---|---|---|
| Serveur | **MariaDB 11.8.10** (`Ver 11.8.10-MariaDB for linux-systemd on x86_64`) | `mariadb_11_8/VERSION_SERVEUR.txt` |
| Origine | Archive binaire officielle `mariadb-11.8.10-linux-systemd-x86_64.tar.gz` (archive.mariadb.org). SHA-256 **`15ca40274597af84fa8f89f8248b37740c5a712c003df80b4c7b32a4486e2027`**, conforme au `sha256sums.txt` publié | `EMPREINTE_ARCHIVE_OFFICIELLE.txt` |
| Paramètres | InnoDB ; `sql_mode` = `STRICT_TRANS_TABLES, ERROR_FOR_DIVISION_BY_ZERO, NO_AUTO_CREATE_USER, NO_ENGINE_SUBSTITUTION` ; isolation `REPEATABLE-READ` ; `utf8mb4` ; collation serveur par défaut `utf8mb4_uca1400_ai_ci` | `PARAMETRES_SERVEUR.txt` |
| Isolement | Instance dédiée : dossier `/tmp/claude-0/m11810`, port 3308, socket privé. Bases de test `ithakya_q118` et `ithakya_q118_migr`, comptes et données **fictifs**. Aucune donnée réelle, aucune production | `qualif_maria118.sh` |
| PHP | PHP 8.3.6 en serveur intégré, 8 processus (`PHP_CLI_SERVER_WORKERS=8`) ; `pdo_mysql` présent ; client `mysqlnd 8.3.6` ; serveur vu par PDO : `11.8.10-MariaDB` | `PILOTE_PHP.txt` |
| Candidate | Copie de **C3.2 reconstituée depuis ses 3 volumes** (SHA-256 `56a153cd…1607`). Mires de banc ajoutées dans la copie seulement. **C3.2 n'est pas modifiée et F10B-1 n'est pas intégré** | `qualif_maria118.sh` |

Voie d'accès :
- Docker est indisponible dans le conteneur, et les paquets Ubuntu 11.8 demandent glibc 2.43 (le système a 2.39). Les exécuter par un chargeur privé a été refusé par la politique de sécurité de la session, et n'a donc pas été fait.
- L'archive officielle a été obtenue après ajout de l'hôte `archive.mariadb.org`, avec votre accord, dans un environnement cloud personnel dédié (« global-ithakya »).
- Un premier téléchargement tronqué (empreinte non conforme) a été détecté puis repris ; seule l'archive à l'empreinte conforme a été utilisée.

## 2. Scénarios exécutés et résultats

| # | Scénario | Résultat | Preuve |
|---|---|---|---|
| S0 | Installation automatique du schéma au premier appel | 13 tables InnoDB, `schema_version` = 6, API 200 | `SCHEMA_AUTO.txt` |
| S1 | Antifraude F10-B, cas T1 à T14 : HTTP 200 sans crédit, fin forgée, plancher sans média, média sans témoins, témoins aux images fausses, témoins accélérés ×4, rejeu, vol de témoin, automate (T9), concurrence, quiz sans lecture, révocation, CSRF, `owner_id` étranger | 12 conformes. **T9 = limite structurelle connue (réserve F10-B)**. T12 = artefact de libellé du banc (403 CSRF), voir S2 | `S1_F10B_T1_T14.json/.log` |
| S2 | Session révoquée (« déconnecter les autres appareils ») | L'ancienne session n'a plus d'utilisateur ; écriture refusée en **401** ; le révocateur écrit (200) | `S2_T12B_SESSION_REVOQUEE.txt` |
| S3 | Concurrence réelle (8 processus) : 10 comptes terminent leur Court simultanément, puis 30 appels simultanés sur un même compte | 10 crédits exacts (5 XP chacun) ; rafale : 200, **aucun double crédit** | `S3_CONCURRENCE.json` |
| S4 | Verrous | **0 deadlock** (`SHOW ENGINE INNODB STATUS`) ; 0 erreur fatale ou 1213/1205 côté PHP | `SORTIE_SCENARIOS.log` |
| S5 | Parcours légitime complet par l'interface (Chromium, 390 px) : Court → Long → V1 en fin de Long | **85 XP / 42 Points** ; V1 ouverte à 60 s, hors lecture | `S5_PARCOURS_LEGITIME_390.json` |
| S6 | Arrêt brutal (`kill -9`) puis redémarrage | Récupération après incident ; décomptes identiques avant et après (18 comptes, 16 progressions, 12 Courts, 31 états) ; `CHECK TABLE` OK sur 5 tables ; API 200 | `S6_*.txt` |
| S7 | Migrations documentées (`GUIDE_INSTALLATION_OVH_V1.md` §3), rejeu, retours | 7 migrations : rc=0, 13 → 32 tables. 4 rejouées : rc=0. 3 retours : rc=0 (32 → 25). 25 tables InnoDB | `S7_MIGRATIONS.txt` |
| S8 | Index et contraintes d'unicité | Clés primaires et uniques identiques à 10.11.14, dont `itp_work_progress(user_id, work_id)`, `itp_states(user_id, state_key)`, `itp_users(login)` et `itp_entries(user_id, request_key)` | `S8_INDEX.txt` |
| S9 | Collation des tables applicatives | Toutes en **`utf8mb4_bin`**, fixée par le schéma : la collation par défaut du serveur (`uca1400`) ne s'applique pas | `S9_COLLATIONS.txt` |

## 3. Comparaison avec MariaDB 10.11.14

Les scénarios S1 à S8 ont été joués sur 10.11.14 plus tôt dans la session (`../preuves/mariadb/`, `../F10B_patch/preuves/`). Les résultats sont **identiques** : mêmes verdicts, mêmes crédits, mêmes index, mêmes migrations.

## 4. Anomalies et limites

- **Aucune anomalie de compatibilité constatée.**
- **Non couvert ici** :
  - php-fpm et HTTPS ;
  - la configuration réelle d'OVH : version de MariaDB proposée, version de PHP, droit `CREATE`, `GET_LOCK`, limites de connexions ;
  - la charge au-delà de 10 comptes simultanés ;
  - les migrations cadeaux L15/L16, non appliquées faute de décision du propriétaire.
- **Avertissement** : le serveur intégré de PHP n'est pas représentatif des performances d'OVH.

## 5. Contrôles à faire sur OVH avant le pilote (non autorisés ici, à exécuter sur votre feu vert)

1. Relever les versions réelles de MariaDB et de PHP, ainsi que les extensions (`pdo_mysql`).
2. Vérifier les droits SQL (`CREATE`, `ALTER`, `GET_LOCK`).
3. Rejouer S0, S7 et S5 sur une base de recette vide.
4. Faire une sauvegarde logique, puis tester la restauration.
