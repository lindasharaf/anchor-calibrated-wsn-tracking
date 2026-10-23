"""
sim.py - the simulated world for our project (paper Section III).

  * an indoor floor with anchors on a grid
  * a realistic radio model (log-distance path loss + random shadowing)
  * walls that weaken signals passing through them (NLOS), which can switch on
  * slow environmental drift (signals fading faster over time)
  * a broken anchor whose readings go wrong from some moment on
  * a localizer (signal strengths -> position) and a Kalman tracker

Everything is vectorized (computed for many links / many anchors at once) so that
hundreds of simulation runs finish in minutes. Nothing here knows about our method.
"""
import numpy as np

P0_NOM, N_NOM, SIGMA_NOM = -40.0, 2.7, 4.0     # the system's NOMINAL radio model


# ----------------------------------------------------------------------------
# 1. The floor, the anchors, the path
# ----------------------------------------------------------------------------
def grid_anchors(side=50.0, per_row=4, margin=3.0):
    """Anchors on an evenly spaced grid, `margin` meters in from the walls."""
    xs = np.linspace(margin, side - margin, per_row)
    return np.array([(x, y) for x in xs for y in xs])


def repo_path(side=50.0, name='tra3'):
    """One of the baseline repo's trajectories (tra2 or tra3), scaled from its 200 m area to our floor."""
    tra = np.load(name + '.npy')
    return np.clip(tra * side / 200.0, 0.5, side - 0.5)


# ----------------------------------------------------------------------------
# 2. The radio world
# ----------------------------------------------------------------------------
def _cross_count(P, Q, walls):
    """How many walls each segment P[i]-Q[i] crosses.  P, Q: (N, 2)."""
    count = np.zeros(len(P))
    def orient(u, v, w):
        return (v[..., 0] - u[..., 0]) * (w[..., 1] - u[..., 1]) - (v[..., 1] - u[..., 1]) * (w[..., 0] - u[..., 0])
    for a, b in walls:
        a = np.broadcast_to(np.asarray(a, float), P.shape)
        b = np.broadcast_to(np.asarray(b, float), P.shape)
        c1 = orient(P, Q, a) * orient(P, Q, b) < 0
        c2 = orient(a, b, P) * orient(a, b, Q) < 0
        count += c1 & c2
    return count


class RadioWorld:
    """
    Signal strength (dBm) heard by a receiver from a transmitter:
        P = P0 - 10 n log10(d) + shadowing - wall_loss * (#walls crossed) + (receiver fault bias)
    """
    def __init__(self, anchors, P0=P0_NOM, n=N_NOM, sigma=SIGMA_NOM, wall_loss=8.0, rng=None):
        self.anchors = anchors
        self.P0, self.n, self.sigma, self.wall_loss = P0, n, sigma, wall_loss
        self.rng = rng if rng is not None else np.random.default_rng()
        self.walls = []          # list of ((x1,y1),(x2,y2)) segments that are currently "closed"
        self.faulty = {}         # receiver anchor index -> dB bias

    def _links(self, tx, rx, rx_idx):
        d = np.maximum(np.linalg.norm(tx - rx, axis=1), 0.5)
        p = self.P0 - 10 * self.n * np.log10(d) + self.rng.normal(0, self.sigma, len(d))
        if self.walls:
            p -= self.wall_loss * _cross_count(tx, rx, self.walls)
        for k, bias in self.faulty.items():
            p[rx_idx == k] += bias
        return p

    def target_rssi(self, x):
        """What each anchor hears from the target at x  -> (K,)."""
        K = len(self.anchors)
        return self._links(np.tile(x, (K, 1)), self.anchors, np.arange(K))

    def anchor_rssi(self):
        """(K, K) matrix: [j, k] = what anchor j hears from anchor k (diagonal = nan)."""
        K = len(self.anchors)
        J, Kk = np.meshgrid(np.arange(K), np.arange(K), indexing='ij')
        J, Kk = J.ravel(), Kk.ravel()
        M = self._links(self.anchors[Kk], self.anchors[J], J).reshape(K, K)
        np.fill_diagonal(M, np.nan)
        return M


