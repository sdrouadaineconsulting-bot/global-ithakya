# F10B-1 — correctif isolé : plafond de débit des crédits de lecture

Correctif livré **séparément** de C3 : C3 reste intacte (SHA-256 `c573b5e8…39d3`). Il est conservé dans ce dossier, sur la branche `claude/new-session-q55sxl`, la seule autorisée ; aucune autre branche Git n'a été créée.

## Effet

Au-delà de N crédits de lecture (Court, Long) **confirmés** pour un compte sur une heure glissante, la lecture suivante est enregistrée normalement, mais son crédit passe **en revue** (`pending`, risque `credit_rate`). L'administration le confirme ou le rejette par la revue existante (`lecture_reviews`, `lecture_decide`).

- **Réglage** : clé privée `credit_rate_max_hour` dans `config.php`. Défaut : 12 ; 0 désactive le plafond.
- **Inchangés** : barème, faits, quiz, idempotence, textes et interface.
- **Concurrence** : le décompte est fait sous le verrou de compte existant (`itpProofSameAccount`, `FOR UPDATE` sous MariaDB).

## Delta : 4 fichiers serveur

`site/api/ithakya-credit-review.php`, `site/api/ithakya-pilote.php` et leurs sources `source/serveur/…`.

La correction tient en deux changements :
- un paramètre facultatif `$config` est ajouté à `itpCreditRisk` ;
- le décompte est fait sur l'heure glissante.

Empreintes : `delta/DELTA_C2_C3.json`. Le nom du fichier est imposé par le script réutilisé : ici « avant » = C3 et « après » = C3+F10B. Manifeste de la variante : `MANIFESTE_C3_F10B_SHA256.txt` (4 118 fichiers).

**Application et retour** (le script reprend les libellés de C2/C3) :
- `python3 -I delta/RETOUR_ARRIERE_F10B.py <dossier_C3> vers-c3` applique F10B-1 ;
- `python3 -I delta/RETOUR_ARRIERE_F10B.py <dossier> vers-c2` revient à C3.

Le message affiché (« état C2 / C3 ») est générique.

## Preuves (MariaDB 10.11.14, PHP 8.3.6 en serveur intégré à 8 processus, mires)

| Test | Résultat | Fichier |
|---|---|---|
| Plafond à 1 par heure : 1re lecture confirmée, 2e enregistrée en `pending` (`credit_rate`) ; l'administration confirme (XP 5 → 10) puis annule l'autre crédit (XP 10 → 5) ; un membre ordinaire est refusé en 403 | CONFORME | `preuves/SEUIL_1_REVUE_ADMIN.json` |
| Défaut à 12 : rejeu des cas T1 à T14 | Identique à l'état sans correctif : 12 conformes ; T9 = limite structurelle (sous le seuil) ; T12 = artefact de libellé, contre-test conforme (401) | `preuves/F10B_T1_T14_APRES_PATCH_MARIADB.json`, `preuves/T12B_SESSION_REVOQUEE_APRES_PATCH.txt` |
| Concurrence : 10 comptes en parallèle, puis 30 appels simultanés sur un même compte | 10 crédits exacts, aucun double crédit, 0 deadlock, 0 erreur fatale | `preuves/CONCURRENCE_10_COMPTES_APRES_PATCH.json` |
| Parcours légitime complet par l'interface (Court → Long → V1 en fin de Long) | 85 XP / 42 Points, identique à C2 et C3 | `preuves/PARCOURS_LEGITIME_APRES_PATCH_390.json` |
| Retour arrière C3 → C3+F10B → C3 | 4 118/4 118 empreintes conformes dans les deux sens | `preuves/RETOUR_ARRIERE_F10B_TEST.txt` |

## Risques résiduels

- **Lecture automatisée** : elle reste possible sous le seuil. F10-B est **limité et contrôlable, pas levé**. Un automate obtient au plus N crédits confirmés par heure et par compte ; au-delà, chaque crédit passe en revue humaine.
- **Création de comptes en masse** : non traitée (proposition F10B-2, non implémentée). Seule la limite par adresse IP existante s'applique (30 comptes par minute).
- **Faux positifs** : un lecteur très assidu (plus de 12 Courts et Longs confirmés en une heure) voit ses crédits suivants mis en attente, sans perte, jusqu'à une décision. Le seuil est à calibrer pendant le pilote. Aucune donnée personnelle supplémentaire n'est collectée.
- **Réconciliation (F10B-3)** : la revue existante permet l'annulation unitaire, prouvée ici. Il n'existe pas d'annulation groupée.
- **Environnements non testés** : MariaDB 11.8 et OVH.

## Recommandation

**Fusion dans la candidate suivante après validation par le propriétaire du seuil par défaut (12 par heure).** Les tests ci-dessus sont favorables. Le seuil est un paramètre métier, que je ne tranche pas.

L'économie réelle reste fermée, et la réserve F10-B est maintenue sous la forme « risque limité et contrôlable ».
