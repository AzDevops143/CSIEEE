# backtree.py
# Backward Key Inference Tree (BackTree) word inference -- a faithful
# reimplementation of the SnoopFinger attack core (paper Section 5.6).
#
# Input  : an ordered list of per-keypress 2D gaze points u_1..u_n where the
#          LAST point is the reference terminator (Enter or Space).
# Output : a dictionary-ranked list of candidate words (most likely first),
#          enabling Top-1 / Top-k% word accuracy exactly as the paper reports.
#
# Idea: even though absolute gaze positions drift between typing instances, the
# *relative* distance+angle between consecutive gaze points stays stable. The
# attack walks backward from the terminator, and at each step finds the keys in
# the adversary's reconstructed layout whose geometric relationship to the
# current reference best matches the measured relationship between the victim's
# consecutive gaze points. Candidates accumulate weights by how often they are
# inferred; words are scored by summed weight and filtered to a dictionary.

import math
from itertools import product
from keyboard import KEYBOARD_LAYOUT

LETTERS = [k for k in KEYBOARD_LAYOUT if len(k) == 1]


def _d(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _ang(frm, to):
    return math.degrees(math.atan2(to[1] - frm[1], to[0] - frm[0]))


def _ang_diff(a, b):
    """Smallest absolute difference between two angles in degrees (0..180)."""
    return abs((a - b + 180) % 360 - 180)


def _candidates_for(ref_key_pos, measured_d, measured_theta,
                    prev_gaze, n_angle=12, n_dist=8, n_distonly=8):
    """Return candidate KEYS for the next (earlier) gaze point.

    ref_key_pos   : position of the reference key in the adversary layout.
    measured_d/θ  : geometry measured between victim gaze points.
    prev_gaze     : the victim gaze point we are trying to identify (for the
                    supplementary distance-only selection).
    """
    scored = []
    for k in LETTERS:
        kp = KEYBOARD_LAYOUT[k]
        dc = _d(ref_key_pos, kp)
        tc = _ang(ref_key_pos, kp)
        scored.append((k, kp, dc, tc))

    # Primary: top-n by angle match, then top-n by distance match.
    by_angle = sorted(scored, key=lambda s: _ang_diff(s[3], measured_theta))[:n_angle]
    by_dist = sorted(by_angle, key=lambda s: abs(s[2] - measured_d))[:n_dist]
    chosen = {s[0] for s in by_dist}

    # Supplementary: distance-only match between the candidate keys and the
    # gaze point's own distance to the reference (adds robustness).
    by_distonly = sorted(scored, key=lambda s: abs(s[2] - measured_d))[:n_distonly]
    for s in by_distonly:
        chosen.add(s[0])

    return chosen


def infer_word_candidates(gaze_points, dictionary, prefixes,
                          max_per_depth=12, top_words=50):
    """Run BackTree and return up to `top_words` ranked dictionary words.

    gaze_points : u_1..u_n, last point = terminator (Enter/Space).
    dictionary  : set of valid words.
    prefixes    : set of valid word prefixes (for pruning the combination tree).
    """
    if len(gaze_points) < 2:
        return []

    n_letters = len(gaze_points) - 1            # exclude terminator
    term_key_pos = KEYBOARD_LAYOUT["enter"]      # terminator reference

    # weight[depth][key] = inference count. depth 0 = last letter, increasing
    # toward the first letter (we build backward, then reverse for word order).
    weights = [dict() for _ in range(n_letters)]

    # Depth 0: reference is the terminator key; measured geometry uses the last
    # two gaze points (terminator and second-to-last).
    refs = [(term_key_pos, 1.0)]                  # (reference position, weight)
    for depth in range(n_letters):
        gaze_to = gaze_points[len(gaze_points) - 1 - depth]       # current ref gaze
        gaze_from = gaze_points[len(gaze_points) - 2 - depth]     # earlier gaze
        measured_d = _d(gaze_to, gaze_from)
        measured_theta = _ang(gaze_to, gaze_from)

        next_refs = {}
        for (ref_pos, _) in refs:
            cands = _candidates_for(ref_pos, measured_d, measured_theta, gaze_from)
            for k in cands:
                weights[depth][k] = weights[depth].get(k, 0) + 1
                # this candidate becomes a reference for the next (earlier) point
                next_refs[k] = KEYBOARD_LAYOUT[k]
        refs = [(pos, 1.0) for pos in next_refs.values()]
        if not refs:
            break

    # Reverse depth order so index 0 = first letter of the word.
    weights = weights[::-1]

    # Keep only the top candidates per position to bound the combination space.
    # BackTree's job is RECALL: get the true key into each position's set.
    per_pos = []
    for w in weights:
        top = sorted(w.items(), key=lambda kv: kv[1], reverse=True)[:max_per_depth]
        per_pos.append([k for k, _ in top] if top else LETTERS[:max_per_depth])

    # Enumerate dictionary words from the candidate sets (prefix-pruned).
    words = []

    def expand(idx, prefix):
        if prefix and prefix not in prefixes:
            return
        if idx == len(per_pos):
            if prefix in dictionary:
                words.append(prefix)
            return
        for k in per_pos[idx]:
            expand(idx + 1, prefix + k)

    expand(0, "")

    # RANK by geometric fit: a candidate word's key positions should reproduce
    # the measured inter-gaze distances and angles along the whole path,
    # including the final letter -> terminator step.
    def fit_error(word):
        keys = list(word) + ["enter"]
        err = 0.0
        for i in range(len(keys) - 1):
            kp_a = KEYBOARD_LAYOUT[keys[i]]
            kp_b = KEYBOARD_LAYOUT[keys[i + 1]]
            g_a, g_b = gaze_points[i], gaze_points[i + 1]
            err += abs(_d(kp_a, kp_b) - _d(g_a, g_b))
            err += 0.05 * _ang_diff(_ang(kp_a, kp_b), _ang(g_a, g_b))
        return err

    ranked = sorted(set(words), key=fit_error)
    return ranked[:top_words]


def load_dictionary(path="wordlist.txt"):
    with open(path) as f:
        words = {line.strip() for line in f if line.strip()}
    prefixes = set()
    for w in words:
        for i in range(1, len(w) + 1):
            prefixes.add(w[:i])
    return words, prefixes
