"""Banc antifraude F10-B / crédits XP-Points (W360 C2). Local uniquement (127.0.0.1).
Distingue : statut HTTP, écriture (progress), attribution effective (XP/Points serveur)."""
import json, sys, time, os, secrets, subprocess, threading, urllib.request, urllib.error, http.cookiejar

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8087"
API = BASE + "/api/ithakya-pilote.php"
OUT = []


class Client:
    def __init__(self):
        self.jar = http.cookiejar.CookieJar()
        self.op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))
        self.csrf = None; self.user = None

    def call(self, action, body=None, method=None, extra=""):
        url = f"{API}?action={action}{extra}"
        data = None if body is None else json.dumps(body).encode()
        req = urllib.request.Request(url, data=data, method=method or ("POST" if body is not None else "GET"))
        if body is not None:
            req.add_header("Content-Type", "application/json"); req.add_header("Origin", BASE)
            req.add_header("X-CSRF-Token", self.csrf or "")
        try:
            with self.op.open(req, timeout=60) as r:
                raw = r.read(); st = r.status
        except urllib.error.HTTPError as e:
            raw = e.read(); st = e.code
        try: js = json.loads(raw)
        except Exception: js = {"_bytes": len(raw)}
        if isinstance(js, dict) and js.get("csrf"): self.csrf = js["csrf"]
        return st, js

    def media(self, content, rng=None):
        req = urllib.request.Request(f"{API}?action=lecture_media&content={content}")
        if rng: req.add_header("Range", rng)
        try:
            with self.op.open(req, timeout=120) as r: return r.status, len(r.read())
        except urllib.error.HTTPError as e: return e.code, 0

    def register(self, login):
        self.call("session")
        self.login = login; self.pw = "phrase de passe de banc " + secrets.token_hex(6)
        st, js = self.call("register", {"login": login, "display_name": "Banc " + login[-4:], "password": self.pw})
        assert st == 201, (st, js); self.user = js["user"]; return self

    def score(self):
        st, js = self.call("progression")
        p = js.get("progression", js)
        return (p.get("xp"), p.get("points"), (p.get("pending") or {}).get("xp"))

    def progress(self, event, value=None, context="signature"):
        b = {"context": context, "event": event, "owner_id": self.user["id"]}
        if value is not None: b["value"] = value
        return self.call("progress", b)

    def clock(self, content, pos, image, view=None, ticket=None):
        b = {"owner_id": self.user["id"], "content": content, "position_ms": pos, "image": image}
        if view: b["view"] = view; b["ticket"] = ticket
        return self.call("lecture_suivi", b)


def frames(mp4):
    raw = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", mp4, "-an", "-vf",
        "fps=8:start_time=0,scale=8:6:flags=area,format=rgb24", "-f", "rawvideo", "-"],
        capture_output=True, check=True).stdout
    out = []
    for k in range(0, len(raw), 144):
        d = raw[k:k + 144]
        out.append(bytes((77 * d[i] + 150 * d[i + 1] + 29 * d[i + 2]) >> 8 for i in range(0, 144, 3)).hex())
    return out


def rec(test, expected, observed, verdict, note=""):
    OUT.append({"test": test, "attendu": expected, "observe": observed, "verdict": verdict, "note": note})
    print(f"[{verdict}] {test} | attendu: {expected} | observé: {observed} {('| ' + note) if note else ''}", flush=True)


def play_clock(c, content, fr, duration_ms, step_ms=1000, speed=1.0, image_ok=True):
    """Témoins de lecture : position avance de step_ms toutes les step_ms/speed ms (temps réel si speed=1)."""
    st, js = c.clock(content, 0, fr[0] if image_ok else "00" * 48)
    view, ticket = js.get("view"), js.get("ticket")
    pos = 0; codes = [st]
    while pos < duration_ms:
        time.sleep(step_ms / 1000 / speed)
        pos = min(duration_ms, pos + step_ms)
        img = fr[min(len(fr) - 1, round(pos * 8 / 1000))] if image_ok else "00" * 48
        st, js = c.clock(content, pos, img, view, ticket)
        codes.append(st)
        if st == 200: view, ticket = js["view"], js["ticket"]
        else: break
    return codes, view, ticket


