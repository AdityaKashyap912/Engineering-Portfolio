"""
LANDING GEAR DYNAMICS - FINAL VERSION
Educational 1-DOF oleo-pneumatic strut model (illustrative parameters, NOT validated aircraft data).

Model : m*s'' = m*g*(1 - lift) - F_strut,  s = strut compression (down = +)
Strut : gas spring + quadratic orifice damping (weaker on rebound) + hard stop
Study : 3 designs (fixed orifice / metering pin / pin + longer gas column),
        off-design scenarios, Monte Carlo robustness, analytic + energy checks.
Run   : python landing_gear_final.py      (takes about 1-3 minutes)
Needs : pip install numpy scipy matplotlib pillow
"""
import os, json, csv
import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp, cumulative_trapezoid
from scipy.optimize import brentq
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.patches import Rectangle, Circle

# ---------------- output folder ----------------
# Resolved relative to this file so all outputs land in ./results/ wherever it is run.
_BASE = os.path.dirname(os.path.abspath(__file__))
SAVE_DIR = os.path.join(_BASE, "results")
os.makedirs(SAVE_DIR, exist_ok=True)

# ---------------- parameters ----------------
G, N_GAS, S_MAX, K_STOP, REBOUND = 9.81, 1.35, 0.35, 5e6, 0.30
M0, V0, LIFT0 = 4500.0, 3.0, 1.0          # mass per gear (kg), sink speed (m/s), lift/weight
F0_BASE, H0_BASE = 20000.0, 0.40          # gas preload (N), gas column length (m)
KE0 = 0.5 * M0 * V0**2


# ---------------- model ----------------
def make(name, F0, h0, c):
    return {"name": name, "F0": F0, "h0": h0, "c": c}


def force(s, v, d, f0_scale=1.0):
    """Returns total, gas, damper, hard-stop force (N)."""
    F0, h0 = d["F0"] * f0_scale, d["h0"]
    sg = min(max(s, 0.0), h0 - 1e-8)
    Fa = F0 * (h0 / (h0 - sg))**N_GAS
    c = max(float(d["c"](max(s, 0.0))), 0.0)
    Fd = c * v * abs(v) if v >= 0 else REBOUND * c * v * abs(v)
    Fs = K_STOP * max(s - S_MAX, 0.0)
    return Fa + Fd + Fs, Fa, Fd, Fs


def simulate(d, mass=M0, sink=V0, lift=LIFT0, f0_scale=1.0, T=1.5):
    def f(t, y):
        s, v = y
        return [v, (mass * G * (1 - lift) - force(s, v, d, f0_scale)[0]) / mass]

    def ev(t, y):
        return y[0]
    ev.terminal, ev.direction = True, -1
    sol = solve_ivp(f, (0, T), [0.0, sink], t_eval=np.arange(0, T, 0.001),
                    events=ev, max_step=0.001, rtol=1e-7, atol=1e-9)
    s, v = sol.y
    p = np.array([force(a, b, d, f0_scale) for a, b in zip(s, v)])
    return {"t": sol.t, "s": s, "v": v, "F": p[:, 0], "Fa": p[:, 1], "Fd": p[:, 2], "Fs": p[:, 3]}


def metrics(r, mass=M0, sink=V0):
    ke, fpk, spk = 0.5 * mass * sink**2, r["F"].max(), r["s"].max()
    return {"F_peak_kN": fpk / 1e3, "s_peak_m": spk, "utilisation_pct": 100 * spk / S_MAX,
            "margin_mm": (S_MAX - spk) * 1e3, "shape_index": ke / (fpk * spk),
            "rebound_mps": max(-r["v"][-1], 0.0), "bottomed": bool(spk > S_MAX)}


def static_compression(d, mass=M0):
    ratio = d["F0"] / (mass * G)
    return 0.0 if ratio >= 1 else d["h0"] * (1 - ratio**(1 / N_GAS))


# ---------------- design A: best fixed orifice ----------------
cs = np.linspace(0, 30000, 61)
pk, ps = [], []
for c0 in cs:
    r = simulate(make("t", F0_BASE, H0_BASE, lambda s, c=c0: c))
    pk.append(r["F"].max()); ps.append(r["s"].max())
