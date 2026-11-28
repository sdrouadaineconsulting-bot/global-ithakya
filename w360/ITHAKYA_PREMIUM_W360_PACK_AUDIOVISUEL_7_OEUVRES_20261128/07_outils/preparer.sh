#!/bin/sh
# ITHAKYA W360 — qualification et déclinaisons d'un ou plusieurs masters.
# Usage : sh 07_outils/preparer.sh [ID ...]      (sans ID : tous les masters présents dans 01_masters/)
# Entrée : 01_masters/<ID>.<ext>  (ID = identifiant de 07_outils/oeuvres.json, ex. W360-ST-COURT.mov)
# Sorties : 06_manifeste/ffprobe/<ID>.json, 06_manifeste/sha256/<ID>.sha256,
#           02_declinaisons/<ID>/<ID>_repli.mp4, 02_declinaisons/<ID>/hls/master.m3u8 (+ variantes, + sous-titres),
#           03_affiches_miniatures/<ID>/affiche.jpg, affiche_dynamique.mp4, miniature_{25,50,75}.jpg
# Puis régénère le manifeste (06_manifeste/manifeste.json, qualification.csv, RAPPORT_MANQUANTS.md).
# Principes : master jamais modifié ; proportions, cadence et dynamique sonore conservées (aucune normalisation) ;
# aucun remontage : chaque déclinaison couvre la durée intégrale du master.
# Prérequis : ffmpeg et ffprobe (7+ recommandé), python3, sha256sum.
set -eu
ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"
command -v ffmpeg >/dev/null && command -v ffprobe >/dev/null || { echo "ffmpeg/ffprobe introuvables"; exit 1; }

ids="$*"
[ -n "$ids" ] || ids=$(ls 01_masters 2>/dev/null | grep -E '^W360-' | sed 's/\.[^.]*$//' | sort -u)
[ -n "$ids" ] || { echo "Aucun master dans 01_masters/ : rien à préparer."; python3 07_outils/manifeste.py; exit 0; }

for ID in $ids; do
  M=$(ls 01_masters/"$ID".* 2>/dev/null | head -1)
  [ -n "$M" ] || { echo "! $ID : master absent de 01_masters/"; continue; }
  echo "== $ID ($M)"
  mkdir -p 06_manifeste/ffprobe 06_manifeste/sha256 "02_declinaisons/$ID/hls" "03_affiches_miniatures/$ID"

  # 1. Qualification
  ffprobe -v error -print_format json -show_format -show_streams -count_packets "$M" > "06_manifeste/ffprobe/$ID.json"
  sha256sum "$M" | sed "s|  .*|  $(basename "$M")|" > "06_manifeste/sha256/$ID.sha256"

  eval "$(python3 - "06_manifeste/ffprobe/$ID.json" <<'EOF'
import json,sys
d=json.load(open(sys.argv[1])); v=next(s for s in d['streams'] if s['codec_type']=='video')
a=[s for s in d['streams'] if s['codec_type']=='audio']
print(f"W={v['width']} H={v['height']} FPS={v.get('avg_frame_rate') or v['r_frame_rate']} DUR={d['format']['duration']}")
print(f"ACODEC={a[0]['codec_name'] if a else 'none'} ACH={a[0].get('channels',2) if a else 0}")
EOF
)"
  # 2. MP4 de repli : H.264 High, plafonné à 1920 px de large, cadence native, audio conservé si AAC
  SC="scale='min($W,1920)':-2:flags=lanczos"
  if [ "$ACODEC" = aac ]; then AOPT="-c:a copy"; elif [ "$ACODEC" = none ]; then AOPT="-an"; else AOPT="-c:a aac -b:a 256k -ac $ACH"; fi
  ffmpeg -nostdin -y -v error -i "$M" -map 0:v:0 -map 0:a:0? -vf "$SC" -c:v libx264 -preset slow -crf 18 -profile:v high -pix_fmt yuv420p \
    -fps_mode passthrough $AOPT -movflags +faststart "02_declinaisons/$ID/${ID}_repli.mp4"

  # 3. HLS adaptatif : échelle par largeur (jamais au-dessus du master), images-clés alignées toutes les 2 s, fMP4
  HL="02_declinaisons/$ID/hls"; : > "$HL/.variantes"
  for rung in 3840:16000 2560:10000 1920:6000 1280:3500 854:1600 640:900; do
    RW=${rung%%:*}; BR=${rung##*:}
    [ "$RW" -le "$W" ] || continue
    ffmpeg -nostdin -y -v error -i "$M" -map 0:v:0 -map 0:a:0? -vf "scale=$RW:-2:flags=lanczos" -c:v libx264 -preset slow -profile:v high -pix_fmt yuv420p \
      -crf 20 -maxrate ${BR}k -bufsize $((BR*2))k -force_key_frames "expr:gte(t,n_forced*2)" -sc_threshold 0 -fps_mode passthrough \
      $( [ "$ACODEC" = none ] && echo -an || echo -c:a aac -b:a 192k -ac 2 ) \
      -f hls -hls_time 6 -hls_playlist_type vod -hls_segment_type fmp4 \
      -hls_fmp4_init_filename "v${RW}_init.mp4" -hls_segment_filename "$HL/v${RW}_%04d.m4s" "$HL/v${RW}.m3u8"
    RH=$(ffprobe -v error -select_streams v:0 -show_entries stream=height -of csv=p=0 "$HL/v${RW}_init.mp4")
    echo "$RW $RH $BR" >> "$HL/.variantes"
  done
  # Plus petite largeur que le master non couverte par l'échelle : variante unique à la taille native
  [ -s "$HL/.variantes" ] || { echo "! $ID : master plus étroit que 640 px, variante native"; }

  # 4. Sous-titres WebVTT présents dans 04_sous_titres/<ID>.*.vtt → groupe SUBTITLES du HLS
  python3 07_outils/hls_master.py "$ID" "$HL" "$FPS" "$DUR"

  # 5. Affiches et miniatures (proportions natives)
  for pc in 25 50 75; do
    T=$(python3 -c "print(round($DUR*$pc/100,3))")
    ffmpeg -nostdin -y -v error -ss "$T" -i "$M" -frames:v 1 -vf "scale=640:-2:flags=lanczos" -q:v 3 "03_affiches_miniatures/$ID/miniature_${pc}.jpg"
  done
  T=$(python3 -c "print(round($DUR*0.10,3))")
  ffmpeg -nostdin -y -v error -ss "$T" -i "$M" -frames:v 1 -vf "scale='min($W,1920)':-2:flags=lanczos" -q:v 2 "03_affiches_miniatures/$ID/affiche.jpg"
  T=$(python3 -c "print(round($DUR*0.20,3))")
  ffmpeg -nostdin -y -v error -ss "$T" -t 6 -i "$M" -an -vf "scale='min($W,1280)':-2:flags=lanczos" -c:v libx264 -crf 23 -pix_fmt yuv420p \
    -movflags +faststart "03_affiches_miniatures/$ID/affiche_dynamique.mp4"
done
python3 07_outils/manifeste.py
