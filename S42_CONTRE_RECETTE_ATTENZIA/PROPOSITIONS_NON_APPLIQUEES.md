# Propositions signalées séparément — non appliquées (S42)

| Id | Constat mesuré | Proposition | Périmètre |
|---|---|---|---|
| PR-01 | `session` et `profile` coûtent 7,8 et 9,4 ms à vide, contre 2,4 à 2,8 ms pour `oeuvres` et `progression` ; sous charge, P95 serveur de 621 et 666 ms (`preuves/diag_par_action.json`) | Profiler ces deux actions (construction du profil public, catalogue d'avatars) avant tout plateau de requalification | Hors S42 — sans modification d'interface ni de contenu |
| PR-02 | Les distributions des lectures n'étaient pas enregistrées séparément sur le plateau S42 | Pour le prochain plateau : journaliser `%D` côté Apache et séparer lectures et écritures dès l'exécution | Méthode de recette |
| PR-03 | Le complément dérivé nul est publié (R-ATZ-03) | Masquer l'indicateur concerné, et non la cellule entière, si le propriétaire retient l'homogénéité comme divulgation | ATTENZIA — décision du propriétaire |
