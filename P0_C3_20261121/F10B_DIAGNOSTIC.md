# F10-B — diagnostic (porte 1, 21/11/2026)

**Statut : diagnostic établi ; correctif NON réalisé.**

C3 n'est pas modifiée. Aucune branche de correctif n'est ouverte.

**Sources :** lecture du code serveur C2/C3, qui est identique entre les deux (`site/api/ithakya-pilote.php`, `ithakya-lecture-preuve.php`, `ithakya-credit-review.php`), et tests T1 à T14 (`preuves/f10b_sqlite.json`, `preuves/f10b_mariadb.json`).

## 1. Fait démontré (T9)

Un client HTTP sans affichage obtient le crédit du Court (+5 XP, 0 Point), sur SQLite comme sur MariaDB 10.11.14. Pour cela, il :

1. télécharge le média par `lecture_media` ;
2. calcule lui-même les vignettes 8×6 en niveaux de gris avec FFmpeg ;
3. envoie des témoins `lecture_suivi` au rythme réel (1 par seconde pendant 21 s) ;
4. déclare `court_finished`.

Ce fait démontre qu'une lecture peut être automatisée et créditée. Il ne démontre ni une attention humaine ni une faille générale : les 13 autres cas sont refusés.

## 2. Cause racine : ce que le serveur vérifie, et ce que déclare le navigateur

| Condition de crédit (`progress`, `court_finished` / `long_finished`) | Origine | Contournable par un automate |
|---|---|---|
| Plancher temporel depuis `*_started` : 15 s pour un Court, ≥ 0,9 × durée pour un Long (`assertPlaybackFinish`) | Horloge serveur | Non. Il faut attendre le temps réel |
| Couverture déclarée ≥ 0,98 | **Navigateur** (déclaratif) | Oui |
| ≥ 98 % des octets du fichier servis à ce compte, pour cette version, depuis ≥ plancher (`itpProofComplete`, plages HTTP) | Serveur | Non, mais un simple téléchargement suffit |
| Progression ≥ 90 % de la durée, en avance par témoin ≤ temps mural + 450 ms, avec une image conforme à la référence privée (`itpProofClock`, `itpProofImage`) | Serveur, à partir de valeurs envoyées par le navigateur | **Oui.** L'image se calcule à partir du fichier servi ; le rythme réel suffit |
| Billet de témoin à usage unique, lié à la session (`view` / `ticket`) | Serveur | Non (T7, T8) |
| Revalidation de la session sous verrou (`auth_version`, `FOR UPDATE` sous MariaDB) | Serveur | Non (T12) |

**Cause racine :** le seul témoin « humain » est une vignette du média. Or toute personne qui reçoit le média peut la recalculer. Le dispositif prouve la livraison du fichier et un écoulement du temps réel. Il ne prouve pas un affichage, ni une présence.

## 3. Éligibilité, plafonds et effets (lecture du code)

**Unicité et idempotence**
- Une seule ligne par compte et par œuvre (clé primaire `itp_work_progress(user_id, work_id)`) ; une étape créditée ne l'est qu'une fois.
- Les scores sont recalculés à partir des faits enregistrés (`progression()`).
- Prouvé par T10 et par MDB-1 : 30 appels simultanés sur un même compte ne créditent qu'une fois.

**Plafond par compte**
- Le gain est borné par le catalogue : Court 5 XP, Long 25 XP + 50 XP au premier Long de chaque univers, quiz 5 ou 10 XP, première contribution 10 XP par univers.
- Pour une œuvre complète, cela donne 85 XP / 42 Points, le montant historique de V03.6.
- Le gain se répète d'une œuvre à l'autre, sans jamais dépasser le barème du catalogue.

**Multi-comptes**
- La création publique de comptes n'est limitée que par adresse IP (`register_public` : 30 par 60 s).
- Un ensemble de comptes automatisés peut donc multiplier ce gain borné. Ce n'est pas testé à grande échelle.

**Grades**
- Ils découlent des XP. Le gain par compte reste petit (Exploratrice à 600 XP).

**Économie et Lounge**
- `economic_eligible = false` et `qualification = usage_telemetry_only` sur chaque crédit.
- Économie en mode A, suspendue ; récompenses réelles fermées.
- Le Lounge tient un registre de droits distinct : aucune conversion automatique des XP ou des Points en droit économique (V036).
- Impact actuel : réputation et grades seulement, aucune valeur économique.

**Contrôlabilité, déjà présente**
- Chaque crédit porte un `credit_review` (statut, risques, historique).
- Le statut passe en `pending` en cas de sessions techniques chevauchantes.
- L'administration peut annuler un crédit confirmé (`lecture_decide`, transition `confirmed → cancelled`).
- Chaque décision est journalisée (`ITHAKYA credit: … outcome= reason=`), sans identité.

## 4. Défenses proportionnées, proposées et non implémentées

Aucun CAPTCHA systématique, aucune webcam, aucune prétendue preuve d'attention.

| ID | Mesure | Effet | Risque | Test requis |
|---|---|---|---|---|
| F10B-1 | Plafond de débit : au-delà de N crédits de lecture confirmés par compte et par heure (réglage privé, désactivé par défaut), le crédit suivant passe en `pending` avec le risque `credit_rate` | Limite le gain automatisé ; reste contrôlable par la revue existante | Faux positifs chez les grands lecteurs : le seuil est à calibrer sur le pilote | Lecture légitime confirmée ; (N+1)ᵉ lecture en `pending` ; rejeu de T1 à T14 ; MariaDB |
| F10B-2 | Signal de création de masse : comptes récents d'une même adresse IP, au-delà d'un seuil, crédités en `pending` | Limite le multi-comptes | Adresses IP partagées (NAT, établissements) ; donnée personnelle → minimisation et durée de conservation | Idem, plus un test à deux adresses IP |
| F10B-3 | Rapport de réconciliation administrateur : crédits par compte et par fenêtre, et annulation groupée contrôlée par `lecture_decide` | Annulation contrôlée des crédits indus | Aucun changement de règle | Annulation puis recalcul des scores |

**Recommandation :**
- maintenir la réserve F10-B ;
- maintenir l'économie fermée ;
- traiter F10B-1 et F10B-3 dans une branche dédiée issue de C3, avec les tests listés, avant toute fusion ;
- ne fusionner qu'après preuves avant/après sur MariaDB.

Ces mesures n'ont **pas** été exécutées dans cette session, faute de budget. Elles restent **NON EXÉCUTÉES**.
