# casom_defense.py
# Context-Aware Sensor Obfuscation Middleware (CASOM) -- improved version.
#
# Why this exists:
#   The original defender added INDEPENDENT zero-mean noise to every 72 Hz
#   sample. Because each keypress dwell contains ~15-35 samples, an attacker
#   who segments by dwell and takes the cluster centroid averages that noise
#   straight back to zero and recovers the key. Independent per-sample noise
#   is therefore the wrong granularity for this threat model.
#
#   This module keeps the original mode for comparison but adds defenses that
#   are designed to survive an averaging (adaptive) adversary.

import math
import random


class CASOM:
    """Context-Aware Sensor Obfuscation Middleware.

    Modes
    -----
    "iid"          : Original baseline. Independent Laplace noise per sample.
                     Defeated by an averaging attacker (kept for comparison).
    "correlated"   : A slowly drifting bias (Ornstein-Uhlenbeck random walk)
                     added on top of small per-sample jitter. The bias is
                     near-constant within a dwell window, so averaging does NOT
                     cancel it -- this is the defense that actually holds up.
    "per_keypress" : One fixed Laplace offset per dwell segment. Models
                     perturbing the *derived* per-key estimate rather than the
                     raw stream. Requires segment boundaries (provided by the
                     OS typing detector in a real deployment).
    "downsample"   : Rate-limit + quantize the stream given to background apps.
                     Attacks the segmentation step the attack depends on.
    "block"        : RECOMMENDED, deployable. A fresh Laplace offset every
                     `block_samples` samples (~one dwell), held constant within
                     the block. Like per_keypress but needs NO exact keypress
                     boundaries -- just a fixed cadence. Independent per-block
                     displacement destroys the relative geometry BackTree relies
                     on, and being block-constant it is not averaged away.

    Note on what does NOT work: a slowly drifting bias preserves the *vectors*
    between consecutive keypresses, and BackTree ranks words by exactly those
    relative vectors -- so drift-style noise leaves the attack largely intact.
    Effective defenses must displace each key INDEPENDENTLY.

    The foreground keyboard always receives the clean stream; only the
    background (potential attacker) stream is obfuscated.
    """

    def __init__(self, mode="block", noise_scale=1.5,
                 ou_theta=0.02, ou_sigma=0.25, jitter=0.05,
                 downsample_factor=8, quantize=0.5,
                 block_samples=15, seed=None):
        self.mode = mode
        self.noise_scale = noise_scale      # Laplace scale b
        self.ou_theta = ou_theta            # mean-reversion of the drift
        self.ou_sigma = ou_sigma            # step size of the drift
        self.jitter = jitter                # small per-sample jitter (correlated)
        self.downsample_factor = downsample_factor
        self.quantize = quantize
        self.block_samples = block_samples  # block length for "block" mode
        self._rng = random.Random(seed)

    # ---- noise primitives -------------------------------------------------
    def _laplace(self, b):
        # Inverse-CDF sampling of a zero-mean Laplace(0, b) variable.
        u = self._rng.random() - 0.5
        return -b * math.copysign(1, u) * math.log(1 - 2 * abs(u))

    # ---- public API -------------------------------------------------------
    def obfuscate(self, gaze_points, segments=None):
        """Return the obfuscated stream a background app would observe.

        gaze_points : list[(x, y)] raw samples.
        segments    : optional list[(start_idx, end_idx)] dwell boundaries,
                      required only for "per_keypress".
        """
        if self.mode == "iid":
            return self._iid(gaze_points)
        if self.mode == "correlated":
            return self._correlated(gaze_points)
        if self.mode == "per_keypress":
            return self._per_keypress(gaze_points, segments)
        if self.mode == "block":
            return self._block(gaze_points)
        if self.mode == "downsample":
            return self._downsample(gaze_points)
        raise ValueError(f"unknown mode: {self.mode}")

    # ---- mode implementations --------------------------------------------
    def _iid(self, pts):
        return [(x + self._laplace(self.noise_scale),
                 y + self._laplace(self.noise_scale)) for (x, y) in pts]

    def _correlated(self, pts):
        # Drift evolves as an OU process: bias_{t+1} = (1-theta)*bias_t + step.
        # It changes slowly relative to a dwell, so averaging cannot remove it.
        out = []
        bx = self._laplace(self.noise_scale)
        by = self._laplace(self.noise_scale)
        for (x, y) in pts:
            bx = (1 - self.ou_theta) * bx + self._rng.gauss(0, self.ou_sigma)
            by = (1 - self.ou_theta) * by + self._rng.gauss(0, self.ou_sigma)
            jx = self._rng.gauss(0, self.jitter)
            jy = self._rng.gauss(0, self.jitter)
            out.append((x + bx + jx, y + by + jy))
        return out

    def _per_keypress(self, pts, segments):
        if segments is None:
            # Fall back to treating the whole stream as one segment.
            segments = [(0, len(pts))]
        out = list(pts)
        for (s, e) in segments:
            ox = self._laplace(self.noise_scale)
            oy = self._laplace(self.noise_scale)
            for i in range(s, e):
                x, y = pts[i]
                out[i] = (x + ox, y + oy)
        return out

    def _block(self, pts):
        out = []
        ox = oy = 0.0
        for i, (x, y) in enumerate(pts):
            if i % self.block_samples == 0:
                ox = self._laplace(self.noise_scale)
                oy = self._laplace(self.noise_scale)
            out.append((x + ox, y + oy))
        return out

    def _downsample(self, pts):
        kept = pts[::self.downsample_factor]
        q = self.quantize
        return [(round(x / q) * q, round(y / q) * q) for (x, y) in kept]


# Backwards-compatible shim so the original main.py keeps working.
class CASOMMiddleware:
    def __init__(self, noise_scale=1.5, use_rounding=False):
        mode = "downsample" if use_rounding else "iid"
        self._impl = CASOM(mode=mode, noise_scale=noise_scale)

    def obfuscate_data(self, gaze_points):
        return self._impl.obfuscate(gaze_points)
