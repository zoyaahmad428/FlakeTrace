"""Planned-vs-actual Gantt for Chapter 3 (figure ch3:fig:gantt).

Run from the repository root:  py mid-eval-report/scripts/gantt.py
Writes mid-eval-report/figures/m2/gantt.png.

Plan rows and windows: the proposal Gantt (mid-eval-report/figures/shared/proposal_gantt.jpeg),
month resolution. Actual dates: merge commits on main (git log --merges --first-parent) or dated
files in the repository. Phase spans and the defence date: stated by the team. Status words:
Chapter 3 and Chapter 6 of the report.
"""

from datetime import date
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.patches import Patch, Rectangle
from matplotlib.lines import Line2D

OUT = Path(__file__).resolve().parents[1] / "figures" / "m2" / "gantt.png"
AS_OF = date(2026, 10, 12)

# Categorical slots 1-4 of the validated default palette (dataviz skill, light mode).
OWNER = {"M1": "#2a78d6", "M2": "#eb6834", "M3": "#1baf7a", "Joint": "#eda100"}
# White surface: the figure is printed on a white page, so any tint would show as a box.
INK, INK2, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#8a8984", "#e6e5e0", "#ffffff"

# (task, owner, plan start, plan end, actual date or None, status)
SECTIONS = [
    ("Iteration 1  (Aug - Oct)", [
        ("Architecture and interface contracts", "Joint", date(2026, 8, 1), date(2026, 9, 30), date(2026, 10, 9), "Late: merged 9 Oct (#1)"),
        ("Benchmark / threshold / threat-model freeze", "Joint", date(2026, 8, 1), date(2026, 10, 31), date(2026, 10, 9), "Partial: no threat model"),
        ("Static bytecode extraction", "M1", date(2026, 8, 1), date(2026, 10, 31), date(2026, 10, 9), "Done (#9, #34)"),
        ("Sandbox runner", "M2", date(2026, 8, 1), date(2026, 10, 31), date(2026, 10, 9), "Partial: no container (#10)"),
        ("Benchmark manifest and baselines", "M3", date(2026, 8, 1), date(2026, 10, 31), date(2026, 10, 11), "Done (#1, #54)"),
    ]),
    ("Iteration 2  (Nov - Jan)", [
        ("Resource normalisation and graph", "M1", date(2026, 9, 1), date(2027, 1, 31), None, "Not started"),
        ("Dynamic resource collection", "M1", date(2026, 11, 1), date(2026, 12, 31), None, "Planned"),
        ("Search, ranking and adaptive policy", "M2", date(2026, 11, 1), date(2027, 1, 31), date(2026, 10, 9), "Partial: search, no ranking (#11)"),
        ("Ablation harness, metrics, statistics", "M3", date(2026, 11, 1), date(2027, 2, 28), date(2026, 10, 8), "Partial: statistics only (#1)"),
        ("Deletion minimisation", "M2", date(2026, 12, 1), date(2027, 2, 28), date(2026, 10, 10), "Done early (#35)"),
    ]),
    ("Iteration 3  (Feb - Apr)", [
        ("Failure signatures, repeated-run verification", "M2", date(2027, 1, 1), date(2027, 3, 31), date(2026, 10, 9), "Done early (#10, #11)"),
        ("Controlled fixtures, reproducibility bundle", "M3", date(2027, 1, 1), date(2027, 4, 30), date(2026, 10, 8), "Fixtures done early (#1, #45)"),
        ("Certificate evidence path and coverage", "M1", date(2027, 2, 1), date(2027, 4, 30), None, "Planned"),
        ("Repair verification (gated)", "M3", date(2027, 3, 1), date(2027, 4, 30), None, "Planned"),
        ("CLI / CI integration, container security", "M2", date(2027, 3, 1), date(2027, 5, 31), date(2026, 10, 10), "CLI and CI done early (#26)"),
        ("Non-perturbation, regression verification", "M3", date(2027, 4, 1), date(2027, 5, 31), None, "Planned"),
    ]),
    ("Iteration 4  (May - Jun)", [
        ("End-to-end integration, user acceptance", "Joint", date(2027, 4, 1), date(2027, 5, 31), None, "Planned"),
        ("Final testing, deployment, report, handover", "Joint", date(2027, 5, 1), date(2027, 6, 30), None, "Planned"),
    ]),
]

# Actual phases as stated by the team, and dated events in the repository.
PHASES = [
    ("Proposal and proof of concept", date(2026, 8, 1), date(2026, 9, 11)),
    ("Post-defence development", date(2026, 9, 15), date(2026, 10, 8)),
]
EVENTS = [  # (date, label) on the phase rows: dated files / git, defence date stated by the team
    (date(2026, 8, 25), "POC runs"),
    (date(2026, 9, 4), "Rev. 2"),
    (date(2026, 9, 11), "defence"),
]
ITERATIONS = [
    ("Iteration 1", date(2026, 8, 1), date(2026, 10, 31)),
    ("Iteration 2", date(2026, 11, 1), date(2027, 1, 31)),
    ("Iteration 3", date(2027, 2, 1), date(2027, 4, 30)),
    ("Iteration 4", date(2027, 5, 1), date(2027, 6, 30)),
]
X0, X1 = date(2026, 8, 1), date(2027, 6, 30)


