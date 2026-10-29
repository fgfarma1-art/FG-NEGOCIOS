"""Verificação independente: conta votos 'computados' após o corte nos logs oficiais das urnas (resultados.tse.jus.br, 2º turno).
Uso: verifica_logs_urna.py UF OFFSET_HORAS_VS_BRASILIA SAIDA.csv   (ex.: rr -1 -> relógio local = Brasília-1h)
Corte: 17:00:00 de Brasília = 17:00:00 + OFFSET na hora local da urna."""
import concurrent.futures as cf, io, json, sys, time, zipfile, urllib.request, urllib.error, csv
uf, off, out = sys.argv[1].lower(), int(sys.argv[2]), sys.argv[3]
BASE = "https://resultados.tse.jus.br/oficial/ele2026/arquivo-urna/3221"
corte = f"{17 + off:02d}:00:00"
def get(url, tries=8):
    for t in range(tries):
        try:
            r = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            return urllib.request.urlopen(r, timeout=60).read()
        except urllib.error.HTTPError as e:
            if e.code == 404: return None
            time.sleep(2 * (t + 1))
        except Exception:
            time.sleep(2 * (t + 1))
    raise RuntimeError(url)
cs = json.loads(get(f"{BASE}/config/{uf}/{uf}-p003221-cs.json"))
secs = [(mu["cd"], z["cd"], s["ns"], s.get("nsp", "")) for u in cs["abr"] for mu in u["mu"] for z in mu["zon"] for s in z["sec"]]
def um(sec):
    mun, z, s, nsp = sec
    if nsp: return dict(mun=mun, z=z, s=s, st="AGREGADA")
    aux = get(f"{BASE}/dados/{uf}/{mun}/{z}/{s}/p003221-{uf}-m{mun}-z{z}-s{s}-aux.json")
    if aux is None: return dict(mun=mun, z=z, s=s, st="SEM_AUX")
    hs = json.loads(aux).get("hashes", [])
    tot = [h for h in hs if h.get("st") == "Totalizado"]
    h = tot[-1] if tot else (hs[-1] if hs else None)
    if not h: return dict(mun=mun, z=z, s=s, st="SEM_HASH")
    arq = {a["tp"]: a["nm"] for a in h["arq"]}
    tp = next((t for t in ("log", "logsa") if t in arq), None)
    if not tp: return dict(mun=mun, z=z, s=s, st="SEM_LOG")
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
    seen, v = set(), []
    for i, tx in enumerate(texts):
        for ln in tx.split("\n"):
            p = ln.rstrip("\r").split("\t")
            if len(p) < 5 or not p[0].startswith("25/10/2026"): continue
            if ln in seen: continue
            seen.add(ln)
            if p[4] == "O voto do eleitor foi computado": v.append(p[0][11:19])
    return dict(mun=mun, z=z, s=s, st="OK", n=len(v), apos=sum(1 for t in v if t >= corte), ultimo=max(v) if v else "")
rows = []
with cf.ThreadPoolExecutor(6) as ex:
    for r in ex.map(um, secs): rows.append(r)
with open(out, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["mun", "z", "s", "st", "n", "apos", "ultimo"]); w.writeheader(); w.writerows(rows)
ok = [r for r in rows if r["st"] == "OK"]
print(uf, "seções:", len(rows), "com log:", len(ok), "| votos computados:", sum(r["n"] for r in ok), "| após", corte, "(local):", sum(r["apos"] for r in ok), "| seções com voto após:", sum(1 for r in ok if r["apos"] > 0))
from collections import Counter; print(Counter(r["st"] for r in rows))
