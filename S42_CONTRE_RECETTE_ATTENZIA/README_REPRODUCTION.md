# Dossier probatoire S42 — reproduction

## 1. Intégrité
```
cat ITHAKYA_S41.zip.part0{1..6} > ITHAKYA_S41.zip         # 100 600 542 o, SHA-256 01149a30…08c4
sha256sum ITHAKYA_PREMIUM_W360_S42_ATTENZIA_V37_20261128.zip   # = MANIFESTE_S42.json:sha256_candidate
```
Comparer l'inventaire extrait avec `MANIFESTE_S42.json:inventaire_final` (4 135 entrées).

## 2. Campagnes déclarées S41 (PHP CLI ≥ 8.2)
```
php outils/test_historique_267.php modules/ithakya-attenzia-instantanes.v37.php      # {"assertions":267,"resultat":"OK"}
php outils/test_complements.php    modules/ithakya-attenzia-instantanes.v36.php      # 10 750
php outils/test_complements_v37.php modules/ithakya-attenzia-instantanes.v37.php     # 10 750 (seule la condition de règle est élargie à V3.7)
```

## 3. Essais adverses HTTP (banc local uniquement)
Prérequis : Apache 2.4 + mod_php 8.3 + MariaDB, vhost HTTPS `127.0.0.1:8443` pointant sur `site/` d'une **copie** de l'archive ; configuration privée `../ithakya-pilote-prive/config.php` générée par `outils/gen_config.php` (le mot de passe de la base est lu dans un fichier local `.dbpw`, non livré) ; certificat local `/etc/ssl/ithakya/c.pem`.
Disposition attendue par les scripts : `<racine>/outils/*.py`, `<racine>/v35|v36|v37/ithakya-attenzia-instantanes.php` (copies de `modules/`), `<racine>/gen_config.php`.
```
outils/tout_rejouer.sh     # V3.6 puis V3.7 : rt_ratios, rt_integration, rt_exploitation, rt_fuzz ; puis plateau de charge 200 × 1 800 s
```
Les faits de progression sont insérés en SQL (simulation déclarée de périodes closes) ; tout le calcul passe par l'API. Les fichiers `preuves/res_*.json` sont les sorties de cette commande.