# ----------------------------------------------------------------------------
# 3. The localizer: signal strengths -> position (weighted Gauss-Newton least squares)
# ----------------------------------------------------------------------------
def localize_batch(rssi, anchors, side=50.0, iters=25):
    """
    Localize B cases at once.
      rssi:    (B, m) readings,   anchors: (B, m, 2) positions of the anchors that heard them
    Uses the NOMINAL radio model only (it does not know about walls, drift or faults).
    Returns positions (B, 2) and three 'how hard was this case' clues (B, 3), all computable
    without ground truth, for the target and for anchors alike:
      fit  - how much the readings disagree with each other (m)
      edge - distance from the estimate to the nearest outer wall (m)
      geom - textbook difficulty of the spot from anchor geometry (Cramer-Rao style, m)
    """
    d_est = 10 ** ((P0_NOM - rssi) / (10 * N_NOM))               # loudness -> distance
    w = 1.0 / d_est                                              # trust near anchors more
    x = (w[..., None] * anchors).sum(1) / w.sum(1, keepdims=True)  # weighted centre start
    for _ in range(iters):
        diff = x[:, None, :] - anchors                           # (B, m, 2)
        dist = np.maximum(np.linalg.norm(diff, axis=2), 1e-3)
        J = diff / dist[..., None]                               # d(dist)/d(x)
        r = dist - d_est
        JtW = J * w[..., None]
        H = np.einsum('bmi,bmj->bij', JtW, J) + 1e-6 * np.eye(2)
        g = np.einsum('bmi,bm->bi', JtW, r)
        x = np.clip(x - np.linalg.solve(H, g[..., None])[..., 0], 0.0, side)
    diff = x[:, None, :] - anchors
    dist = np.maximum(np.linalg.norm(diff, axis=2), 0.5)
    fit = np.sqrt((w * (dist - d_est) ** 2).sum(1) / w.sum(1))
    edge = np.minimum(np.minimum(x[:, 0], side - x[:, 0]), np.minimum(x[:, 1], side - x[:, 1]))
    u = diff / dist[..., None]
    sd = dist * np.log(10) * SIGMA_NOM / (10 * N_NOM)
    F = np.einsum('bmi,bmj->bij', u / sd[..., None] ** 2, u) + 1e-9 * np.eye(2)
    geom = np.sqrt(np.trace(np.linalg.inv(F), axis1=1, axis2=2))
    return x, np.stack([fit, edge, geom], axis=1)


def localize(rssi, anchors, side=50.0):
    """Single case convenience wrapper."""
    x, info = localize_batch(rssi[None], anchors[None], side)
    return x[0], info[0]


# ----------------------------------------------------------------------------
# 4. The tracker: constant-velocity Kalman filter that keeps its uncertainty P
# ----------------------------------------------------------------------------
class Kalman:
    def __init__(self, x0, R, q=0.05, dt=1.0):
        self.A = np.array([[1, dt, 0, 0], [0, 1, 0, 0], [0, 0, 1, dt], [0, 0, 0, 1]])
        self.H = np.array([[1, 0, 0, 0], [0, 0, 1, 0]])
        G = np.array([[dt**2 / 2, 0], [dt, 0], [0, dt**2 / 2], [0, dt]])
        self.Q, self.R = q * G @ G.T, R
        self.x = np.array([x0[0], 0, x0[1], 0.0])
        self.P = 10 * np.eye(4)

    def step(self, z):
        self.x = self.A @ self.x
        self.P = self.A @ self.P @ self.A.T + self.Q
        S = self.H @ self.P @ self.H.T + self.R
        K = self.P @ self.H.T @ np.linalg.inv(S)
        self.x = self.x + K @ (z - self.H @ self.x)
        self.P = (np.eye(4) - K @ self.H) @ self.P
        return self.H @ self.x, self.H @ self.P @ self.H.T
