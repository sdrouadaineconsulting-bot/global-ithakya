#!/usr/bin/env bash
# Banc MariaDB isolé pour la variante F10-B. Usage : monter_wf.sh <port> <base> <seuil|defaut>
set -euo pipefail
S=/tmp/claude-0/-home-user-global-ithakya/17605feb-0011-5f0d-82b1-d4eac23043df/scratchpad
PORT=$1; DB=$2; SEUIL=$3; B=$S/P0/BF_$PORT
test ! -e "$B" || { echo "banc déjà présent : $B"; exit 1; }
cp -a "$S/P0/WF" "$B"
cp "$S/P0/B/site/media/"*.mp4 "$B/site/media/"
mariadb -S /tmp/claude-0/mdb/m.sock -e "DROP DATABASE IF EXISTS $DB; CREATE DATABASE $DB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci; GRANT ALL ON $DB.* TO 'ithakya_banc'@'127.0.0.1';"
cd "$B"
ITHAKYA_RECETTE_DRIVER=mysql ITHAKYA_RECETTE_PORT=$PORT ITHAKYA_DB_HOST=127.0.0.1 ITHAKYA_DB_PORT=3307 ITHAKYA_DB_NAME=$DB ITHAKYA_DB_USER=ithakya_banc ITHAKYA_DB_PASSWORD="$(cat /tmp/claude-0/mdb/.pw)" php recette-privee/generer_config_locale.php >/dev/null
if [ "$SEUIL" != "defaut" ]; then
  php -r '$c=require "ithakya-pilote-prive/config.php"; $c["credit_rate_max_hour"]=(int)$argv[1]; file_put_contents("ithakya-pilote-prive/config.php", "<?php\n// BANC LOCAL UNIQUEMENT\nreturn ".var_export($c,true).";\n");' "$SEUIL"
fi
python3 source/outils/preparer-preuves-lecture.py site ithakya-pilote-prive | tail -1
(PHP_CLI_SERVER_WORKERS=8 nohup php -S 127.0.0.1:$PORT -t site > "$S/P0/php_bf_$PORT.log" 2>&1 &)
sleep 1.5
curl -s -o /dev/null -w "banc $PORT session %{http_code}\n" "http://127.0.0.1:$PORT/api/ithakya-pilote.php?action=session"
