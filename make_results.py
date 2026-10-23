"""
make_results.py - turns results.pkl into the paper's tables and figures.

    python make_results.py
Outputs: tables.md (readable), tables.tex (paste into the paper),
         fig_timeseries_s2.png, fig_rolling.png
"""
import pickle, numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from method import simulate, METHODS

R = pickle.load(open('results.pkl', 'rb'))
NAMES = {'KF': 'Kalman ellipse', 'SURVEY': 'One-time survey', 'ORACLE': 'Oracle (true feedback)',
         'INTERM': 'Oracle, 10% feedback', 'N': 'Ours', 'U': 'Ours-U (plain)',
         'G': 'Ours-G (geometry)', 'U_aci': 'Ours-U + ACI', 'N_aci': 'Ours + ACI'}
MAIN = ['KF', 'SURVEY', 'INTERM', 'ORACLE', 'N']
ABL = ['U', 'N', 'G', 'U_aci', 'N_aci']
SCEN = {'S1': 'Normal room', 'S2': 'Walls appear', 'S3': 'Signals worsen', 'S4': 'Anchor breaks'}

def runs(sc, pr=4):
    return [v for (s, p, _), v in R.items() if s == sc and p == pr]

def stat(rs, m, key, part):
    vals = np.array([r[m][key][part] for r in rs], float)
    return vals.mean(), vals.std()

def part_of(sc):
    return 2 if sc == 'S1' else 1          # S1: whole run; others: after the change

md, tex = [], []
# ---------------- Table I: main comparison ----------------
md.append('## Table I - coverage % (mean ± std over runs) / mean radius m.  Target 90%.\n')
md.append('S1 = whole run; S2-S4 = second half (after the change).\n')
md.append('| Method | ' + ' | '.join(SCEN.values()) + ' |')
md.append('|---|' + '---|' * len(SCEN))
tex.append('% Table I\n\\begin{tabular}{l' + 'c' * len(SCEN) + '}\\toprule')
tex.append('Method & ' + ' & '.join(SCEN.values()) + ' \\\\ \\midrule')
for m in MAIN:
    cells, tcells = [], []
    for sc in SCEN:
        rs = runs(sc); p = part_of(sc)
        c, cs = stat(rs, m, 'cov', p); r, _ = stat(rs, m, 'rad', p)
        cells.append(f'{100*c:.1f} ± {100*cs:.1f} / {r:.1f}')
        tcells.append(f'{100*c:.1f}\\,/\\,{r:.1f}')
    md.append(f'| {NAMES[m]} | ' + ' | '.join(cells) + ' |')
    tex.append(f'{NAMES[m]} & ' + ' & '.join(tcells) + ' \\\\')
tex.append('\\bottomrule\\end{tabular}\n')
n_runs = len(runs('S1'))

# ---------------- Table II: ablation ----------------
md.append(f'\n## Table II - variants of our method (coverage % / radius m), {n_runs} runs\n')
md.append('| Variant | ' + ' | '.join(SCEN.values()) + ' |')
md.append('|---|' + '---|' * len(SCEN))
tex.append('% Table II\n\\begin{tabular}{l' + 'c' * len(SCEN) + '}\\toprule')
tex.append('Variant & ' + ' & '.join(SCEN.values()) + ' \\\\ \\midrule')
for m in ABL:
    cells = []
    for sc in SCEN:
        rs = runs(sc); p = part_of(sc)
        c, _ = stat(rs, m, 'cov', p); r, _ = stat(rs, m, 'rad', p)
        cells.append(f'{100*c:.1f}\\,/\\,{r:.1f}')
    md.append(f'| {NAMES[m]} | ' + ' | '.join(c.replace("\\,", " ") for c in cells) + ' |')
    tex.append(f'{NAMES[m]} & ' + ' & '.join(cells) + ' \\\\')
tex.append('\\bottomrule\\end{tabular}\n')

# ---------------- Table III: anchor density ----------------
md.append('\n## Table III - anchor density (coverage % / radius m)\n')
md.append('| Anchors | Method | Normal room | Walls appear |')
md.append('|---|---|---|---|')
tex.append('% Table III\n\\begin{tabular}{llcc}\\toprule\nAnchors & Method & Normal room & Walls appear \\\\ \\midrule')
for pr in [3, 4, 5]:
    for m in ['SURVEY', 'ORACLE', 'N']:
        c1, _ = stat(runs('S1', pr), m, 'cov', 2); r1, _ = stat(runs('S1', pr), m, 'rad', 2)
        c2, _ = stat(runs('S2', pr), m, 'cov', 1); r2, _ = stat(runs('S2', pr), m, 'rad', 1)
        md.append(f'| {pr*pr} | {NAMES[m]} | {100*c1:.1f} / {r1:.1f} | {100*c2:.1f} / {r2:.1f} |')
        tex.append(f'{pr*pr} & {NAMES[m]} & {100*c1:.1f}\\,/\\,{r1:.1f} & {100*c2:.1f}\\,/\\,{r2:.1f} \\\\')
tex.append('\\bottomrule\\end{tabular}\n')

