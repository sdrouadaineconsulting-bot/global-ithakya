import sys, threading, time, json
sys.argv=[sys.argv[0], sys.argv[1], sys.argv[2], sys.argv[3]]
src=open("f10b.py").read().split('if __name__ == "__main__":')[0]; exec(src)
BASE_=sys.argv[1]; fr=frames(sys.argv[2]+"/court21.mp4"); N=10
users=[Client().register("mc%02d"%i+secrets.token_hex(2)) for i in range(N)]
for u in users: u.progress("court_started"); u.media("signature.court")
th=[threading.Thread(target=play_clock,args=(u,"signature.court",fr,21000)) for u in users]
t0=time.time(); [t.start() for t in th]; [t.join() for t in th]
res=[None]*N
def fin(i): res[i]=users[i].progress("court_finished",{"coverage":1})[0]
th=[threading.Thread(target=fin,args=(i,)) for i in range(N)]; [t.start() for t in th]; [t.join() for t in th]
sc=[u.score()[:2] for u in users]
# rafale concurrente même compte, quiz + fin
u=users[0]; r2=[]
def q(): r2.append(u.progress("court_finished",{"coverage":1})[0])
th=[threading.Thread(target=q) for _ in range(30)]; [t.start() for t in th]; [t.join() for t in th]
out={"comptes":N,"lecture_s":round(time.time()-t0,1),"fins_simultanees_http":res,"scores":sc,"rafale_30_meme_compte_http":sorted(set(r2)),"score_apres_rafale":u.score()[:2],"logins":[x.login for x in users]}
json.dump(out,open(sys.argv[3],"w"),indent=1); print(json.dumps(out)[:600])
