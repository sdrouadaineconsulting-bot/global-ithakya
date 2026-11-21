import json,hashlib,sys,os,glob
root=sys.argv[1]
cache={}
def h(p):
    if p not in cache:
        try: cache[p]=hashlib.sha256(open(os.path.join(root,p),'rb').read()).hexdigest()
        except FileNotFoundError: cache[p]=None
    return cache[p]
res=[]
for f in glob.glob(root+'/**/*.json',recursive=True):
    if os.path.getsize(f)>20_000_000: continue
    try: j=json.load(open(f,encoding='utf-8'))
    except Exception: continue
    m=None
    if isinstance(j,dict):
        for k in ('fichiers','files','entries','sha256'):
            if isinstance(j.get(k),dict): m=j[k];break
            if isinstance(j.get(k),list) and j[k] and isinstance(j[k][0],dict):
                try: m={e.get('path') or e.get('chemin') or e.get('fichier'):e.get('sha256') for e in j[k]};break
                except Exception: pass
    if not m: continue
    site={k:v for k,v in m.items() if isinstance(k,str) and k.startswith('site/') and isinstance(v,str)}
    if len(site)<300: continue
    ok=sum(1 for k,v in site.items() if h(k)==v); miss=sum(1 for k in site if h(k) is None)
    res.append((ok,len(site),miss,os.path.relpath(f,root),j.get('date') if isinstance(j,dict) else None))
for r in sorted(res,reverse=True)[:12]: print(r)
