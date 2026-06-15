# adaptive_attacker.py
# A stronger SnoopFinger-style attacker for evaluating defenses.
#
# Two capabilities the original toy attacker lacked:
#   1. Dwell-aware segmentation. A real attacker recovers per-keypress segments
#      from the motion (slowdown/pause), then averages WITHIN each segment.
#      Averaging cancels independent per-sample noise -- so any honest defense
#      evaluation must be run against this attacker, not only the naive one.
#   2. Ranked candidates per keypress, so we can report Top-1 / Top-3 character
#      accuracy in the spirit of the paper's Top-k metric.

import math
from keyboard import KEYBOARD_LAYOUT


def _dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


class NaiveAttacker:
    """The original approach: threshold-cluster the stream, then centroid.

    Sensitive to noise because noise breaks the distance-threshold clustering,
    not because the spatial information is gone.
    """

    def __init__(self, cluster_threshold=0.8):
        self.cluster_threshold = cluster_threshold

    def _clusters(self, pts):
        if not pts:
            return []
        clusters, cur = [], [pts[0]]
        for p in pts[1:]:
            if _dist(p, cur[-1]) < self.cluster_threshold:
                cur.append(p)
            else:
                clusters.append(cur)
                cur = [p]
        clusters.append(cur)
        return [c for c in clusters if len(c) >= 2]

    def ranked_per_key(self, pts, segments=None):
        out = []
        for c in self._clusters(pts):
            cx = sum(p[0] for p in c) / len(c)
            cy = sum(p[1] for p in c) / len(c)
            out.append(_rank_keys(cx, cy))
        return out


class AdaptiveAttacker:
    """Uses dwell segment boundaries to average within each keypress.

    In a real deployment the boundaries come from the attacker's own
    keypress-moment detector. Passing the true boundaries here makes this an
    upper-bound (best-case) adversary -- exactly what a defense should be
    stress-tested against.
    """

    def ranked_per_key(self, pts, segments):
        out = []
        for (s, e) in segments:
            seg = pts[s:e]
            if not seg:
                continue
            cx = sum(p[0] for p in seg) / len(seg)
            cy = sum(p[1] for p in seg) / len(seg)
            out.append(_rank_keys(cx, cy))
        return out


def _rank_keys(x, y):
    """Return key labels sorted by distance to (x, y) -- nearest first."""
    return [k for k, _ in sorted(KEYBOARD_LAYOUT.items(),
                                 key=lambda kv: _dist((x, y), kv[1]))]


def char_topk_accuracy(ranked_per_key, true_chars, k=1):
    """Fraction of keypresses whose true char is within the top-k candidates."""
    hits = total = 0
    for cands, true in zip(ranked_per_key, true_chars):
        total += 1
        if true in cands[:k]:
            hits += 1
    return hits / total if total else 0.0
