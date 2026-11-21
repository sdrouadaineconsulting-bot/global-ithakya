#!/usr/bin/env bash
# Qualification MariaDB 11.8.10 (archive officielle) pour C3.2 — banc isolé, données fictives, rien en production.
# Instance : /tmp/claude-0/m11810/mariadb, port 3308, socket /tmp/claude-0/m118.sock. Banc PHP : copie de C3.2 + mires, port 8094.
set -euo pipefail
S=/tmp/claude-0/-home-user-global-ithakya/17605feb-0011-5f0d-82b1-d4eac23043df/scratchpad
M=/tmp/claude-0/m11810; BASE=$M/mariadb; DATA=$M/data; SOCK=/tmp/claude-0/m118.sock; OUT=$S/P0/preuves/mariadb_11_8; mkdir -p "$OUT"
log() { echo "[$(date +%H:%M:%S)] $*" | tee -a "$OUT/JOURNAL_QUALIFICATION.txt"; }
cli() { "$BASE/bin/mariadb" --no-defaults -S "$SOCK" -uroot "$@"; }

if [ ! -d "$BASE" ]; then mkdir -p "$BASE" && tar -xzf "$M/mariadb-11.8.10-linux-systemd-x86_64.tar.gz" -C "$BASE" --strip-components=1; fi
"$BASE/bin/mariadbd" --version | tee "$OUT/VERSION_SERVEUR.txt"
if [ ! -d "$DATA/mysql" ]; then
  "$BASE/scripts/mariadb-install-db" --no-defaults --basedir="$BASE" --datadir="$DATA" --user=root --auth-root-authentication-method=socket > "$OUT/installation.log" 2>&1
fi
demarrer() { (nohup "$BASE/bin/mariadbd" --no-defaults --basedir="$BASE" --datadir="$DATA" --user=root --socket="$SOCK" --port=3308 --bind-address=127.0.0.1 --pid-file=/tmp/claude-0/m118.pid --innodb-buffer-pool-size=256M --log-error="$OUT/mariadbd_erreurs.log" > /dev/null 2>&1 &); for i in $(seq 1 40); do cli -e 'select 1' >/dev/null 2>&1 && return 0; sleep 1; done; return 1; }
cli -e 'select 1' >/dev/null 2>&1 || demarrer
cli -e "SELECT VERSION() version, @@version_comment commentaire, @@default_storage_engine moteur, @@sql_mode sql_mode, @@tx_isolation isolation, @@character_set_server charset, @@collation_server collation\G" | tee "$OUT/PARAMETRES_SERVEUR.txt"
PW=$(cat /tmp/claude-0/mdb/.pw)
cli -e "DROP DATABASE IF EXISTS ithakya_q118; CREATE DATABASE ithakya_q118 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci; CREATE USER IF NOT EXISTS 'ithakya_banc'@'127.0.0.1' IDENTIFIED BY '$PW'; GRANT ALL ON ithakya_q118.* TO 'ithakya_banc'@'127.0.0.1';
DROP DATABASE IF EXISTS ithakya_q118_migr; CREATE DATABASE ithakya_q118_migr CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci; GRANT ALL ON ithakya_q118_migr.* TO 'ithakya_banc'@'127.0.0.1';"
log "MariaDB $(cli -N -e 'select version()') prêt (bases ithakya_q118, ithakya_q118_migr)"

# Banc PHP sur une copie de C3.2 reconstituée (la candidate n'est pas modifiée), mires de banc et pages régénérées dans la copie.
B=$S/P0/BQ118
if [ ! -d "$B" ]; then
  cp -a /tmp/claude-0/gel_c32/x "$B"; cp "$S/P0/B/site/media/"*.mp4 "$B/site/media/"
  (cd "$B" && PYTHONDONTWRITEBYTECODE=1 python3 source/outils/generer.py source site > "$OUT/generation_banc.log" 2>&1)
  (cd "$B" && ITHAKYA_RECETTE_DRIVER=mysql ITHAKYA_RECETTE_PORT=8094 ITHAKYA_DB_HOST=127.0.0.1 ITHAKYA_DB_PORT=3308 ITHAKYA_DB_NAME=ithakya_q118 ITHAKYA_DB_USER=ithakya_banc ITHAKYA_DB_PASSWORD="$PW" php recette-privee/generer_config_locale.php > /dev/null)
  (cd "$B" && python3 source/outils/preparer-preuves-lecture.py site ithakya-pilote-prive | tail -1)
fi
pkill -f "php -S 127.0.0.1:8094" || true; sleep 1
(cd "$B" && PHP_CLI_SERVER_WORKERS=8 nohup php -S 127.0.0.1:8094 -t site > "$OUT/php_serveur.log" 2>&1 &); sleep 2
curl -s -o /dev/null -w "API session %{http_code}\n" "http://127.0.0.1:8094/api/ithakya-pilote.php?action=session" | tee -a "$OUT/JOURNAL_QUALIFICATION.txt"
cli -e "SELECT COUNT(*) tables_, SUM(engine='InnoDB') innodb FROM information_schema.tables WHERE table_schema='ithakya_q118'; SELECT * FROM ithakya_q118.itp_meta;" | tee "$OUT/SCHEMA_AUTO.txt"
php -r 'echo "PHP ", PHP_VERSION, " pdo_mysql=", extension_loaded("pdo_mysql") ? "oui" : "non", " client=", (new PDO("mysql:host=127.0.0.1;port=3308;dbname=ithakya_q118","ithakya_banc",$argv[1]))->getAttribute(PDO::ATTR_CLIENT_VERSION), " serveur=", (new PDO("mysql:host=127.0.0.1;port=3308;dbname=ithakya_q118","ithakya_banc",$argv[1]))->getAttribute(PDO::ATTR_SERVER_VERSION), "\n";' "$PW" | tee "$OUT/PILOTE_PHP.txt"
log "fin de préparation"