if __name__ == "__main__":
    MEDIA = sys.argv[2]  # dossier des mires
    fr21 = frames(os.path.join(MEDIA, "court21.mp4"))
    run = secrets.token_hex(3)

    # T1 : HTTP 200 sans crédit (événements non crédités)
    a = Client().register("f10a" + run)
    s0 = a.score()
    st, _ = a.progress("saved", True)
    st2, _ = a.progress("note_k", 5)
    rec("T1 événements non crédités (saved, note_k)", "HTTP 200, XP inchangé", f"HTTP {st}/{st2}, score {s0}->{a.score()}",
        "CONFORME" if st == st2 == 200 and a.score()[:2] == s0[:2] else "ECART")

    # T2 : fin de Court forgée immédiate
    st, js = a.progress("court_started"); st, js = a.progress("court_finished", {"coverage": 1})
    rec("T2 fin de Court forgée immédiate (couverture 1.0)", "409, aucun XP", f"HTTP {st} {js.get('error')}, score {a.score()}",
        "CONFORME" if st == 409 and a.score()[0] == 0 else "ECART")

    # T3 : plancher temporel atteint, aucun média servi
    b = Client().register("f10b" + run)
    b.progress("court_started"); time.sleep(16)
    st, js = b.progress("court_finished", {"coverage": 1})
    rec("T3 plancher 15 s atteint, média jamais servi", "409 playback_delivery, aucun XP", f"HTTP {st} {js.get('error')}, score {b.score()}",
        "CONFORME" if st == 409 and b.score()[0] == 0 else "ECART")

    # T4 : média téléchargé intégralement + plancher, sans témoins de lecture
    st_m, n = b.media("signature.court")
    st, js = b.progress("court_finished", {"coverage": 1})
    rec("T4 média téléchargé 100 % + plancher, sans témoins", "409 playback_timeline, aucun XP",
        f"média HTTP {st_m} {n} o ; fin HTTP {st} {js.get('error')}, score {b.score()}",
        "CONFORME" if st == 409 and b.score()[0] == 0 else "ECART")

    # T5 : témoins forgés avec images fausses, rythme réel
    codes, _, _ = play_clock(b, "signature.court", fr21, 21000, image_ok=False)
    st, js = b.progress("court_finished", {"coverage": 1})
    rec("T5 témoins rythme réel, images fausses", "409, aucun XP", f"témoins {sorted(set(codes))} ; fin HTTP {st} {js.get('error')}, score {b.score()}",
        "CONFORME" if st == 409 and b.score()[0] == 0 else "ECART")

    # T6 : témoins accélérés x4 avec images exactes (calculées depuis le fichier servi)
    c = Client().register("f10c" + run)
    c.progress("court_started"); c.media("signature.court")
    codes, _, _ = play_clock(c, "signature.court", fr21, 21000, speed=4)
    time.sleep(max(0, 16 - 21 / 4))
    st, js = c.progress("court_finished", {"coverage": 1})
    rec("T6 témoins accélérés ×4, images exactes", "409, aucun XP", f"témoins {sorted(set(codes))} ; fin HTTP {st} {js.get('error')}, score {c.score()}",
        "CONFORME" if st == 409 and c.score()[0] == 0 else "ECART")

    # T7 : rejeu d'un ancien témoin
    st0, js0 = c.clock("signature.court", 0, fr21[0])
    v, t_old = js0["view"], js0["ticket"]
    time.sleep(0.3); st1, js1 = c.clock("signature.court", 300, fr21[2], v, t_old)
    time.sleep(0.3); st2, js2 = c.clock("signature.court", 600, fr21[5], v, t_old)
    rec("T7 rejeu d'un témoin déjà consommé", "409 playback_ticket", f"1er {st1}, rejeu {st2} {js2.get('error')}",
        "CONFORME" if st1 == 200 and st2 == 409 else "ECART")

    # T8 : témoin d'un autre compte (vol de ticket)
    d = Client().register("f10d" + run)
    st, js = d.clock("signature.court", 900, fr21[7], js1.get("view"), js1.get("ticket"))
    rec("T8 témoin de A présenté par B", "409/422, refus", f"HTTP {st} {js.get('error')}", "CONFORME" if st in (409, 422) else "ECART")

    # T9 : client scripté sans humain, rythme réel, images exactes (limite structurelle F10-B)
    e = Client().register("f10e" + run)
    e.progress("court_started"); e.media("signature.court")
    t0 = time.time(); codes, _, _ = play_clock(e, "signature.court", fr21, 21000)
    st, js = e.progress("court_finished", {"coverage": 1}); sc = e.score()
    rec("T9 automate sans affichage, rythme réel, images calculées depuis le fichier servi",
        "réserve F10-B : crédit non distinguable d'un humain", f"durée {time.time()-t0:.1f} s ; fin HTTP {st} {js.get('error','')} ; score {sc}",
        "LIMITE_STRUCTURELLE" if st == 200 and sc[0] > 0 else "NON_REPRODUIT",
        "le serveur atteste une livraison et une progression temps réel, pas une présence humaine")

    # T10 : concurrence / idempotence sur la même fin (20 appels simultanés)
    res = []
    def hit(): res.append(e.progress("court_finished", {"coverage": 1})[0])
    th = [threading.Thread(target=hit) for _ in range(20)]
    [x.start() for x in th]; [x.join() for x in th]
    sc2 = e.score()
    rec("T10 20 fins de Court concurrentes après crédit", "un seul crédit, XP inchangé", f"HTTP {sorted(set(res))}, score {sc}->{sc2}",
        "CONFORME" if sc2[:2] == sc[:2] else "ECART")

    # T11 : quiz sans Long sur œuvre non historique / historique sans Court
    f = Client().register("f10f" + run)
    st, js = f.progress("quiz_answered", 1)
    rec("T11 quiz sans lecture (œuvre historique, sans Court)", "409 quiz_requires_playback, aucun XP", f"HTTP {st} {js.get('error')}, score {f.score()}",
        "CONFORME" if st == 409 and f.score()[0] == 0 else "ECART")

    # T12 : session révoquée (« déconnecter les autres appareils ») puis écriture depuis l'ancienne session
    g2 = Client(); g2.call("session")
    st, js = g2.call("login", {"login": e.login, "password": e.pw}); g2.user = e.user
    st_r, _ = e.call("logout_others", {})
    st, js = g2.progress("long_started")
    rec("T12 écriture depuis une session révoquée", "401", f"révocation {st_r} ; ancienne session HTTP {st} {js.get('error')}",
        "CONFORME" if st == 401 else "ECART")

    # T13 : CSRF / origine
    st, js = a.call("progress", {"context": "signature", "event": "saved", "value": True, "owner_id": a.user["id"]})
    a2 = Client(); a2.jar = a.jar; a2.op = a.op; a2.csrf = "0" * 64
    st2, js2 = a2.call("progress", {"context": "signature", "event": "saved", "value": True, "owner_id": a.user["id"]})
    rec("T13 jeton CSRF faux", "403 csrf", f"valide {st}, faux {st2} {js2.get('error')}", "CONFORME" if st2 == 403 else "ECART")

    # T14 : owner_id d'un autre compte
    st, js = a.call("progress", {"context": "signature", "event": "saved", "value": True, "owner_id": e.user["id"]})
    rec("T14 owner_id d'un autre compte", "409 session_changed", f"HTTP {st} {js.get('error')}", "CONFORME" if st == 409 else "ECART")

    json.dump(OUT, open(sys.argv[3], "w"), ensure_ascii=False, indent=1)
