"""
method.py - our method (paper Section IV) and every method we compare against (Section V-C).

simulate() walks the target along its path once and records, at every time step, the
circle radius each method would draw and whether the true target fell inside it.

Methods (all promise 90% coverage):
  KF      Kalman-filter ellipse (B1)                     - uses its own noise model
  SURVEY  one-time survey, offline conformal (B2)        - 100 hand-measured points before start
  ORACLE  online conformal fed the TRUE target error (B3) - impossible in practice, upper bound
  INTERM  same, but truth arrives only 10% of the time (B4)
  U       ours, plain:      90th percentile of recent anchor self-test errors
  N       ours, normalized: errors scaled by each case's 'fit' clue (readings disagreement)
  G       ours, geometry:   errors scaled by each case's textbook geometric difficulty
  U_aci, N_aci  ours + online correction fed ONLY by anchors
"""
import numpy as np
from sim import grid_anchors, repo_path, RadioWorld, localize_batch, localize, Kalman

SIDE = 50.0
CHI2_90 = 4.605
OURS = ['U', 'N', 'G']
METHODS = ['KF', 'SURVEY', 'ORACLE', 'INTERM'] + OURS + ['U_aci', 'N_aci']


def cq(x, level):
    """Conformal quantile with the small-sample correction ceil((n+1)level)/n."""
    n = len(x)
    return np.quantile(x, min(1.0, np.ceil((n + 1) * level) / n)) if n else np.inf


class Detector:
    """Broken-anchor detector: a receiver that is off on (almost) all its links,
    differently from the other anchors, for `persist` consecutive steps."""
    def __init__(self, anchors, z_thr=3.5, persist=5):
        D = np.linalg.norm(anchors[:, None] - anchors[None], axis=2)
        np.fill_diagonal(D, 1.0)
        self.expected = -40.0 - 27.0 * np.log10(D)
        self.z_thr, self.persist = z_thr, persist
        self.count = np.zeros(len(anchors), int)
        self.flagged = np.zeros(len(anchors), bool)

    def update(self, M, active):
        resid = M - self.expected
        med = np.array([np.nanmedian(resid[j, active]) for j in range(len(M))])
        center = np.median(med[active])
        mad = 1.4826 * np.median(np.abs(med[active] - center)) + 1e-6
        z = (med - center) / mad
        self.count = np.where(np.abs(z) > self.z_thr, self.count + 1, 0)
        self.flagged |= self.count >= self.persist
        return self.flagged.copy()


def self_test(M, A, active):
    """Leave-one-anchor-out: locate every active anchor from the other active anchors."""
    act = np.asarray(active)
    m = len(act)
    others = np.array([[j for j in act if j != k] for k in act])          # (m, m-1)
    rssi = M[others, act[:, None]]                                        # what others hear from k
    est, info = localize_batch(rssi, A[others])
    return np.linalg.norm(est - A[act], axis=1), info


def scenario_events(world, scenario, t, T):
    if scenario == 'S2' and t == T // 2:          # walls appear: floor split into 4 rooms
        world.walls = [((SIDE / 2, 0), (SIDE / 2, SIDE)), ((0, SIDE / 2), (SIDE, SIDE / 2))]
    if scenario == 'S3':                          # signals fade faster and faster
        world.n = 2.7 + 1.0 * t / T
    if scenario == 'S4' and t == T // 2:          # anchor 5 breaks
        world.faulty = {5: 12.0}


