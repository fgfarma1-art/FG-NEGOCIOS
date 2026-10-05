"""Projeção do 2º turno 2026 combinando TRÊS lentes independentes (cada uma com sua incerteza) e 3 cenários.
 Lente A: transferência por UF calibrada em 2022 (projecao_2turno.py, sigma=0,25 = quanto 2026 pode diferir de 2022).
 Lente B: premissas de transferência por candidato do 1º turno (julgamento do analista, Dirichlet com incerteza) + novos eleitores.
 Lente C: histórico de 2º turnos (2002-2022): variação da % do líder entre os dois turnos, normalizada pelo tamanho do 'pool' de outros (números de memória).
Pesos iguais por padrão. Nenhuma lente é verdade; a mistura mede o quanto os métodos discordam."""
import json, os, sys
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__)); rng = np.random.default_rng(7); N = 40000
r1 = json.load(open("/tmp/r1_2026_total.json")); c = {k.split("|")[1]: v for k, v in r1["cands"].items()}
L1, F1, vv = r1["lula"], r1["fla"], r1["vv"]; O = vv - L1 - F1
# ---- Lente A ----
A = np.load(f"{AQUI}/_sim_share_sigma0.25.npy"); A = rng.choice(A, N)
# ---- Lente B ----
grp = {"direita": (c["RONALDO CAIADO"] + c["ZEMA"] + c["VETERINÁRIO WILSON GRASSI"], (0.08, 0.68, 0.24)),
       "cury": (c["ESCRITOR AUGUSTO CURY"], (0.22, 0.45, 0.33)), "renan": (c["RENAN SANTOS"], (0.17, 0.35, 0.48)),
       "esq": (c["SAMARA"] + c["HERTZ DIAS"] + c["CLARIANA BARAO"] + c["EDMILSON COSTA"] + c["RUI COSTA PIMENTA"], (0.70, 0.06, 0.24))}
assert abs(sum(v for v, _ in grp.values()) - O) < 5, (sum(v for v, _ in grp.values()), O)
KAPPA = 12.0
L2 = np.full(N, float(L1)); F2 = np.full(N, float(F1))
for v, p in grp.values():
    d = rng.dirichlet(np.array(p) * KAPPA, N); L2 += v * d[:, 0]; F2 += v * d[:, 1]
NV = rng.normal(0.6e6, 0.8e6, N); lam = np.clip(rng.normal(0.5, 0.10, N), 0, 1); L2 += NV * lam; F2 += NV * (1 - lam)
B = L2 / (L2 + F2)
# ---- Lente C ----
hist = {2002: (-5.43, 30.4), 2006: (+6.97, 9.75), 2010: (-2.95, 20.5), 2014: (-3.71, 24.9), 2018: (-5.99, 24.7), 2022: (-1.96, 8.37)}
s = np.array([a / b for a, b in hist.values()]); mu, sd = s.mean(), s.std(ddof=1) * np.sqrt(1 + 1 / len(s))
two = L1 / (L1 + F1); pool = O / vv * 100
# s = variação da % do LÍDER (Flávio); a % de Lula é o complemento. Aqui o líder em 2026 é Flávio (two-party Flávio = 1-two)
Cshare = 1 - ((1 - two) * 100 + rng.normal(mu, sd, N) * pool) / 100
print(f"1º turno 2026: Lula {L1/vv*100:.2f}% Flávio {F1/vv*100:.2f}% | two-party Lula {two*100:.2f}% | pool de outros {O/vv*100:.2f}% ({O:,})")
print(f"Lente C: variação normalizada média {mu:+.2f}, desvio {sd:.2f} -> mudança esperada do líder {mu*pool:+.2f} pp (±{sd*pool:.2f})")
def resumo(nome, x):
    print(f"{nome}: Lula % válidos 2º turno: p10 {np.percentile(x,10)*100:.1f} | mediana {np.median(x)*100:.1f} | p90 {np.percentile(x,90)*100:.1f} | P(Flávio) {(x<0.5).mean()*100:.0f}%")
resumo("Lente A (2022 por UF)    ", A); resumo("Lente B (por candidato)   ", B); resumo("Lente C (histórico 2002-22)", Cshare)
for w in ((1/3, 1/3, 1/3), (0.5, 0.25, 0.25), (0.25, 0.5, 0.25), (0.25, 0.25, 0.5)):
    n = [int(N * x) for x in w]; M = np.concatenate([A[:n[0]], B[:n[1]], Cshare[:n[2]]])
    print(f"  pesos A/B/C {w[0]:.2f}/{w[1]:.2f}/{w[2]:.2f}: P(Flávio vence) = {(M<0.5).mean()*100:.0f}% | mediana Lula {np.median(M)*100:.1f}%")
M = np.concatenate([A[: N // 3], B[: N // 3], Cshare[: N // 3]])
p10, p50, p90 = [np.percentile(M, q) for q in (10, 50, 90)]
V2 = 119.0e6  # válidos esperados no 2º turno (projecao_2turno.py)
print(f"\nMISTURA (pesos iguais): P(Flávio) = {(M<0.5).mean()*100:.0f}% | P(Lula) = {(M>=0.5).mean()*100:.0f}%")
for nome, q in (("Cenário favorável a Lula (p90: só 10% dos casos são melhores para Lula)", p90), ("Cenário base (mediana)", p50), ("Cenário favorável a Flávio (p10: só 10% dos casos são melhores para Flávio)", p10)):
    L, F = q * V2, (1 - q) * V2; print(f"  {nome}: Lula {q*100:.1f}% ({L/1e6:.1f} mi) x Flávio {(1-q)*100:.1f}% ({F/1e6:.1f} mi) | margem {abs(L-F)/1e6:.1f} mi a favor de {'Lula' if L>F else 'Flávio'}")
# o que Lula precisa (aritmética)
need = (F1 - L1) / O
print(f"\nAritmética: Flávio abre {F1-L1:,} votos. Para Lula virar só com o pool de outros, precisa de (fração Lula - fração Flávio) > {need:.2f} do pool de {O:,} (em 2022 foi {(3086495-7134009)/9897870:+.2f}).")
np.save(f"{AQUI}/_mistura.npy", M)
