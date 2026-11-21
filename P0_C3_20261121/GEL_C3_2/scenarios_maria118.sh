#!/usr/bin/env bash
# Scénarios de qualification MariaDB 11.8.10 sur le banc C3.2 (port 8094). Résultats dans preuves/mariadb_11_8/.
set -uo pipefail
S=/tmp/claude-0/-home-user-global-ithakya/17605feb-0011-5f0d-82b1-d4eac23043df/scratchpad; T=$S/tools; O=$S/P0/preuves/mariadb_11_8
M=/tmp/claude-0/m11810; BASE=$M/mariadb; SOCK=/tmp/claude-0/m118.sock; URL=http://127.0.0.1:8094
cli() { "$BASE/bin/mariadb" --no-defaults -S "$SOCK" -uroot "$@"; }
log() { echo "[$(date +%H:%M:%S)] $*" | tee -a "$O/JOURNAL_QUALIFICATION.txt"; }
cd "$T"
log "S1 antifraude F10-B T1–T14"; python3 -I f10b.py "$URL" "$S/P0/mires" "$O/S1_F10B_T1_T14.json" > "$O/S1_F10B_T1_T14.log" 2>&1; grep -oE "^\[[A-Z_]+\] T[0-9]+" "$O/S1_F10B_T1_T14.log" | tr '\n' ' ' | tee -a "$O/JOURNAL_QUALIFICATION.txt"; echo | tee -a "$O/JOURNAL_QUALIFICATION.txt"
log "S2 session révoquée (T12b)"; sed "s#http://127.0.0.1:8088#$URL#" t12.py > t12_8094.py; python3 -I t12_8094.py | tee "$O/S2_T12B_SESSION_REVOQUEE.txt"
log "S3 concurrence 10 comptes + rafale 30"; python3 -I maria_conc.py "$URL" "$S/P0/mires" "$O/S3_CONCURRENCE.json" | cut -c1-260 | tee -a "$O/JOURNAL_QUALIFICATION.txt"
log "S4 deadlocks / attentes de verrou"; echo "deadlock_detectes=$(cli -e 'SHOW ENGINE INNODB STATUS\G' | grep -c 'LATEST DETECTED DEADLOCK') erreurs_php=$(grep -ciE 'fatal|deadlock|1213|1205|lock wait' "$O/php_serveur.log")" | tee -a "$O/JOURNAL_QUALIFICATION.txt"
log "S5 parcours légitime complet par l'interface"; timeout 260 node parcours_v1.cjs "$URL" 01-signature 390 844 "$O/S5_PARCOURS_LEGITIME_390.json" | python3 -c "import json,sys;d=json.load(sys.stdin);print('final',d['final'],'V1',[(x['ouverture']['t'],x['pendant_lecture']) for x in d['v1']])" | tee -a "$O/JOURNAL_QUALIFICATION.txt"
log "S6 arrêt brutal (kill -9) et redémarrage"
Q="SELECT COUNT(*) FROM itp_users; SELECT COUNT(*), SUM(data LIKE '%court_finished%') FROM itp_work_progress; SELECT COUNT(*) FROM itp_states;"
cli -N ithakya_q118 -e "$Q" > "$O/S6_avant.txt"; kill -9 "$(cat /tmp/claude-0/m118.pid)"; sleep 2
(nohup "$BASE/bin/mariadbd" --no-defaults --basedir="$BASE" --datadir="$M/data" --user=root --socket="$SOCK" --port=3308 --bind-address=127.0.0.1 --pid-file=/tmp/claude-0/m118.pid --innodb-buffer-pool-size=256M --log-error="$O/mariadbd_erreurs.log" > /dev/null 2>&1 &)
for i in $(seq 1 40); do cli -e 'select 1' >/dev/null 2>&1 && break; sleep 1; done
cli -N ithakya_q118 -e "$Q" > "$O/S6_apres.txt"; cmp -s "$O/S6_avant.txt" "$O/S6_apres.txt" && log "données identiques après arrêt brutal ($(tr '\n' ' ' < "$O/S6_apres.txt"))" || log "ÉCART de données après arrêt brutal"
grep -E "crash recovery|Starting crash" "$O/mariadbd_erreurs.log" | tail -1 | tee -a "$O/JOURNAL_QUALIFICATION.txt"
cli ithakya_q118 -e "CHECK TABLE itp_users, itp_work_progress, itp_states, itp_meta, itp_entries;" | tee "$O/S6_CHECK_TABLE.txt"
curl -s -o /dev/null -w "API après redémarrage %{http_code}\n" "$URL/api/ithakya-pilote.php?action=session" | tee -a "$O/JOURNAL_QUALIFICATION.txt"
log "S7 migrations documentées, rejeu, retours (base ithakya_q118_migr)"
"$BASE/bin/mariadb-dump" --no-defaults -S "$SOCK" -uroot --no-data ithakya_q118 | cli ithakya_q118_migr
cli ithakya_q118_migr -e "INSERT INTO itp_meta SELECT * FROM ithakya_q118.itp_meta;"
n() { cli -N -e "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='ithakya_q118_migr'"; }
SQL=/tmp/claude-0/gel_c32/x/prive/sql; echo "base v6 : $(n) tables" > "$O/S7_MIGRATIONS.txt"
for f in migration_programmation_p2_mysql.sql migration_avatars_m09_mysql.sql seed_avatars_m09_mysql.sql migration_reactions_p4_t8_mysql.sql migration_economie_v036_mysql.sql migration_liste_attente_pilote_mysql.sql migration_attenzia_instantanes_v1_mysql.sql; do out=$(cli ithakya_q118_migr < "$SQL/$f" 2>&1); echo "$f rc=$? tables=$(n) ${out:0:200}" >> "$O/S7_MIGRATIONS.txt"; done
echo "--- rejeu" >> "$O/S7_MIGRATIONS.txt"
for f in migration_programmation_p2_mysql.sql migration_reactions_p4_t8_mysql.sql migration_economie_v036_mysql.sql migration_liste_attente_pilote_mysql.sql; do out=$(cli ithakya_q118_migr < "$SQL/$f" 2>&1); echo "$f rc=$? ${out:0:200}" >> "$O/S7_MIGRATIONS.txt"; done
echo "--- retours" >> "$O/S7_MIGRATIONS.txt"
for f in retour_attenzia_instantanes_v1_mysql.sql retour_reactions_p4_t8_mysql.sql retour_avatars_m09_mysql.sql; do out=$(cli ithakya_q118_migr < "$SQL/$f" 2>&1); echo "$f rc=$? tables=$(n) ${out:0:200}" >> "$O/S7_MIGRATIONS.txt"; done
cli -N -e "SELECT engine, COUNT(*) FROM information_schema.tables WHERE table_schema='ithakya_q118_migr' GROUP BY engine" >> "$O/S7_MIGRATIONS.txt"; cat "$O/S7_MIGRATIONS.txt"
log "S8 contraintes et index"; cli -e "SELECT table_name, index_name, non_unique, GROUP_CONCAT(column_name ORDER BY seq_in_index) cols FROM information_schema.statistics WHERE table_schema='ithakya_q118' AND table_name IN ('itp_work_progress','itp_states','itp_users','itp_progress2','itp_entries') GROUP BY table_name,index_name,non_unique;" | tee "$O/S8_INDEX.txt"
log "S9 collation des tables"; cli -e "SELECT table_name, table_collation FROM information_schema.tables WHERE table_schema='ithakya_q118' ORDER BY 1;" | tee "$O/S9_COLLATIONS.txt"
log "fin des scénarios"
