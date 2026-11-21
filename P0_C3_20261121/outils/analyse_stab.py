import json,sys,collections
d=json.load(open(sys.argv[1])); n=len(d)
exc=[(r['vue'],r['page'],r['exception']) for r in d if r.get('exception')]
ent=[(r['vue'],r['page'],r['entete']) for r in d if r.get('entete') and (len(r['entete']['positions'])>1 or len(r['entete']['hauteurs'])>1)]
chg=[(r['vue'],r['page'],[m for m in r['chargement']['mouvements'] if m['k']!='focus'][:3]) for r in d if r.get('chargement') and (r['chargement']['scrollY']!=0 or any(m['k'] in('scroll','scrollIntoView','window.scrollTo','window.scrollBy','window.scroll') for m in r['chargement']['mouvements']))]
cls=sorted([(r['chargement']['cls'],r['vue'],r['page']) for r in d if r.get('chargement')],reverse=True)[:3]
imm=[(r['vue'],r['page'],r['immobilite']) for r in d if r.get('immobilite') and (r['immobilite']['y0']!=r['immobilite']['y1'] or r['immobilite']['mv'])]
menu=[(r['vue'],r['page'],r['menu']) for r in d if r.get('menu') and (r['menu']['avant']['y']!=r['menu']['apres']['y'] or r['menu']['avant']['h']!=r['menu']['apres']['h'])]
dbx=[(r['vue'],r['page'],r['debordementX']) for r in d if r.get('debordementX',0)>0]
rel=[(r['vue'],r['page'],r['rechargement']['avant'],r['rechargement']['apres']) for r in d if r.get('rechargement') and abs(r['rechargement']['avant']-r['rechargement']['apres'])>2]
ret=[(r['vue'],r['page'],r['retour']['avant'],r['retour']['apres']) for r in d if r.get('retour') and abs(r['retour']['avant']-r['retour']['apres'])>2]
nav=[(r['vue'],r['page'],r['navigations']) for r in d if r.get('navigations') and len(set(r['navigations']))>3]
err=[(r['vue'],r['page'],r['erreurs'][:2]) for r in d if r.get('erreurs')]
print(f"{sys.argv[1].split('/')[-1]} : {n} cas")
for k,v in [('exceptions',exc),('entete_instable',ent),('mouvement_au_chargement',chg),('mouvement_sans_action(1,5 s)',imm),('menu_deplace',menu),('debordement_X',dbx),('rechargement_non_restaure',rel),('retour_non_restaure',ret),('erreurs_js',err)]:
    print(f"  {k}: {len(v)}"); [print('    ',x) for x in v[:8]]
print('  CLS max:',cls)
