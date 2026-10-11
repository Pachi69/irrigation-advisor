"""Figuras del estudio de eficiencia hídrica. Reusa el motor del harness (sim_efficiency).
Uso (desde backend/):  venv/Scripts/python.exe scripts/figures.py
Genera PNGs en scripts/_out/figs/.
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # permitir import sim_efficiency
import matplotlib
matplotlib.use("Agg")  # sin display, solo archivos
import matplotlib.pyplot as plt
import numpy as np

import sim_efficiency as se
from app.models.enums import SoilType

FIG_DIR = se.OUT_DIR / "figs"
FIG_DIR.mkdir(parents=True, exist_ok=True)

# paleta
C_SYS = "#1b7f5c"     # sistema
C_IRN = "#e07b39"     # calendario a requerimiento
C_CALSYS = "#8a8d91"  # calendario a igual agua

SOILS = [SoilType.loamy_sand, SoilType.sandy_loam, SoilType.loam]
SOIL_LBL = {
    SoilType.loamy_sand: "loamy_sand\n(TAW 105)",
    SoilType.sandy_loam: "sandy_loam\n(TAW 150)",
    SoilType.loam:       "loam\n(TAW 210)",
}


def _season_series():
    """[(tag, series)] para las 3 temporadas (usa el cache de datos del harness)."""
    return [(f"{s.year}/{str(e.year)[2:]}", se.build_series(s, e)) for s, e in se.SEASONS]


def _calendar_per_interval(series, total, n, p=se.P_DEFAULT, soil=se.SOIL):
    """Un dict de métricas por intervalo {7,10,14}d (cada uno promediado sobre fases)."""
    out = []
    for itv in se.CALENDAR_INTERVALS:
        ph = [se.run_policy(series, se.make_calendar(itv, total, n, k), p=p, soil=soil)
            for k in range(itv)]
        out.append({k: sum(x[k] for x in ph) / len(ph) for k in ph[0]})
    return out


def trajectory(series, decide, p, soil, root=se.ROOT_DEPTH):
    """Re-corre el balance día a día capturando el déficit Dr (no modifica el harness)."""
    s = se.wb._SOIL_PROPS[soil]
    taw = 1000 * (s["theta_fc"] - s["theta_wp"]) * root
    raw = p * taw
    deficit, dates, drs = 0.0, [], []
    for i, x in enumerate(series):
        irr = decide(i, deficit, raw, taw)
        res = se.wb.calculate_water_balance(x.eto, x.kc, x.precip_mm, deficit,
                                            soil, root, p, irrigation_mm=irr)
        deficit = res.water_deficit_mm
        dates.append(x.d)
        drs.append(deficit)
    return dates, drs, raw, taw


# ---------- Fig 1: resultado principal (config nominal) ----------
def fig_main(seasons):
    metrics = [("neto_mm", "Agua aplicada (mm)"),
                ("percolacion_mm", "Percolación (mm)"),
                ("dias_sed", "Días en estrés (Ks<1)")]
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.2))
    x = np.arange(len(seasons))
    w = 0.26
    for ax, (key, title) in zip(axes, metrics):
        sys_v, irn_m, irn_lo, irn_hi, cs_m, cs_lo, cs_hi = ([] for _ in range(7))
        for _, series in seasons:
            n = len(series)
            irn = se.season_irn(series)
            m = se.run_policy(series, se.decide_system)
            sys_v.append(m[key])
            irn_itv = [d[key] for d in _calendar_per_interval(series, irn, n)]
            cs_itv = [d[key] for d in _calendar_per_interval(series, m["neto_mm"], n)]
            irn_m.append(np.mean(irn_itv)); irn_lo.append(min(irn_itv)); irn_hi.append(max(irn_itv))
            cs_m.append(np.mean(cs_itv)); cs_lo.append(min(cs_itv)); cs_hi.append(max(cs_itv))
        ax.bar(x - w, sys_v, w, color=C_SYS, label="sistema")
        ax.bar(x, irn_m, w, color=C_IRN, label="calendario a requerimiento",
                yerr=[np.array(irn_m) - irn_lo, np.array(irn_hi) - irn_m], capsize=3, ecolor="#555")
        ax.bar(x + w, cs_m, w, color=C_CALSYS, label="calendario a igual agua",
                yerr=[np.array(cs_m) - cs_lo, np.array(cs_hi) - cs_m], capsize=3, ecolor="#555")
        ax.set_title(title)
        ax.set_xticks(x)
        ax.set_xticklabels([t for t, _ in seasons])
        ax.grid(axis="y", alpha=0.3)
    axes[0].legend()
    fig.suptitle("Sistema vs calendario (config nominal)", fontweight="bold")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig1_resultado_principal.png", dpi=160)
    plt.close(fig)


# ---------- Fig 2: mecanismo del timing — trayectoria Dr(t) ----------
def fig_trajectory(seasons):
    tag, series = seasons[2]  # 2023/24 (seca)
    n = len(series)
    m = se.run_policy(series, se.decide_system)
    d_sys, dr_sys, raw, taw = trajectory(series, se.decide_system, se.P_DEFAULT, se.SOIL)
    cal = se.make_calendar(10, m["neto_mm"], n, 0)
    d_cal, dr_cal, _, _ = trajectory(series, cal, se.P_DEFAULT, se.SOIL)
    fig, ax = plt.subplots(figsize=(11, 4.2))
    ax.plot(d_sys, dr_sys, color=C_SYS, lw=1.6, label="sistema (gatillo RAW → repone a FC)")
    ax.plot(d_cal, dr_cal, color=C_CALSYS, lw=1.4, ls="--", label="calendario a igual agua /10d")
    ax.axhline(raw, color="#c0392b", ls=":", lw=1, label=f"RAW = {raw:.0f} mm")
    ax.axhline(taw, color="#7f8c8d", ls=":", lw=1, label=f"TAW = {taw:.0f} mm")
    ax.invert_yaxis()  # arriba = suelo lleno (Dr=0)
    ax.set_ylabel("Déficit de zona radicular Dr (mm)")
    ax.set_title(f"Balance hídrico Dr(t) — {tag} (seca)", fontweight="bold")
    ax.legend(loc="lower right", fontsize=8)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig2_trayectoria_Dr.png", dpi=160)
    plt.close(fig)


# ---------- Fig 3: sensibilidad p × suelo (heatmap) ----------
def fig_sensitivity(seasons):
    P = se.P_GRID
    grid = np.zeros((len(P), len(SOILS)))
    annot = [[""] * len(SOILS) for _ in P]
    for i, p in enumerate(P):
        for j, soil in enumerate(SOILS):
            savs = []
            for _, series in seasons:
                irn = se.season_irn(series)
                m = se.run_policy(series, se.decide_system, p=p, soil=soil)
                savs.append(100 * (irn - m["neto_mm"]) / irn if irn > 0 else 0.0)
            grid[i, j] = np.mean(savs)
            annot[i][j] = f"{np.mean(savs):.0f}%\n({min(savs):.0f}–{max(savs):.0f})"
    fig, ax = plt.subplots(figsize=(7.8, 5))
    im = ax.imshow(grid, cmap="YlGn", vmin=0, aspect="auto")
    ax.set_xticks(range(len(SOILS))); ax.set_xticklabels([SOIL_LBL[s] for s in SOILS])
    ax.set_yticks(range(len(P))); ax.set_yticklabels([f"p = {p:.2f}" for p in P])
    for i in range(len(P)):
        for j in range(len(SOILS)):
            ax.text(j, i, annot[i][j], ha="center", va="center", fontsize=8)
    fig.colorbar(im, ax=ax, label="Ahorro de agua vs cal. a requerimiento (media de 3 temporadas)")
    ax.set_title("Sensibilidad p × suelo: ahorro de agua", fontweight="bold")
    fig.text(0.01, 0.01, "p = factor de agotamiento (umbral de riego RAW = p·TAW)",
            fontsize=8, style="italic", color="#555")
    fig.tight_layout(rect=[0, 0.04, 1, 1])
    fig.savefig(FIG_DIR / "fig3_sensibilidad_heatmap.png", dpi=160)
    plt.close(fig)


# ---------- Fig 4: límite del refill-a-FC (loam, año húmedo) ----------
def fig_limit(seasons):
    tag, series = seasons[0]  # 2021/22 (húmedo)
    p, soil = 0.50, SoilType.loam
    n = len(series)
    m = se.run_policy(series, se.decide_system, p=p, soil=soil)
    d_sys, dr_sys, raw, taw = trajectory(series, se.decide_system, p, soil)
    cal = se.make_calendar(7, m["neto_mm"], n, 0)
    d_cal, dr_cal, _, _ = trajectory(series, cal, p, soil)
    rain = [x.precip_mm for x in series]
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 5.6), sharex=True,
                                    gridspec_kw={"height_ratios": [3, 1]})
    ax1.plot(d_sys, dr_sys, color=C_SYS, lw=1.6, label="sistema (repone a FC)")
    ax1.plot(d_cal, dr_cal, color=C_CALSYS, lw=1.4, ls="--", label="calendario a igual agua /7d")
    ax1.axhline(raw, color="#c0392b", ls=":", lw=1, label=f"RAW = {raw:.0f} mm")
    ax1.axhline(taw, color="#7f8c8d", ls=":", lw=1, label=f"TAW = {taw:.0f} mm")
    ax1.invert_yaxis()
    ax1.set_ylabel("Dr (mm)")
    ax1.legend(loc="lower right", fontsize=8)
    ax1.grid(alpha=0.3)
    ax1.set_title("Límite del refill-a-FC (loam, año húmedo)", fontweight="bold")
    ax2.bar(d_cal, rain, color="#3498db", width=1.0)
    ax2.set_ylabel("Lluvia\n(mm)")
    ax2.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig4_limite_refill_FC.png", dpi=160)
    plt.close(fig)

def main():
    seasons = _season_series()
    fig_main(seasons)
    fig_trajectory(seasons)
    fig_sensitivity(seasons)
    fig_limit(seasons)
    print(f"Figuras -> {FIG_DIR}")


if __name__ == "__main__":
    main()