def simulate(scenario, seed=0, per_row=4, alpha=0.1, W=15, gamma=0.02,
             oracle_window=100, p_feedback=0.1, keep_series=False, path_name='tra3'):
    rng = np.random.default_rng(seed)
    A = grid_anchors(SIDE, per_row)
    path = repo_path(SIDE, path_name)
    T = len(path)
    world = RadioWorld(A, rng=rng)
    det = Detector(A)

    # ---- baselines' one-time survey (clean conditions, before tracking starts) ----
    survey = rng.uniform(0, SIDE, (100, 2))
    sr = np.array([world.target_rssi(p) for p in survey])
    sx, _ = localize_batch(sr, np.broadcast_to(A, (100,) + A.shape))
    surv_err = sx - survey
    r_survey = cq(np.linalg.norm(surv_err, axis=1), 1 - alpha)
    kf = Kalman(path[0], np.cov(surv_err.T))

    pool_s, pool_phi = [], []
    lvl = {'U_aci': alpha, 'N_aci': alpha, 'ORACLE': alpha, 'INTERM': alpha}
    true_hist, interm_hist = [], []
    rad = {m: np.zeros(T) for m in METHODS}
    inside = {m: np.zeros(T, bool) for m in METHODS}
    err_z, err_x, flags_t = np.zeros(T), np.zeros(T), []

    for t, x in enumerate(path):
        scenario_events(world, scenario, t, T)

        # ---- anchor self-test ----
        M = world.anchor_rssi()
        flags = det.update(M, np.where(~det.flagged)[0])
        active = np.where(~flags)[0]
        s_t, phi_t = self_test(M, A, active)
        pool_s.append(s_t); pool_phi.append(phi_t)
        S = np.concatenate(pool_s[-W:]); PHI = np.vstack(pool_phi[-W:])

        # ---- target ----
        z, phi = localize(world.target_rssi(x)[active], A[active])
        xf, Pf = kf.step(z)
        e = np.linalg.norm(z - x)
        err_z[t], err_x[t] = e, np.linalg.norm(xf - x)
        flags_t.append(flags)

        # ---- our circles ----
        c = 1.0
        def radius(v, level, q=phi):
            if v == 'U':
                return cq(S, level)
            if v == 'N':
                return cq(S / (PHI[:, 0] + c), level) * (q[0] + c)
            return cq(S / PHI[:, 2], level) * q[2]                      # 'G'
        for v in OURS:
            rad[v][t] = radius(v, 1 - alpha)
        for v, base in [('U_aci', 'U'), ('N_aci', 'N')]:
            L = float(np.clip(1 - lvl[v], 0.5, 0.999))
            rad[v][t] = radius(base, L)
            miss = np.mean([s_t[i] > radius(base, L, phi_t[i]) for i in range(len(s_t))])
            lvl[v] += gamma * (alpha - miss)                           # fed by anchors only

        # ---- baselines ----
        d = xf - x
        rad['KF'][t] = np.sqrt(CHI2_90 * np.linalg.eigvalsh(Pf)[-1])
        inside['KF'][t] = d @ np.linalg.inv(Pf) @ d <= CHI2_90
        rad['SURVEY'][t] = r_survey
        for name, hist in [('ORACLE', true_hist), ('INTERM', interm_hist)]:
            L = float(np.clip(1 - lvl[name], 0.5, 0.999))
            rad[name][t] = cq(np.array(hist[-oracle_window:]), L) if len(hist) >= 10 else r_survey
        miss_true = float(e > rad['ORACLE'][t])
        lvl['ORACLE'] += gamma * (alpha - miss_true)
        true_hist.append(e)
        if rng.random() < p_feedback:                                  # truth arrives rarely
            lvl['INTERM'] += gamma * (alpha - float(e > rad['INTERM'][t])) / p_feedback
            interm_hist.append(e)

        for m in METHODS:
            if m != 'KF':
                inside[m][t] = e <= rad[m][t]

    flags_t = np.array(flags_t)
    res = {'T': T, 'err_z': err_z, 'err_x': err_x, 'flags': flags_t,
           'rad': rad, 'inside': inside}
    return res if keep_series else summarize(res, scenario)


def summarize(res, scenario, win=30, target=0.88):
    """Turn one run's time series into the numbers that go in the tables."""
    T, h = res['T'], res['T'] // 2
    out = {'mean_err_z': [res['err_z'][:h].mean(), res['err_z'][h:].mean()],
           'mean_err_x': [res['err_x'][:h].mean(), res['err_x'][h:].mean()]}
    for m in METHODS:
        ins, r = res['inside'][m], res['rad'][m]
        roll = np.convolve(ins.astype(float), np.ones(win) / win, mode='valid')
        after = roll[h:]
        rec = int(np.argmax(after >= target)) if (after >= target).any() else None
        out[m] = {'cov': [ins[:h].mean(), ins[h:].mean(), ins.mean()],
                  'rad': [r[:h].mean(), r[h:].mean(), r.mean()],
                  'recovery': rec}
    F = res['flags']
    out['false_alarm'] = bool(F[:h].any()) or (scenario != 'S4' and bool(F.any()))
    if scenario == 'S4':
        hit = np.where(F[h:, 5])[0]
        out['detect_delay'] = int(hit[0]) if len(hit) else None
        out['wrong_anchor_flagged'] = bool(np.delete(F, 5, axis=1).any())
    return out