# ---------------- Recovery and fault detection ----------------
md.append('\n## Recovery after the change (steps until 30-step rolling coverage >= 88%)\n')
for sc in ['S2', 'S3']:
    row = []
    for m in MAIN:
        rec = [r[m]['recovery'] for r in runs(sc)]
        ok = [x for x in rec if x is not None]
        row.append(f'{NAMES[m]}: ' + (f'median {np.median(ok):.0f} ({len(ok)}/{len(rec)} recover)' if ok else f'never (0/{len(rec)})'))
    md.append(f'- **{SCEN[sc]}**: ' + '; '.join(row))
s4 = runs('S4')
delays = [r['detect_delay'] for r in s4]
det = [d for d in delays if d is not None]
fa = sum(r['false_alarm'] for sc in ['S1', 'S2', 'S3'] for r in runs(sc)) + sum(r['false_alarm'] for r in s4)
wrong = sum(r['wrong_anchor_flagged'] for r in s4)
md.append(f'\n## Broken-anchor detection\n- detected in {len(det)}/{len(s4)} runs; delay median {np.median(det):.0f} steps, max {max(det)}')
md.append(f'- false alarms (any anchor flagged without a fault): {fa} of {4*len(s4)} runs; wrong anchor flagged in S4: {wrong}')
md.append(f'\nRuns per configuration: {n_runs}')

open('tables.md', 'w').write('\n'.join(md))
open('tables.tex', 'w').write('\n'.join(tex))
print('\n'.join(md))

# ---------------- Figures ----------------
INK, MUTED, GRID = '#0b0b0b', '#52514e', '#e4e3df'
BLUE, ORANGE, AQUA = '#2a78d6', '#eb6834', '#1baf7a'
plt.rcParams.update({'font.size': 9, 'axes.edgecolor': MUTED, 'axes.labelcolor': INK,
                     'xtick.color': MUTED, 'ytick.color': MUTED, 'axes.grid': True,
                     'grid.color': GRID, 'grid.linewidth': 0.6, 'axes.spines.top': False,
                     'axes.spines.right': False})

# Fig: one run of S2, radius vs real error
s = simulate('S2', seed=1, keep_series=True)
T, h = s['T'], s['T'] // 2
t = np.arange(T)
fig, ax = plt.subplots(figsize=(7.2, 2.9))
ax.plot(t, s['err_z'], color=MUTED, lw=0.7, label='Real error')
ax.plot(t, s['rad']['SURVEY'], color=ORANGE, lw=2, label='One-time survey')
ax.plot(t, s['rad']['ORACLE'], color=INK, lw=1.2, ls='--', label='Oracle (true feedback)')
ax.plot(t, s['rad']['N'], color=BLUE, lw=2, label='Ours')
ax.axvline(h, color=MUTED, ls=':', lw=1)
ax.text(h + 6, 2, 'walls appear', color=MUTED, fontsize=8)
ax.set_xlabel('time step (s)'); ax.set_ylabel('metres'); ax.set_ylim(0, 40)
ax.legend(loc='upper left', fontsize=7.5, frameon=False, ncol=2)
plt.tight_layout(); plt.savefig('fig_timeseries_s2.png', dpi=200); plt.close()

# Fig: rolling coverage averaged over runs, S2 and S3 side by side
W_ROLL = 30
def rolling(ins, w=W_ROLL):
    return np.convolve(ins.astype(float), np.ones(w) / w, mode='valid')
fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.7), sharey=True)
for ax, sc in zip(axes, ['S2', 'S3']):
    series = [simulate(sc, seed=k, keep_series=True) for k in range(20)]
    T = series[0]['T']
    ends = []
    for m, col, ls, lw in [('KF', AQUA, '-', 1.6), ('SURVEY', ORANGE, '-', 1.6),
                           ('ORACLE', INK, '--', 1.0), ('N', BLUE, '-', 2.0)]:
        y = 100 * np.mean([rolling(x['inside'][m]) for x in series], axis=0)
        t = np.arange(len(y)) + W_ROLL - 1          # value at t = coverage of the last 30 steps
        ax.plot(t, y, color=col, ls=ls, lw=lw, label=NAMES[m])
        ends.append([y[-1], NAMES[m].split(' (')[0].split(',')[0]])
    ends.sort()
    for i in range(1, len(ends)):                    # keep end labels from overlapping
        ends[i][0] = max(ends[i][0], ends[i - 1][0] + 7)
    for yv, lab in ends:
        ax.text(T + 4, yv, lab, color=INK, fontsize=6.5, va='center')
    ax.axhline(90, color=MUTED, lw=0.8, ls=':')
    ax.axvline(T // 2 if sc == 'S2' else 0, color=MUTED, lw=0.8, ls=':')
    ax.set_title(SCEN[sc], fontsize=9, color=INK); ax.set_xlabel('time step (s)')
    ax.set_xlim(0, T + 80); ax.set_ylim(0, 102)
axes[0].set_ylabel('rolling coverage (%)')
axes[0].legend(loc='lower left', fontsize=6.5, frameon=False)
plt.tight_layout(); plt.savefig('fig_rolling.png', dpi=200); plt.close()
print('\nfigures saved')
