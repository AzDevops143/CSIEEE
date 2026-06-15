# benchmark.py
# Evaluates each CASOM defense mode against BOTH a naive attacker and an
# adaptive (averaging) attacker, reporting Top-1 / Top-3 character accuracy
# averaged over many words and trials -- the honest way to claim a defense works.

import math
import random
import statistics

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from keyboard import KEYBOARD_LAYOUT
from create_dataset import generate_fitts_movement_time, minimum_jerk_trajectory
from casom_defense import CASOM
from adaptive_attacker import NaiveAttacker, AdaptiveAttacker, char_topk_accuracy

WORDS = ["fox", "the", "quick", "brown", "jumps", "over", "lazy", "dog",
         "cyber", "secure", "vision", "keyboard"]

TRIALS = 30
SAMPLE_RATE = 72.0


def generate_stream(word, rng):
    """In-memory version of create_dataset: returns (points, segments, chars).

    points   : list[(x, y)] for the typing (dwell) samples only.
    segments : list[(start, end)] dwell boundaries into `points`.
    chars    : the true character for each segment.
    """
    dt = 1.0 / SAMPLE_RATE
    pts, segments, chars = [], [], []
    cur = (4.5, 1.0)
    for ch in word.lower():
        if ch not in KEYBOARD_LAYOUT:
            continue
        target = KEYBOARD_LAYOUT[ch]
        mt = generate_fitts_movement_time(math.hypot(target[0] - cur[0],
                                                      target[1] - cur[1]))
        # Travel frames are discarded by the attacker (is_typing == False),
        # so we only emit dwell samples here.
        dwell = rng.uniform(0.15, 0.30)
        n = max(int(dwell / dt), 3)
        start = len(pts)
        for _ in range(n):
            jx = rng.gauss(0, 0.03)
            jy = rng.gauss(0, 0.03)
            pts.append((target[0] + jx, target[1] + jy))
        segments.append((start, len(pts)))
        chars.append(ch)
        cur = target
    return pts, segments, chars


def run():
    modes = ["none", "iid", "downsample", "per_keypress", "correlated"]
    naive, adaptive = NaiveAttacker(), AdaptiveAttacker()
    # results[mode] = {"naive_t1":[], "adaptive_t1":[], "adaptive_t3":[]}
    results = {m: {"naive_t1": [], "adaptive_t1": [], "adaptive_t3": []}
               for m in modes}

    for trial in range(TRIALS):
        rng = random.Random(1000 + trial)
        for word in WORDS:
            pts, segs, chars = generate_stream(word, rng)
            for mode in modes:
                if mode == "none":
                    obf = pts
                else:
                    cas = CASOM(mode=mode, noise_scale=1.5, seed=trial * 97 + 7)
                    obf = cas.obfuscate(pts, segments=segs)

                # Adaptive attacker uses the true dwell boundaries. For
                # downsample the indices change, so it re-segments by ratio.
                if mode == "downsample":
                    f = cas.downsample_factor
                    a_segs = [(s // f, max(e // f, s // f + 1)) for (s, e) in segs]
                    a_segs = [(s, min(e, len(obf))) for (s, e) in a_segs]
                else:
                    a_segs = segs

                naive_ranked = naive.ranked_per_key(obf)
                adapt_ranked = adaptive.ranked_per_key(obf, a_segs)

                # Naive may return the wrong number of clusters; align by count.
                results[mode]["naive_t1"].append(
                    _aligned_topk(naive_ranked, chars, k=1))
                results[mode]["adaptive_t1"].append(
                    char_topk_accuracy(adapt_ranked, chars, k=1))
                results[mode]["adaptive_t3"].append(
                    char_topk_accuracy(adapt_ranked, chars, k=3))

    _print_table(modes, results)
    _plot(modes, results)
    return results


def _aligned_topk(ranked, chars, k):
    # Naive segmentation can miscount keys; compare only over the overlap.
    n = min(len(ranked), len(chars))
    if n == 0:
        return 0.0
    return char_topk_accuracy(ranked[:n], chars[:n], k)


def _mean(xs):
    return statistics.mean(xs) if xs else 0.0


def _print_table(modes, results):
    print(f"\n{'Defense mode':<14} | {'Naive Top-1':>11} | "
          f"{'Adaptive Top-1':>14} | {'Adaptive Top-3':>14}")
    print("-" * 62)
    for m in modes:
        r = results[m]
        print(f"{m:<14} | {_mean(r['naive_t1'])*100:>10.1f}% | "
              f"{_mean(r['adaptive_t1'])*100:>13.1f}% | "
              f"{_mean(r['adaptive_t3'])*100:>13.1f}%")
    print("\nKey reading: the attacker that matters is 'Adaptive Top-1'. A real")
    print("defense must push THAT down. Naive Top-1 dropping is not protection.")


def _plot(modes, results):
    labels = {"none": "No defense", "iid": "iid noise\n(original)",
              "downsample": "downsample\n+quantize",
              "per_keypress": "per-keypress\noffset",
              "correlated": "correlated\ndrift (new)"}
    naive = [_mean(results[m]["naive_t1"]) * 100 for m in modes]
    adapt = [_mean(results[m]["adaptive_t1"]) * 100 for m in modes]

    x = range(len(modes))
    w = 0.38
    fig, ax = plt.subplots(figsize=(11, 5.5))
    b1 = ax.bar([i - w / 2 for i in x], naive, w,
                label="Naive attacker (Top-1)", color="#9ecae1")
    b2 = ax.bar([i + w / 2 for i in x], adapt, w,
                label="Adaptive attacker (Top-1)", color="#de2d26")
    ax.set_xticks(list(x))
    ax.set_xticklabels([labels[m] for m in modes])
    ax.set_ylabel("Character inference accuracy (%)")
    ax.set_ylim(0, 105)
    ax.set_title("CASOM defenses vs SnoopFinger attackers\n"
                 "(lower = better defense; the adaptive attacker is the honest test)")
    ax.legend()
    ax.axhline(100 / 27, color="gray", ls="--", lw=1)
    ax.text(len(modes) - 0.5, 100 / 27 + 2, "random guess (1/27)",
            color="gray", ha="right", fontsize=8)
    for bars in (b1, b2):
        for bar in bars:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                    f"{bar.get_height():.0f}", ha="center", fontsize=8)
    plt.tight_layout()
    plt.savefig("benchmark_result.png", dpi=130)
    print("\nSaved plot -> benchmark_result.png")


if __name__ == "__main__":
    run()
