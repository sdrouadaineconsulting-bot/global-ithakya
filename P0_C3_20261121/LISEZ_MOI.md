# ITHAKYA W360 — sauvegarde de la candidate C3 (P0 du 21/11/2026)

Cette sauvegarde a été faite **avant toute nouvelle campagne de tests**. C2 reste intacte. C3 n'est pas homologuée : la campagne de vérification et le verdict sont encore à produire.

## Reconstituer C3 à partir de C2

L'archive complète `ITHAKYA_W360_CANDIDATE_C3_20261121.zip` pèse 100,46 Mo, au-delà de la limite de GitHub par fichier. Elle n'est donc pas versionnée ici ; elle se reconstitue à partir de C2 et du delta :

```
unzip ITHAKYA_W360_CANDIDATE_C2_CONSOLIDEE_20261121.zip -d candidate   # SHA-256 279660f06bff9deb09b64b99d3d89d51d909ed310dba7c72ac0545585b9a9411
python3 -I delta/RETOUR_ARRIERE_C3.py candidate vers-c3
cd candidate && sha256sum -c ../MANIFESTE_C3_SHA256.txt               # 4 118 fichiers attendus
```

- **Retour arrière** : `python3 -I delta/RETOUR_ARRIERE_C3.py candidate vers-c2`. L'aller-retour est prouvé dans `preuves/RETOUR_ARRIERE_C3_TEST.txt`.
- **Empreinte de l'archive C3 produite dans la session** : `SHA256_CANDIDATE_C3.txt`.

## Delta C2 → C3 : 42 fichiers, aucun ajout, aucun retrait

| Lot | Fichiers | Nature |
|---|---|---|
| P0-V1 | `ithakya-v1-interaction.js` (site et source) | La question V1 ne s'ouvre plus à 65 % du Long, en pause sous un voile. Elle s'ouvre à la fin effective du Long, sans obligation de répondre. Énoncé, réponses, libellés, transmission et crédits inchangés. |
| P0-L9 (C-06) | `ithakya-v9962-carnet.js` (site et source) | « Garder cette découverte » est placé après « Explorer une autre œuvre ». Le libellé est inchangé et aucun bouton n'est ajouté. |
| P0-N01 | `generer.py` (`tete_fiche_disponible`) | Avec Court et Long présents, la mention fausse « Vidéo indisponible » n'est plus affichée en tête de fiche. Sans effet sur C2 livrée sans films. |
| P0-CACHE | `generer.py` (`versionner_scripts`) et les 37 pages HTML | Chaque `<script src>` local porte `?sha=` = empreinte du contenu. Corrige 162 références périmées de C2 (dont `ithakya-memoire.js`, porteur de X03) et les scripts sans version (dont `ithakya-v1-interaction.js`). |

## Contrôles déjà faits, avant sauvegarde

- **Générateur** : régénération reproductible (deux générations identiques au fichier près) ; `generer.py --verifier` donne 315 fichiers comparés, 0 écart.
- **Contenus** : texte visible identique sur 37/37 pages ; 37/37 pages identiques une fois les `?sha=` retirés ; aucun média ni aucune donnée modifié (`preuves/INTEGRITE_C2_C3.json`).
- **Versionnement JS** : 0 script local sans version et 0 référence JS périmée (`outils/sha_refs.py`).
- **V1 avec média présent**, parcours réel par l'interface, membre à 390 px :

  | | C2 | C3 |
  |---|---|---|
  | Comportement de la question | pause imposée à 39,3 s, voile sur 100 % du lecteur | s'ouvre à 60 s (fin du Long) |
  | Crédits | 85 XP / 42 Points | 85 XP / 42 Points |
  | Défilement à l'ouverture ou à la fermeture | — | aucun (dy = 0) |

  Preuves : `preuves/v1/`.
- **Antifraude F10-B**, SQLite et MariaDB 10.11.14 (`preuves/f10b_*.json`) : voir le journal et le rapport à venir.

## Restant à faire (campagnes non exécutées au moment de la sauvegarde)

- Balayage de stabilité C3 : 37 pages × 4 vues, CLS et mouvements JavaScript (balayage C2 fait : `preuves/stabilite/`).
- Transition Court → Long sur C3 : 4 pages × 3 vues.
- Contrôle du chargement effectif des scripts versionnés.
- Qualification MariaDB (concurrence, migrations, redémarrage).
- Registre exhaustif et verdict.

## Réserves déjà identifiées

- **CSS** : `ithakya-composition-360.css` garde une version `?sha=` périmée (70 références) et 47 feuilles CSS restent sans version. Hors du périmètre JS demandé.
- **L6 / L10 (Grande Traversée en œuvre unique)** : bloqués. L'œuvre est absente (aucun média, droits non acquis) et le lot réécrit des contenus gelés. L'archive Work F09 n'a pas été transmise.
- **L8 (« Voir le Court » en tête de fiche)** : à confirmer. L'appliquer imposerait de réécrire un libellé ou d'ajouter un CTA.
- **Captures C2** : seul le volume part01 a été reçu.

Journal des échecs de commande : `JOURNAL_ECHECS_COMMANDES.md`.
