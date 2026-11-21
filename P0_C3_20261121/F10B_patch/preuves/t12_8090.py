import sys; sys.argv=[sys.argv[0],sys.argv[1] if False else "http://127.0.0.1:8090"]
exec(open("f10b.py").read().split('if __name__ == "__main__":')[0])
import secrets
e=Client().register("t12e"+secrets.token_hex(3))
g2=Client(); g2.call("session"); st,js=g2.call("login",{"login":e.login,"password":e.pw}); g2.user=e.user
print("login 2e appareil",st, "score avant", g2.score())
print("révocation par 1er appareil", e.call("logout_others",{})[0])
st,js=g2.call("session"); print("2e appareil GET session:",st,"user=",js.get("user"))
st,js=g2.progress("long_started"); print("2e appareil écriture avec CSRF rafraîchi:",st,js.get("error"))
st,js=e.progress("long_started"); print("1er appareil (révocateur) écriture:",st,js.get("error"))
