# Différentiel cumulatif S40 → S41 → S42

| Étape | Fichiers modifiés | Ajouts / retraits | Contenu | Empreinte du module |
|---|---|---|---|---|
| S40 → S41 (ChatGPT, hors Work) | `source/serveur/ithakya-attenzia-instantanes.php`, `site/api/ithakya-attenzia-instantanes.php` (identiques) | 0 / 0 (déclaré par `MANIFESTE_S41.json`, **non vérifiable sans S40**) | Règle V3.5 → V3.6 : `itpAtzComplementsPublies`, `itpAtzComplementFragile`, masque intégral de la cellule si un complément dérivé ou sa variation est < seuil | V3.5 reconstituée `d63d5f1e…9b65` (inversion du correctif, **non confrontée à S40**) → V3.6 `33313dc9…6499` |
| S41 → S42 (cette contre-recette) | les deux mêmes chemins (identiques) | 0 / 0 (**vérifié** : 4 135 fichiers, inventaire complet comparé) | Règle V3.6 → V3.7 : dans `$pub`, un taux n'est publié que si ses deux termes sont publiés (4 lignes et l'identifiant de règle) | V3.7 `51a4e6bb…4e85` |

Fichiers :
- `differentiel/S40_S41_attenzia_v3_6.patch` — correctif S41 d'origine (SHA-256 `56817e77…575`)
- `differentiel/S41_S42_attenzia_v3_7.diff` — correctif S42
- `differentiel/S40_S42_cumulatif_source_serveur.diff` — V3.5 reconstituée → V3.7 (source ; la copie `site/api` est identique)
- `modules/ithakya-attenzia-instantanes.v35.php`, `.v36.php`, `.v37.php`

Retour arrière : réinstaller S41 (`01149a30…08c4`), conservée intacte, ou recopier `modules/…v36.php` sur les deux chemins. Aucune migration ; les instantanés figés restent lisibles (RT-11).
