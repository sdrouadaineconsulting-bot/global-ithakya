# Différentiel cumulatif S40 → S41 → S42

| Étape | Fichiers modifiés | Ajouts / retraits | Contenu | Empreinte du module |
|---|---|---|---|---|
| S40 → S41 (ChatGPT, hors Work) | `source/serveur/ithakya-attenzia-instantanes.php`, `site/api/ithakya-attenzia-instantanes.php` (identiques) | 0 / 0 (**vérifié** par comparaison des inventaires S40 et S41) | Règle V3.5 → V3.6 : `itpAtzComplementsPublies`, `itpAtzComplementFragile`, masque intégral de la cellule si un complément dérivé ou sa variation est < seuil | V3.5 `d63d5f1e…9b65` (reconstitution = empreinte de l'inventaire S40) → V3.6 `33313dc9…6499` |
| S41 → S42 (cette contre-recette) | les deux mêmes chemins (identiques) | 0 / 0 (**vérifié** : 4 135 fichiers, inventaire comparé à S40 et à S41) | V3.6 → V3.7 : un taux n'est publié que si ses deux termes sont publiés (A-01). V3.7 → V3.8 : trace de garde des instantanés purgés (R-ATZ-01) | V3.7 `51a4e6bb…4e85` → **V3.8 `e0cd26db…bd87`** |

Fichiers :
- `differentiel/S40_S41_attenzia_v3_6.patch` — correctif S41 d'origine (SHA-256 `56817e77…575`)
- `differentiel/S41_S42_attenzia_v3_7.diff` — correctif A-01
- `differentiel/S42_attenzia_v3_8.diff` — correctif R-ATZ-01 (V3.7 → V3.8)
- `differentiel/S40_S42_cumulatif_source_serveur.diff` — V3.5 (S40) → V3.8 (source ; la copie `site/api` est identique)
- `modules/ithakya-attenzia-instantanes.v35.php`, `.v36.php`, `.v37.php`, `.v38.php`

Retour arrière : réinstaller S41 (`01149a30…08c4`), conservée intacte, ou recopier `modules/…v36.php` sur les deux chemins. Aucune migration ; les instantanés figés restent lisibles (RT-11).
