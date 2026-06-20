# CSL6010-Cybersecurity Major Project

## SNOOPFINGER Attack Analysis & Defense Simulation (v2 Evaluation)

This repository contains the source code for the major project analyzing and proposing a defense against the **SNOOPFINGER** side-channel attack in AR/VR environments, updated with a rigorous end-to-end evaluation against the real **BackTree** word-inference attack.

### The Problem (SNOOPFINGER)
The "Eyes on Your Typing" IEEE paper demonstrates that subtle head movements during direct hand-based typing on virtual keyboards can inadvertently leak typed text. The SNOOPFINGER attack exploits the unrestricted access to head orientation data (a zero-permission sensor) by background applications to infer keystrokes.

### The Gap & Limitation
The paper identifies countermeasures, such as adaptive sensor data obfuscation, but does not provide a practical implementation or evaluate them against adaptive adversaries. Furthermore, simple frame-level independent noise (IID) is easily averaged out by an attacker who groups samples by keypress dwells.

### The Proposed Solution
We implement and evaluate the **Context-Aware Sensor Obfuscation Middleware (CASOM)**. CASOM runs at the OS level and bifurcates coordinate tracking. It passes clean tracking data to the foreground virtual keyboard (preserving usability) and injects bounded noise into background streams. 

Our recommended mode is **Block Offset**, which draws a fresh Laplace offset once per block of 15 samples (~dwell duration) and holds it constant. This shifts keypress centroids independently, disrupting the relative spatial vectors that the BackTree attack relies on, and cannot be averaged away.

### Repository Module Structure
- [keyboard.py](file:///d:/CS%20IEEE/CSIEEE/keyboard.py): Defines the 2D layout of the virtual keyboard.
- [create_dataset.py](file:///d:/CS%20IEEE/CSIEEE/create_dataset.py): Simulates natural head movements (gaze points) of a user typing.
- [casom_defense.py](file:///d:/CS%20IEEE/CSIEEE/casom_defense.py): Implements the CASOM middleware with multiple defense modes (`iid`, `correlated` drift, `per_keypress` offset, `downsample`, and the recommended `block` offset).
- [backtree.py](file:///d:/CS%20IEEE/CSIEEE/backtree.py): Implementation of the Backward Key Inference Tree (BackTree) geometric attack.
- [adaptive_attacker.py](file:///d:/CS%20IEEE/CSIEEE/adaptive_attacker.py): Dwell-aware attacker that averages coordinate clusters to cancel zero-mean noise.
- [run_backtree_eval.py](file:///d:/CS%20IEEE/CSIEEE/run_backtree_eval.py): Script running the BackTree attack against all defenses, reporting Top-k word accuracy.
- [benchmark.py](file:///d:/CS%20IEEE/CSIEEE/benchmark.py): Runs character-level evaluations against naive and adaptive attackers.
- [main.py](file:///d:/CS%20IEEE/CSIEEE/main.py): Legacy orchestration script for the single-word demo.

### Evaluation Results (BackTree Word Accuracy)
Evaluating word reconstruction over 30 trials with a dictionary of 8,000 words reveals:

| Defense Mode | Word Top-1 | Word Top-3 | Word Top-10 | Status |
| :--- | :---: | :---: | :---: | :---: |
| **No Defense (Baseline)** | **80.9%** | **80.9%** | **80.9%** | Vulnerable |
| **IID Noise (Original)** | 35.8% | 51.8% | 62.9% | Bypassable (Averaged) |
| **Correlated Drift** | 27.6% | 42.1% | 52.7% | Bypassable (Vectors survive) |
| **Downsample & Quantize** | 2.3% | 5.6% | 8.9% | Secured |
| **Block Offset (CASOM)** | **3.6%** | **7.0%** | **13.6%** | Secured (Recommended) |
| **Per-Keypress Offset** | 2.3% | 3.8% | 7.6% | Secured |

### How to Run
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run character-level benchmark:
   ```bash
   python benchmark.py
   ```
3. Run the BackTree word-level evaluation:
   ```bash
   python run_backtree_eval.py --trials 30
   ```
4. This generates the evaluation plots:
   - `benchmark_result.png` (Character accuracy)
   - `backtree_result.png` (Word accuracy)