pk, ps = np.array(pk), np.array(ps)
ok = np.where(ps <= S_MAX)[0]
c_best = cs[ok[np.argmin(pk[ok])]]

# ---------------- designs B, C: metering pin (damping vs stroke) ----------------
KN = np.array([0.0, 0.1, 0.2, 0.3])
CB = np.array([6534.0, 8858.0, 13676.0, 22010.0])
CC = np.array([5336.0, 6862.0, 9480.0, 9863.0])
designs = [make(f"A: fixed orifice (c={c_best:.0f})", F0_BASE, H0_BASE, lambda s: c_best),
           make("B: metering pin", F0_BASE, 0.40, lambda s: np.interp(s, KN, CB)),
           make("C: pin + longer gas column", F0_BASE, 0.50, lambda s: np.interp(s, KN, CC))]
nominal = [simulate(d) for d in designs]
nom_m = [metrics(r) for r in nominal]

# ---------------- checks ----------------
d0, r0 = designs[0], nominal[0]
i_max = int(np.argmax(r0["s"]))
E_gas = F0_BASE * H0_BASE / (N_GAS - 1) * ((H0_BASE / (H0_BASE - r0["s"]))**(N_GAS - 1) - 1)
E_kin = 0.5 * M0 * r0["v"]**2
E_dmp = cumulative_trapezoid(r0["Fd"] * r0["v"], r0["t"], initial=0)
E_tot = E_kin + E_gas + E_dmp + 0.5 * K_STOP * np.maximum(r0["s"] - S_MAX, 0)**2
energy_err = float(E_tot[i_max] - KE0)
static_closed = static_compression(d0)
static_root = brentq(lambda s: force(s, 0.0, d0)[1] - M0 * G, 0, H0_BASE - 1e-6)
print("\nCHECKS (design A)")
print(f"  energy balance error at max compression: {energy_err:.3f} J of {KE0:.0f} J ({100*abs(energy_err)/KE0:.4f}%)")
print(f"  static compression closed form {static_closed*1e3:.2f} mm vs numerical root {static_root*1e3:.2f} mm")
print(f"  energy split at max compression: gas {E_gas[i_max]:.0f} J, damper {E_dmp[i_max]:.0f} J")
print(f"  rebound speed (lift = weight, weak rebound damping): {nom_m[0]['rebound_mps']:.2f} m/s")

# ---------------- off-design scenarios ----------------
SINKS = [1.5, 2.0, 2.5, 3.0, 3.4, 3.7, 4.0, 4.3]
scen = [(f"sink {v} m/s", {"sink": v}) for v in SINKS]
scen += [("lift 67%", {"lift": 0.67}), ("gas charge -20%", {"f0_scale": 0.8}),
         ("gas charge -40%", {"f0_scale": 0.6}), ("mass +15%", {"mass": M0 * 1.15})]
rows = []
for label, kw in scen:
    for d in designs:
        r = simulate(d, **kw)
        m = metrics(r, mass=kw.get("mass", M0), sink=kw.get("sink", V0))
        rows.append({"scenario": label, "design": d["name"], **{k: m[k] for k in
                     ("F_peak_kN", "s_peak_m", "utilisation_pct", "margin_mm", "bottomed")}})
