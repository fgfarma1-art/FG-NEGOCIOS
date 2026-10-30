"""Coleta, por município, o 1º e o 2º turno de 2026 (Presidente) no TSE: eleitorado, comparecimento, abstenção, brancos, nulos, Lula e Flávio.
Arquivos: resultados.tse.jus.br/oficial/ele2026/<6257|6258>/dados/<uf>/<uf><cod>-c0001-e00<ele>-u.json   (config: .../config/mun-e006257-cm.json)
Uso: python3 -I municipios_2026.py <saida.csv>   (pausa global quando o TSE responde 429)"""
import csv, json, sys, threading, time, urllib.error, urllib.request
from concurrent.futures import ThreadPoolExecutor
OUT = sys.argv[1]; H = {"User-Agent": "Mozilla/5.0"}
lock = threading.Lock(); pausa_ate = [0.0]; cont = {"ok": 0, "falha": 0, "429": 0}

def get(url):
    for t in range(8):
        agora = time.time()
        if pausa_ate[0] > agora: time.sleep(pausa_ate[0] - agora)
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=25))
        except urllib.error.HTTPError as e:
            if e.code == 429:
                with lock: cont["429"] += 1; pausa_ate[0] = time.time() + 3 + 2 * t
            elif e.code == 404: return None
            time.sleep(1 + t)
        except Exception: time.sleep(1 + t)
    return "falha"

def le(ele, uf, cod):
    d = get(f"https://resultados.tse.jus.br/oficial/ele2026/{ele}/dados/{uf}/{uf}{cod}-c0001-e00{ele}-u.json")
    if d is None or d == "falha": return d
    c = {k["n"]: int(k["vap"]) for ag in d["carg"][0]["agr"] for p in ag["par"] for k in p["cand"]}
    return dict(hg=d["hg"], sec=int(d["s"]["st"]), sec_tot=int(d["s"]["ts"]), aptos=int(d["e"]["te"]), aptos_ap=int(d["e"]["est"]), comp=int(d["e"]["c"]), abst=int(d["e"]["a"]),
                vv=int(d["v"]["vv"]), br=int(d["v"]["vb"]), nu=int(d["v"]["tvn"]), lula=c.get("13", 0), fla=c.get("22", 0))

cfg = get("https://resultados.tse.jus.br/oficial/ele2026/6257/config/mun-e006257-cm.json")
mun = [(a["cd"], m["cd"], m["cdi"], m["nm"]) for a in cfg["abr"] for m in a.get("mu", [])]
print("municípios:", len(mun), flush=True)
CAMPOS = ["hg", "sec", "sec_tot", "aptos", "aptos_ap", "comp", "abst", "vv", "br", "nu", "lula", "fla"]
cols = ["uf", "cod_tse", "cod_ibge", "municipio"] + [f"{c}_1t" for c in CAMPOS] + [f"{c}_2t" for c in CAMPOS]
feitos = [0]; t0 = time.time()
def tarefa(m):
    uf, cod, ibge, nm = m; a = le(6257, uf, cod); b = le(6258, uf, cod)
    with lock:
        feitos[0] += 1
        if a in (None, "falha") or b in (None, "falha"): cont["falha"] += 1; return None
        cont["ok"] += 1
        return [uf.upper(), cod, ibge, nm] + [a[c] for c in CAMPOS] + [b[c] for c in CAMPOS]
with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(cols)
    with ThreadPoolExecutor(6) as ex:
        for i, r in enumerate(ex.map(tarefa, mun), 1):
            if r: w.writerow(r)
            if i % 250 == 0: f.flush(); print(f"{i}/{len(mun)} | ok {cont['ok']} falhas {cont['falha']} 429 {cont['429']} | {time.time()-t0:.0f}s", flush=True)
print("FIM", cont, f"{time.time()-t0:.0f}s", flush=True)
