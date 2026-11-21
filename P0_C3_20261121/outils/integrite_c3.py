import sys,re,os,html,hashlib,json
C2,C3=sys.argv[1],sys.argv[2]; delta=[l.strip() for l in open(sys.argv[3]) if l.strip()]
def vis(s):
    s=re.sub(r'(?is)<(script|style)[^>]*>.*?</\1>',' ',s); attrs=' '.join(re.findall(r'\b(?:alt|title|aria-label|placeholder|content)="([^"]*)"',s))
    s=re.sub(r'<[^>]+>',' ',s); return re.sub(r'\s+',' ',html.unescape(s+' '+attrs)).strip()
norm=lambda s: re.sub(r'\?sha=[0-9a-f]+','',s)
res={'pages':0,'texte_identique':0,'identique_hors_sha':0,'ecarts_hors_sha':[],'sha_faux':[],'sha_ok':0}
for f in delta:
    if not f.endswith('.html'): continue
    a=open(os.path.join(C2,f),encoding='utf8').read(); b=open(os.path.join(C3,f),encoding='utf8').read(); res['pages']+=1
    res['texte_identique']+= vis(a)==vis(b)
    if norm(a)==norm(b): res['identique_hors_sha']+=1
    else: res['ecarts_hors_sha'].append(f)
    if f.startswith('site/'):
        for url,h in re.findall(r'(?:src|href)="([^"?#:]+\.(?:js|css|json))\?sha=([0-9a-f]+)"',b):
            p=os.path.normpath(os.path.join(C3,os.path.dirname(f),url))
            if h=='0' or not os.path.isfile(p): continue
            if hashlib.sha256(open(p,'rb').read()).hexdigest()[:12]==h: res['sha_ok']+=1
            else: res['sha_faux'].append((f,url,h))
# médias et données
med=[x for x in delta if re.search(r'\.(mp4|webp|svg|jpg|jpeg|png|vtt|srt|ico|json)$',x)]
res['medias_ou_donnees_modifies']=med
print(json.dumps(res,ensure_ascii=False,indent=1))