with open(os.path.join(SAVE_DIR, "scenario_results.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)

print("\nSCENARIOS (peak force kN / stroke used %)  [!] = bottomed out")
for label, _ in scen:
    line = f"  {label:18s}"
    for row in [x for x in rows if x["scenario"] == label]:
        flag = "[!]" if row["bottomed"] else "   "
        line += f" {row['F_peak_kN']:7.1f}/{row['utilisation_pct']:5.1f}{flag}"
    print(line)

# ---------------- Monte Carlo robustness ----------------
NMC = 120
rng = np.random.default_rng(1)
smp = {"sink": rng.uniform(1.5, 3.7, NMC), "lift": rng.uniform(0.67, 1.0, NMC),
       "mass": np.clip(rng.normal(M0, 250, NMC), 3500, 5500), "f0": rng.uniform(0.7, 1.05, NMC)}
mc = {d["name"]: {"F": [], "bottom": []} for d in designs}
print(f"\nMONTE CARLO ({NMC} random landings: sink 1.5-3.7 m/s, lift 67-100%, mass +-250 kg, gas charge 70-105%)")
for i in range(NMC):
    for d in designs:
        r = simulate(d, mass=smp["mass"][i], sink=smp["sink"][i], lift=smp["lift"][i], f0_scale=smp["f0"][i])
        mc[d["name"]]["F"].append(r["F"].max() / 1e3)
        mc[d["name"]]["bottom"].append(bool(r["s"].max() > S_MAX))
mc_summary = {}
for d in designs:
    F, b = np.array(mc[d["name"]]["F"]), np.array(mc[d["name"]]["bottom"])
    mc_summary[d["name"]] = {"mean_kN": float(F.mean()), "p95_kN": float(np.percentile(F, 95)),
                             "prob_bottom_pct": float(100 * b.mean())}
    print(f"  {d['name']:34s} mean {F.mean():6.1f} kN | 95th pct {np.percentile(F, 95):6.1f} kN | bottoms out {100*b.mean():4.1f}%")

# ---------------- summary file (for the portfolio website) ----------------
summary = {"nominal": {d["name"]: nom_m[i] for i, d in enumerate(designs)},
           "static_mm": {d["name"]: 1e3 * static_compression(d) for d in designs},
           "checks": {"energy_error_J": energy_err, "energy_error_pct": 100 * abs(energy_err) / KE0,
                      "static_closed_mm": static_closed * 1e3, "static_root_mm": static_root * 1e3},
           "monte_carlo": mc_summary, "ideal_flat_force_kN": KE0 / S_MAX / 1e3,
           "scenarios": rows,
           "generated_at": __import__("datetime").datetime.now().astimezone().isoformat(),
           "files": ["1_design_comparison.png", "2_energy_accounting.png", "3_robustness.png",
                     "landing_gear_animation.gif", "scenario_results.csv", "results.json"]}
with open(os.path.join(SAVE_DIR, "results.json"), "w") as fh:
    json.dump(summary, fh, indent=2)

# ---------------- figures ----------------
fig1, ax = plt.subplots(1, 3, figsize=(16, 4.8))
sa = np.linspace(0, 0.3, 100)
for d, r in zip(designs, nominal):
    ax[0].plot(r["s"], r["F"] / 1e3, label=d["name"]); ax[1].plot(r["t"], r["F"] / 1e3, label=d["name"])
    ax[2].plot(sa, [d["c"](x) for x in sa], label=d["name"])
ax[0].axhline(KE0 / S_MAX / 1e3, color="k", ls=":", label="ideal flat force")
ax[0].set(xlabel="Compression (m)", ylabel="Force (kN)", title="Force vs stroke")
ax[1].set(xlabel="Time (s)", ylabel="Force (kN)", title="Load on airframe")
ax[2].set(xlabel="Compression (m)", ylabel="Damping coefficient", title="Damping profile")
for a in ax: a.grid(True); a.legend(fontsize=8)
fig1.tight_layout(); fig1.savefig(os.path.join(SAVE_DIR, "1_design_comparison.png"), dpi=150)

fig2, ax2 = plt.subplots(1, 2, figsize=(12, 4.6))
for y, lab in [(E_kin, "Kinetic"), (E_gas, "Gas spring (stored)"), (E_dmp, "Damper (heat)")]:
    ax2[0].plot(r0["t"], y / 1e3, label=lab)
ax2[0].plot(r0["t"], E_tot / 1e3, "k--", label="Total")
ax2[0].set(xlabel="Time (s)", ylabel="Energy (kJ)", title="Energy accounting (design A)")
sl = slice(0, i_max + 1)
ax2[1].plot(r0["s"][sl], r0["F"][sl] / 1e3, label="Total")
ax2[1].fill_between(r0["s"][sl], 0, r0["Fa"][sl] / 1e3, alpha=.3, label="Gas part")
ax2[1].fill_between(r0["s"][sl], r0["Fa"][sl] / 1e3, r0["F"][sl] / 1e3, alpha=.3, label="Damper part")
ax2[1].set(xlabel="Compression (m)", ylabel="Force (kN)", title="Area under curve = energy absorbed")
for a in ax2: a.grid(True); a.legend()
fig2.tight_layout(); fig2.savefig(os.path.join(SAVE_DIR, "2_energy_accounting.png"), dpi=150)

fig3, ax3 = plt.subplots(1, 3, figsize=(16, 4.8))
for k, d in enumerate(designs):
    rr = [x for x in rows if x["design"] == d["name"] and x["scenario"].startswith("sink")]
    F = [x["F_peak_kN"] for x in rr]; U = [x["utilisation_pct"] for x in rr]
    ax3[0].plot(SINKS, F, "o-", label=d["name"]); ax3[1].plot(SINKS, U, "o-", label=d["name"])
    for v, f_, u, x in zip(SINKS, F, U, rr):
        if x["bottomed"]:
            ax3[0].plot(v, f_, "rx", ms=11); ax3[1].plot(v, u, "rx", ms=11)
ax3[1].axhline(100, color="r", ls="--", label="stroke limit")
ax3[0].set(xlabel="Sink speed (m/s)", ylabel="Peak force (kN)", title="Peak force vs sink speed (red x = bottomed)")
ax3[1].set(xlabel="Sink speed (m/s)", ylabel="Stroke used (%)", title="Stroke margin")
names = [d["name"].split(":")[0] for d in designs]
ax3[2].bar(names, [mc_summary[d["name"]]["prob_bottom_pct"] for d in designs], color=["C0", "C1", "C2"])
ax3[2].set(ylabel="Probability of bottoming out (%)", title=f"Monte Carlo ({NMC} random landings)")
for a in ax3[:2]: a.grid(True); a.legend(fontsize=8)
fig3.tight_layout(); fig3.savefig(os.path.join(SAVE_DIR, "3_robustness.png"), dpi=150)

# ---------------- animation ----------------
FS, HOLD, RW, L0 = 5, 15, 0.15, 0.90
CYL = L0 - S_MAX
nf = max(len(r["t"]) for r in nominal) // FS + HOLD
fig4, ax4 = plt.subplots(1, 3, figsize=(12, 5)); parts = []
for a, d in zip(ax4, designs):
    a.set_xlim(-0.8, 0.8); a.set_ylim(-0.1, 1.6); a.set_aspect("equal"); a.set_title(d["name"], fontsize=8)
    a.axhline(0, color="k", lw=3); a.axhline(RW + L0 - S_MAX, color="r", ls=":", lw=1)
    a.add_patch(Circle((0, RW), RW, fc="dimgray"))
    rod = Rectangle((-0.025, RW), 0.05, L0, fc="silver"); cyl = Rectangle((-0.06, 0), 0.12, CYL, fc="steelblue")
    body = Rectangle((-0.6, 0), 1.2, 0.25, fc="lightsteelblue", ec="k")
    for p in (rod, cyl, body): a.add_patch(p)
    parts.append((rod, cyl, body, a.text(0, 1.45, "", ha="center", fontsize=9)))


def draw(fr):
    for (rod, cyl, body, tx), r in zip(parts, nominal):
        k = min(fr * FS, len(r["t"]) - 1); y = RW + L0 - r["s"][k]
        rod.set_height(y - RW); cyl.set_y(y - CYL); body.set_y(y)
        tx.set_text(f"t={r['t'][k]*1e3:.0f} ms  s={r['s'][k]*1e3:.0f} mm\nF={r['F'][k]/1e3:.0f} kN")


anim = FuncAnimation(fig4, draw, frames=nf, interval=40, blit=False)
anim.save(os.path.join(SAVE_DIR, "landing_gear_animation.gif"), writer=PillowWriter(fps=25))
print("\nSaved plots, gif, scenario_results.csv and results.json to:", SAVE_DIR)
