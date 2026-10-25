"""Acompanhamento do 2º turno de 2026 (Presidente: Lula x Flávio Bolsonaro) de minuto em minuto.
- Busca os arquivos do TSE (ele2026/6258) das 27 UFs + exterior, soma o país e compara com o 2º turno de 2022 NO MESMO HORÁRIO
  (cada UF de 2022 cortada no horário do arquivo daquela UF; relógio do dia da eleição: 30/10/2022 <-> 25/10/2026).
- Acrescenta a linha do minuto em historico_2t_2026_nacional.csv (e as UFs que mudaram em historico_2t_2026_uf.csv).
- Imprime 1 linha por mudança (e um sinal de vida a cada 5 min sem mudança). A cada 10 min faz commit+push (falha não derruba).
Uso: python3 -I acompanha_2turno.py [--once] [--intervalo 60]"""
import json, os, subprocess, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(AQUI)
UFS = "AC AL AM AP BA CE DF ES GO MA MG MS MT PA PB PE PI PR RJ RN RO RR RS SC SE SP TO ZZ".split()
H_NAC, H_UF = f"{AQUI}/historico_2t_2026_nacional.csv", f"{AQUI}/historico_2t_2026_uf.csv"
ONCE = "--once" in sys.argv
INTERVALO = int(sys.argv[sys.argv.index("--intervalo") + 1]) if "--intervalo" in sys.argv else 60
S22 = pd.read_csv(f"{AQUI}/secoes_2t_2022.csv.gz", parse_dates=["recebido"])
S22["valid"] = S22.lula + S22.bolsonaro
S22_UF = {u: g.sort_values("recebido") for u, g in S22.groupby("uf")}
TOT22 = S22.groupby("uf").size().to_dict()

def baixa(uf):
    """uf = sigla ou 'BR' (arquivo nacional). Tenta até 6 vezes, com espera crescente (o TSE responde 429 quando há rajada)."""
    pasta = uf.lower(); err = ""
    for t in range(6):
        try:
            q = urllib.request.Request(f"https://resultados.tse.jus.br/oficial/ele2026/6258/dados/{pasta}/{pasta}-c0001-e006258-u.json", headers={"User-Agent": "Mozilla/5.0"})
            d = json.load(urllib.request.urlopen(q, timeout=25))
            c = {k["n"]: int(k["vap"]) for ag in d["carg"][0]["agr"] for p in ag["par"] for k in p["cand"]}
            return dict(uf=uf, hg=d["hg"], dg=d["dg"], st=int(d["s"]["st"]), ts=int(d["s"]["ts"]), vv=int(d["v"]["vv"]), lula=c.get("13", 0), fla=c.get("22", 0),
                        br=int(d["v"]["vb"]), nu=int(d["v"]["tvn"]), comp=int(d["e"]["c"]), aptos=int(d["e"]["te"]))
        except Exception as e:
            err = str(e)[:60]; time.sleep(1.5 * (t + 1))
    return dict(uf=uf, erro=err)

def corte22(uf, hg):
    g = S22_UF[uf]; h, m, s = map(int, hg.split(":")); lim = datetime(2022, 10, 30, h, m, s)
    x = g[g.recebido <= lim]; return len(x), int(x.lula.sum()), int(x.bolsonaro.sum())

def git_push():
    try:
        msg = "Acompanhamento do 2º turno 2026 (atualização automática)\n\nCo-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01GYm5aQPjLVK7kH858b3eWL"
        subprocess.run(["git", "-C", REPO, "add", H_NAC, H_UF], check=True, capture_output=True)
        r = subprocess.run(["git", "-C", REPO, "commit", "-q", "-m", msg], capture_output=True)
        if r.returncode == 0: subprocess.run(["git", "-C", REPO, "push", "-q", "-u", "origin", "ccr-c8df37d6-eo7a3z"], check=True, capture_output=True, timeout=120)
    except Exception as e:
        print(f"[aviso] commit/push falhou: {str(e)[:80]}", flush=True)

