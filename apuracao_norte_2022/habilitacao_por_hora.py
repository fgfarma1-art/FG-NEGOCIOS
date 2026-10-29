"""Habilitações por hora (Brasília) nos logs das urnas: total e NÃO biométricas (sem 'Tipo de habilitação do eleitor [biométrica]' no ciclo do eleitor).
Uso: habilitacao_por_hora.py UF OFFSET_HORAS SAIDA.csv   (OFFSET: horas do relógio local em relação a Brasília, ex.: ac -2, am -1, ba 0). Retomável."""
import collections, concurrent.futures as cf, csv, io, json, os, sys, time, zipfile, urllib.request, urllib.error
uf, off, out = sys.argv[1].lower(), int(sys.argv[2]), sys.argv[3]
BASE = "https://resultados.tse.jus.br/oficial/ele2026/arquivo-urna/3221"
def get(url, tries=8):
    for t in range(tries):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=60).read()
        except urllib.error.HTTPError as e:
            if e.code == 404: return None
            time.sleep(2 * (t + 1))
        except Exception:
            time.sleep(2 * (t + 1))
    raise RuntimeError(url)
cs = json.loads(get(f"{BASE}/config/{uf}/{uf}-p003221-cs.json"))
secs = [(mu["cd"], z["cd"], s["ns"], s.get("nsp", "")) for u in cs["abr"] for mu in u["mu"] for z in mu["zon"] for s in z["sec"]]
BIO = "Tipo de habilitação do eleitor [biométrica]"
def um(sec):
    mun, z, s, nsp = sec
    if nsp: return [dict(mun=mun, z=z, s=s, hora="AGREGADA", hab=0, nbio=0, comp=0)]
    aux = get(f"{BASE}/dados/{uf}/{mun}/{z}/{s}/p003221-{uf}-m{mun}-z{z}-s{s}-aux.json")
    if aux is None: return [dict(mun=mun, z=z, s=s, hora="SEM_AUX", hab=0, nbio=0, comp=0)]
    hs = json.loads(aux).get("hashes", [])
    tot = [h for h in hs if h.get("st") == "Totalizado"]
    h = tot[-1] if tot else (hs[-1] if hs else None)
    arq = {a["tp"]: a["nm"] for a in (h or {}).get("arq", [])}
    tp = next((t for t in ("log", "logsa") if t in arq), None)
    if not tp: return [dict(mun=mun, z=z, s=s, hora="SEM_LOG", hab=0, nbio=0, comp=0)]
    b = get(f"{BASE}/dados/{uf}/{mun}/{z}/{s}/{h['hash']}/{arq[tp]}")
    texts = []
    def col(zf, d):
        for n in zf.namelist():
            raw = zf.read(n)
            if n.lower().endswith((".zip", ".jez")) and d < 3:
                try: col(zipfile.ZipFile(io.BytesIO(raw)), d + 1); continue
                except zipfile.BadZipFile: pass
            texts.append(raw.decode("latin-1", "replace"))
    col(zipfile.ZipFile(io.BytesIO(b)), 0)
    seen = set(); ev = []
    for i, tx in enumerate(texts):
        for ln in tx.split("\n"):
            p = ln.rstrip("\r").split("\t")
            if len(p) < 5 or not p[0].startswith("25/10/2026"): continue
            if ln in seen: continue
            seen.add(ln); ev.append((p[0][11:19], p[4]))
    ev.sort(key=lambda x: x[0])
    c = collections.defaultdict(lambda: [0, 0, 0]); bio = False
    for t, msg in ev:
        hh = int(t[:2]) - off
        if msg == BIO: bio = True
        elif msg == "Eleitor foi habilitado":
            c[hh][0] += 1
            if not bio: c[hh][1] += 1
        elif msg == "O voto do eleitor foi computado":
            c[hh][2] += 1; bio = False
    return [dict(mun=mun, z=z, s=s, hora=h_, hab=v[0], nbio=v[1], comp=v[2]) for h_, v in sorted(c.items())] or [dict(mun=mun, z=z, s=s, hora="VAZIO", hab=0, nbio=0, comp=0)]
F = ["mun", "z", "s", "hora", "hab", "nbio", "comp"]
feitos = set()
if os.path.exists(out):
    for r in csv.DictReader(open(out)): feitos.add((r["mun"], r["z"], r["s"]))
pend = [x for x in secs if (str(x[0]), str(x[1]), str(x[2])) not in feitos]
novo = not os.path.exists(out)
with open(out, "a", newline="") as f, cf.ThreadPoolExecutor(int(os.environ.get("THREADS", "12"))) as ex:
    w = csv.DictWriter(f, fieldnames=F)
    if novo: w.writeheader()
    for i, fu in enumerate(cf.as_completed([ex.submit(um, x) for x in pend])):
        try: w.writerows(fu.result())
        except Exception as e: print("erro", e, flush=True)
        if i % 500 == 0: f.flush(); print(i, "/", len(pend), flush=True)
print("fim", uf)
