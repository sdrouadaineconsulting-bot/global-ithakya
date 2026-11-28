#!/usr/bin/env bash
# S42 — rejeu intégral des suites HTTP sur V3.6 (S41) puis V3.7 (S42), puis plateau de charge sur V3.7.
set -u; cd "$(dirname "$0")"; W=..; MOD=/var/www/ithakya/site/api/ithakya-attenzia-instantanes.php
for V in v36 v37; do
  cp $W/$V/ithakya-attenzia-instantanes.php $MOD; chown www-data $MOD; sleep 3
  python3 -I rt_ratios.py $W/res_${V}_ratios.json && python3 -I rt_integration.py $W/res_${V}_integration.json && CIBLE=$V python3 -I rt_exploitation.py $W/res_${V}_exploitation.json && python3 -I rt_fuzz.py $V $W/res_${V}_fuzz.json || echo "ECHEC $V"
done
cp $W/v37/ithakya-attenzia-instantanes.php $MOD; chown www-data $MOD; sleep 3
python3 -I -c "import sys;sys.path.insert(0,'.');from banc42 import *;reset_atz()"
python3 -I charge_plateau.py $W/res_v37_charge_200_1800s.json 200 1800 || echo "ECHEC charge"
echo FIN
