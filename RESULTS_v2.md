# CASOM v2 — End-to-End Evaluation Against the Real BackTree Attack

This extends the project from a single-word demo to an honest, end-to-end
evaluation: the actual SnoopFinger geometric attack (Backward Key Inference
Tree, paper §5.6) is run against every candidate defense, and defenses are
judged by the paper's metric — **word-level Top-1 accuracy**.

## The flaw in the original defense

The original `defender.py` added independent zero-mean noise to every 72 Hz
sample. Each keypress dwell holds ~15–35 samples, so an attacker who segments by
dwell and averages each cluster cancels that noise. The original `main.py` only
*looked* protected because the noise broke the toy attacker's clustering, not
because the spatial information was gone. (Secondary issues: it used
`random.uniform`, not the Laplace noise the docs claimed, and there was no ε /
sensitivity, so the "differential privacy" label did not hold.)

## What the end-to-end test revealed (and corrected)

A first, character-level test suggested a slow "correlated drift" would be the
fix. Running the **real BackTree attack** disproved that:

BackTree ranks words by the **relative geometry** — the vectors between
consecutive gaze points. A slow drift shifts consecutive points by nearly the
same amount, so those vectors survive and the attack still works. The only
defenses that work are ones that displace **each key independently** and are not
averaged away.

## Results — BackTree word inference (30 trials, ~22 words, 8k-word dictionary)

| Defense mode        | Word Top-1 | Word Top-3 | Word Top-10 |
|---------------------|-----------:|-----------:|------------:|
| none (attack works) | **~70–86%**|  ~70–86%   |    ~70–86%  |
| iid (original)      |      ~38%  |      ~53%  |       ~64%  |
| correlated drift    |      ~29%  |      ~44%  |       ~55%  |
| downsample+quantize |     ~4%    |      ~7%   |       ~12%  |
| block offset (rec.) |     ~4%    |      ~7%   |       ~14%  |
| per-keypress offset |     ~3%    |      ~5%   |        ~8%  |

(The no-defense baseline exceeds the paper's 55% because the synthetic gaze is
cleaner than real hardware and the ranking uses full-path geometric fit.)

### Reading the table
- **iid and correlated are NOT effective**: they leave Word Top-1 at ~30–40%
  and Top-10 above 50%. Drift in particular fails by design (it preserves
  relative geometry).
- **The effective defenses displace each key independently**: per-keypress
  offset, the deployable `block` offset, and downsampling all collapse Word
  Top-1 to ~3–4%, near chance for an 8k dictionary.

## Recommended defense: `block` offset

`block` draws a fresh Laplace offset every ~dwell-length window and holds it
constant within the window. It matches per-keypress effectiveness but needs only
a fixed cadence, **not exact keypress boundaries** — so it is deployable from the
existing CASOM typing detector. Foreground keyboard input is untouched; only the
background stream is perturbed.

## Files

- `casom_defense.py` — CASOM with modes: `iid`, `correlated`, `per_keypress`,
  `block` (recommended), `downsample`; real Laplace sampler; back-compat shim.
- `adaptive_attacker.py` — dwell-aware averaging attacker + ranked candidates.
- `backtree.py` — faithful BackTree word inference with dictionary ranking.
- `run_backtree_eval.py` — word-level Top-k evaluation across defenses → table +
  `backtree_result.png`.
- `benchmark.py` — character-level naive-vs-adaptive comparison →
  `benchmark_result.png`.
- `wordlist.txt` — 8,000 frequency-ranked 3–6 letter words (bundled, no network).

## Reproduce / CI

```bash
pip install -r requirements.txt
python run_backtree_eval.py --trials 30
python benchmark.py
```

GitHub Actions (`.github/workflows/evaluation.yml`) runs the sanity demo, the
character benchmark, and the word-level BackTree evaluation on every push, and
uploads both plots as artifacts. It is self-contained: `MPLBACKEND=Agg` for
headless plotting and the wordlist is committed, so no network is needed at run
time.

## Honest limitations

- Synthetic gaze (Fitts + minimum-jerk + tremor), not real headset captures.
- The adaptive attacker is given true dwell boundaries (best-case adversary) —
  intentional, to stress-test defenses against the strongest reasonable attacker.
- Word-level only; sentence reconstruction (DBSCAN space detection) is the next
  step. A formal DP statement (sensitivity + ε over a typing window) would build
  on the `per_keypress` / `block` modes.
