import sys,re,os,hashlib,glob,json
R=sys.argv[1]; st={'ok':0,'faux':0,'zero':0,'sans':0}; fauxf=set(); zerof=set(); sansf=set()
for f in glob.glob(R+'/site/**/*.html',recursive=True):
    if '/pagefind/' in f or '/media/' in f: continue
    t=open(f,encoding='utf8').read()
    for tag,url,q in re.findall(r'<(script|link)\b[^>]*?\b(?:src|href)="([^"?#:]+\.(?:js|css))(\?sha=[0-9a-z]+)?"',t):
        p=os.path.normpath(os.path.join(os.path.dirname(f),url))
        if not os.path.isfile(p) or url.startswith('/'): continue
        rel=os.path.relpath(p,R+'/site')
        if re.search(r'-[0-9a-f]{12}\.(js|css)$',url) and not q: continue
        h=hashlib.sha256(open(p,'rb').read()).hexdigest()[:12]
        if not q: st['sans']+=1; sansf.add(rel)
        elif q=='?sha=0': st['zero']+=1; zerof.add(rel)
        elif q[5:]==h: st['ok']+=1
        else: st['faux']+=1; fauxf.add(rel)
print(json.dumps({'refs':st,'fichiers_sha_faux':sorted(fauxf),'fichiers_sha_0':sorted(zerof),'fichiers_sans_version':sorted(sansf)},ensure_ascii=False))
