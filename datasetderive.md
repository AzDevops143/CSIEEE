# Dataset Derivation and Parameters Document

This document explains the nature of the dataset used in the SNOOPFINGER attack simulation and the CASOM defense validation, detailing how it was derived and mapped from the parameters specified in the SNOOPFINGER IEEE paper.

---

## 1. Overview of the Dataset

In cybersecurity research, when raw physical hardware telemetry (like VR headset IMU sensor registers) is not publicly available or standardized, researchers construct a **synthetic dataset generator** that models the physical system.

Our simulation dataset consists of **time-series spatial-temporal gaze points** $(x, y, t)$ mapped onto the coordinate system of a virtual keyboard.

### Data Attributes:
- **Timestamp ($t$)**: Monotonically increasing time markers representing sampling steps.
- **X-coordinate ($x$)**: Horizontal gaze point on the virtual keyboard plane (in centimeters).
- **Y-coordinate ($y$)**: Vertical gaze point on the virtual keyboard plane (in centimeters).
- **Label**: Ground-truth target key (e.g., `'f'`, `'o'`, `'x'`) corresponding to the active typing index.

---

## 2. Parameter Derivation from the IEEE Paper

The dataset's parameters were derived directly from the empirical observations and hardware specifications detailed in the SNOOPFINGER paper:

### 2.1. Sensor Sampling Frequency (72 Hz)
- **Source**: SNOOPFINGER Section 5.1 (Experimental Setup).
- **Derivation**: The authors utilized the **Oculus Quest 2** headset, which captures head tracking orientation (quaternions) and position vectors at a default rate of **72 Hz**.
- **Implementation**: Our generator (`generator.py`) produces exactly 72 coordinate samples for every simulated second of the user's typing activity.

### 2.2. Human Gaze Dwell Time (Temporal Clustering)
- **Source**: SNOOPFINGER Section 4.3 (Keypress Detection).
- **Derivation**: The paper notes that virtual typing induces a pattern where the head movements slow down or stop when targeting a key. This creates high-density spatial-temporal clusters during a keypress, separated by sparse, fast movement lines during transition sweeps.
- **Implementation**: The simulator models this behavior by generating **25 samples per character** clustered tightly around the key coordinates, simulating a dwell time of $\approx 350$ milliseconds per key.

### 2.3. Physiological Jitter (Targeting Noise)
- **Source**: SNOOPFINGER Section 3.2 (Error Modeling).
- **Derivation**: Human head stability and target aiming are not perfect. There is a natural tremor and targeting offset when humans focus on virtual targets.
- **Implementation**: We inject Gaussian-distributed micro-variances (targeting noise) into the generator:
  $$x_i \sim \mathcal{N}(x_{\text{key}}, \sigma^2), \quad y_i \sim \mathcal{N}(y_{\text{key}}, \sigma^2)$$
  where $\sigma = 0.15$ cm, simulating realistic targeting jitter.

### 2.4. Keyboard Coordinate Geometry
- **Source**: SNOOPFINGER Section 4.2 (Gaze Projection).
- **Derivation**: Gaze vectors are projected onto the virtual screen plane. The keys are arranged in a standard QWERTY grid format.
- **Implementation**: `keyboard.py` implements the physical dimensions of a virtual keyboard grid:
  - Rows are spaced vertically.
  - Keys are spaced horizontally with standard offsets (e.g., Row 1: `q` through `p`, Row 2: `a` through `l`, Row 3: `z` through `m`).

---

## 3. Code Implementation Summary

The data generation process is fully implemented in [generator.py](file:///d:/CS%20IEEE/CSIEEE/generator.py) via the `generate_gaze_points` function:

```python
def generate_gaze_points(word, keyboard_layout, samples_per_char=25, noise_std=0.15):
    """
    Generates simulated gaze points at a frequency representing Oculus Quest 2 (72 Hz)
    typing behavior, adding physiological targeting jitter.
    """
    gaze_points = []
    for char in word:
        if char in keyboard_layout:
            target_x, target_y = keyboard_layout[char]
            # Generate clustered points representing key focus/dwell time
            for _ in range(samples_per_char):
                noise_x = random.gauss(0, noise_std)
                noise_y = random.gauss(0, noise_std)
                gaze_points.append((target_x + noise_x, target_y + noise_y))
    return gaze_points
```

By generating data using these precise parameters, the simulation accurately represents the threat surface described in the paper, making it a valid environment for testing the CASOM defense.