def build():
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 7, "axes.edgecolor": GRID})
    rows = [("header", "Actual work (phases as stated by the team)")]
    rows += [("phase", phase) for phase in PHASES]
    for title, tasks in SECTIONS:
        rows.append(("header", f"Proposal plan: {title}"))
        rows += [("task", t) for t in tasks]

    n = len(rows)
    height = 0.25 * n + 1.25
    fig = plt.figure(figsize=(7.4, height), dpi=300, facecolor=SURFACE)
    # Three fixed columns in figure coordinates: names | plot | status.
    LABEL_X, PLOT_L, PLOT_R, STATUS_X = 0.01, 0.37, 0.70, 0.715
    top, bottom = 1 - 0.45 / height, 0.78 / height
    ax = fig.add_axes([PLOT_L, bottom, PLOT_R - PLOT_L, top - bottom], facecolor=SURFACE)
    ax.set_ylim(n - 0.5, -0.5)
    ax.set_xlim(mdates.date2num(X0), mdates.date2num(X1))

    def row_y(y):  # data row -> figure y
        return fig.transFigure.inverted().transform(ax.transData.transform((0, y)))[1]

    for i, (name, a, b) in enumerate(ITERATIONS):
        if i % 2 == 0:
            ax.axvspan(mdates.date2num(a), mdates.date2num(b), color="#f1f0eb", zorder=0, lw=0)
        ax.text((mdates.date2num(a) + mdates.date2num(b)) / 2, -0.62, name.replace("Iteration", "Iter."),
                ha="center", va="bottom", color=INK2, fontsize=6.5, fontweight="bold")
    fig.text(STATUS_X, row_y(-0.62), "Status", ha="left", va="bottom", color=INK2, fontsize=6.5,
             fontweight="bold")

    for y, (kind, payload) in enumerate(rows):
        fy = row_y(y)
        if kind == "header":
            fig.text(LABEL_X, fy, payload, ha="left", va="center", fontweight="bold", color=INK)
            ax.axhline(y + 0.5, color=GRID, lw=0.6, zorder=1)
            continue
        if kind == "phase":
            label, a, b = payload
            ax.add_patch(Rectangle((mdates.date2num(a), y - 0.22), mdates.date2num(b) - mdates.date2num(a),
                                   0.44, facecolor="#d9d8d2", edgecolor=MUTED, hatch="////", lw=0.5, zorder=2))
            fig.text(LABEL_X + 0.012, fy, label, ha="left", va="center", color=INK)
            # The event on the phase's last day names the end; the others are listed below it.
            end = next((text for d, text in EVENTS if d == b), None)
            events = [f"{text} {d.day} {d:%b}" for d, text in EVENTS if a <= d < b]
            for d, _ in EVENTS:
                if a <= d <= b:
                    ax.plot(mdates.date2num(d), y, marker="D", ms=4, color=INK, zorder=4,
                            markeredgecolor=SURFACE, markeredgewidth=0.6)
            status = (f"{a.day} {a:%b} - {b.day} {b:%b}" + (f" ({end})" if end else "")
                      + ("\n" + ", ".join(events) if events else ""))
            fig.text(STATUS_X, fy, status, ha="left", va="center", color=INK2, linespacing=1.15)
            continue
        task, owner, a, b, actual, status = payload
        ax.add_patch(Rectangle((mdates.date2num(a), y - 0.2), mdates.date2num(b) - mdates.date2num(a), 0.4,
                               facecolor=OWNER[owner], edgecolor=SURFACE, lw=0.8, zorder=2))
        fig.text(LABEL_X + 0.012, fy, f"{task} ({owner})", ha="left", va="center", color=INK)
        if actual:
            ax.plot(mdates.date2num(actual), y, marker="D", ms=4.5, color=INK, zorder=4,
                    markeredgecolor=SURFACE, markeredgewidth=0.7)
        fig.text(STATUS_X, fy, status, ha="left", va="center", color=INK2)

    ax.axvline(mdates.date2num(AS_OF), color=INK, lw=0.8, zorder=3)
    ax.axvline(mdates.date2num(date(2026, 10, 16)), color=INK, lw=0.8, ls=":", zorder=3)

    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.set_xticklabels([])
    ticks = [mdates.num2date(t) for t in ax.get_xticks()]
    ax.set_xticks([mdates.date2num(t) for t in ticks])
    ax.set_xticklabels([f"{t:%b}" + (f"\n{t:%Y}" if t.month in (1, 8) else "") for t in ticks],
                       color=INK2, fontsize=6)
    ax.tick_params(axis="x", length=0, pad=3)
    ax.set_yticks([])
    ax.grid(axis="x", color=GRID, lw=0.5, zorder=1)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)

    legend = [Patch(facecolor=OWNER[k], edgecolor="none", label=f"Plan: {k}") for k in OWNER]
    legend += [
        Line2D([], [], marker="D", ls="none", color=INK, ms=4.5, label="Actual (merge or dated file)"),
        Patch(facecolor="#d9d8d2", edgecolor=MUTED, hatch="////", label="Phase stated by the team"),
        Line2D([], [], color=INK, lw=0.8, label=f"Status date {AS_OF:%d %b}"),
        Line2D([], [], color=INK, lw=0.8, ls=":", label="Mid meeting 16 Oct"),
    ]
    fig.legend(handles=legend, loc="lower center", ncol=4, frameon=False, fontsize=6.3,
               bbox_to_anchor=(0.5, 0.0), handlelength=1.5, columnspacing=1.2)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, facecolor=SURFACE)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    build()