ultimo = None; ultimo_nac = None; sem_mudanca = 0; ciclo = 0; ultimo_uf = {}; cache = {}
while True:
    t0 = time.time(); agora = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%H:%M:%S")
    NAC = baixa("BR"); R = []
    for u in UFS:
        R.append(baixa(u)); time.sleep(0.2)
    falhas = [r["uf"] for r in R if "erro" in r]
    for r in R:
        if "erro" not in r: cache[r["uf"]] = r
    R = [r if "erro" not in r else cache.get(r["uf"], r) for r in R]   # falha de rede: mantém o último valor conhecido da UF
    ok = [r for r in R if "erro" not in r]
    if len(ok) >= 20:
        D = pd.DataFrame(ok)
        sec26, tot26, vv, L, F = D.st.sum(), D.ts.sum(), D.vv.sum(), D.lula.sum(), D.fla.sum()
        c22 = [corte22(r["uf"], r["hg"]) for r in ok]; sec22 = sum(a for a, _, _ in c22); L22 = sum(b for _, b, _ in c22); B22 = sum(c for _, _, c in c22)
        v22 = L22 + B22; tot22 = sum(TOT22[r["uf"]] for r in ok)
        hmax = max(D.hg); chave = (int(sec26), int(L), int(F))
        row = dict(coletado_em=agora, arquivos_ate=hmax, tse_nacional_hg=NAC.get('hg'), tse_nacional_secoes=NAC.get('st'), tse_nacional_validos=NAC.get('vv'), tse_nacional_lula=NAC.get('lula'), tse_nacional_flavio=NAC.get('fla'), secoes=int(sec26), total_secoes=int(tot26), pct_secoes=round(sec26 / tot26 * 100, 3), validos=int(vv),
                   lula=int(L), flavio=int(F), lula_pct=round(L / vv * 100, 3) if vv else None, flavio_pct=round(F / vv * 100, 3) if vv else None,
                   margem_lula_menos_flavio=int(L - F), pct_secoes_2022=round(sec22 / tot22 * 100, 3), lula_pct_2022=round(L22 / v22 * 100, 3) if v22 else None,
                   bolsonaro_pct_2022=round(B22 / v22 * 100, 3) if v22 else None, ufs_ok=len(ok) - len(falhas))
        mudou = chave != ultimo
        pd.DataFrame([row]).to_csv(H_NAC, mode="a", header=not os.path.exists(H_NAC), index=False)
        novas = [r for r in ok if ultimo_uf.get(r["uf"]) != (r["hg"], r["st"], r["lula"], r["fla"])]
        for r in novas: ultimo_uf[r["uf"]] = (r["hg"], r["st"], r["lula"], r["fla"])
        if novas: pd.DataFrame(novas).assign(coletado_em=agora).to_csv(H_UF, mode="a", header=not os.path.exists(H_UF), index=False)
        if mudou or sem_mudanca >= 4:
            ritmo = f" | nacional {NAC['st'] - ultimo_nac:+,} seções no minuto".replace(",", ".") if (ultimo and "erro" not in NAC and ultimo_nac is not None) else ""
            lider = "Lula" if L > F else "Flávio"
            if "erro" not in NAC and NAC["vv"]:
                nac = f"TSE nacional {NAC['hg']}: seções {NAC['st']:,}/{NAC['ts']:,} = {NAC['st']/NAC['ts']*100:.2f}% | Lula {NAC['lula']/NAC['vv']*100:.2f}% ({NAC['lula']:,}) x Flávio {NAC['fla']/NAC['vv']*100:.2f}% ({NAC['fla']:,}) | {'Lula' if NAC['lula']>NAC['fla'] else 'Flávio'} +{abs(NAC['lula']-NAC['fla']):,}"
            else:
                nac = "TSE nacional indisponível"
            print((f"{agora} {nac} || soma dos estados (arq. até {hmax}): {int(sec26):,} seções = {sec26/tot26*100:.2f}%, Lula {L/vv*100:.2f}% x Flávio {F/vv*100:.2f}% | "
                   f"2022 no mesmo horário: {sec22/tot22*100:.2f}% das seções, Lula {L22/v22*100:.2f}% x Bolsonaro {B22/v22*100:.2f}%{ritmo}").replace(",", ".")
                  + (f" | sem resposta (valor anterior mantido): {','.join(falhas)}" if falhas else ""), flush=True)
            sem_mudanca = 0
        else:
            sem_mudanca += 1
        ultimo = chave; ultimo_nac = NAC.get('st') if 'erro' not in NAC else ultimo_nac
        if sec26 / tot26 >= 0.9995 and not mudou: print(f"{agora} apuração praticamente concluída ({sec26/tot26*100:.3f}%). Encerrando acompanhamento.", flush=True); git_push(); break
    else:
        print(f"{agora} [aviso] só {len(ok)} UFs responderam: {falhas[:6]}", flush=True)
    ciclo += 1
    if ciclo % 10 == 0: git_push()
    if ONCE: break
    time.sleep(max(1, INTERVALO - (time.time() - t0)))
