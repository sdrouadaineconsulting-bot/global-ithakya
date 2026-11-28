"""Écrit hls/master.m3u8 à partir des variantes produites, et ajoute les WebVTT de 04_sous_titres/<ID>.*.vtt
comme groupe SUBTITLES (une playlist d'un segment par langue). Usage : hls_master.py ID HLS_DIR FPS DUREE"""
import glob, math, os, shutil, sys
ID, HL, FPS, DUR = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4])
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
num, den = (FPS.split('/') + ['1'])[:2]
fps = float(num) / float(den or 1)
vari = [l.split() for l in open(os.path.join(HL, '.variantes')) if l.strip()]

subs = []
for vtt in sorted(glob.glob(os.path.join(ROOT, '04_sous_titres', f'{ID}.*.vtt'))):
    lang = os.path.basename(vtt)[len(ID) + 1:-4]          # ex. fr, en-US, en.auto
    code = lang.split('.')[0]
    os.makedirs(os.path.join(HL, 'subs'), exist_ok=True)
    body = open(vtt, encoding='utf-8').read()
    if 'X-TIMESTAMP-MAP' not in body:                      # alignement explicite sur le début des segments fMP4
        body = body.replace('WEBVTT', 'WEBVTT\nX-TIMESTAMP-MAP=LOCAL:00:00:00.000,MPEGTS:0', 1)
    open(os.path.join(HL, 'subs', f'{lang}.vtt'), 'w', encoding='utf-8').write(body)
    with open(os.path.join(HL, 'subs', f'{lang}.m3u8'), 'w') as f:
        f.write(f"#EXTM3U\n#EXT-X-VERSION:6\n#EXT-X-TARGETDURATION:{math.ceil(DUR)}\n#EXT-X-PLAYLIST-TYPE:VOD\n"
                f"#EXTINF:{DUR:.3f},\n{lang}.vtt\n#EXT-X-ENDLIST\n")
    subs.append((lang, code, 'auto' in lang))

with open(os.path.join(HL, 'master.m3u8'), 'w') as f:
    f.write('#EXTM3U\n#EXT-X-VERSION:7\n#EXT-X-INDEPENDENT-SEGMENTS\n')
    for i, (lang, code, auto) in enumerate(subs):
        name = f"{code}{' (automatique)' if auto else ''}"
        f.write(f'#EXT-X-MEDIA:TYPE=SUBTITLES,GROUP-ID="subs",NAME="{name}",LANGUAGE="{code}",'
                f'DEFAULT=NO,AUTOSELECT=YES,URI="subs/{lang}.m3u8"\n')   # sous-titres désactivés par défaut : la VO est conservée
    for w, h, br in sorted(vari, key=lambda r: -int(r[0])):
        bw = int(br) * 1000 + 192000
        f.write(f'#EXT-X-STREAM-INF:BANDWIDTH={bw},RESOLUTION={w}x{h},FRAME-RATE={fps:.3f},CODECS="avc1.640028,mp4a.40.2"'
                + (',SUBTITLES="subs"' if subs else '') + f'\nv{w}.m3u8\n')
print(f"{ID} : master.m3u8 ({len(vari)} variantes, {len(subs)} pistes de sous-titres)")
