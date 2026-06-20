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

- **Sensor Sampling Frequency (72 Hz)**: The Oculus Quest 2 headset captures tracking data at a default rate of **72 Hz**. Our generator ([create_dataset.py](file:///d:/CS%20IEEE/CSIEEE/create_dataset.py)) produces exactly 72 coordinate samples for every simulated second of typing.
- **Human Gaze Dwell Time**: Gaze movements slow down during target focus. The simulator models this by generating **25 samples per character** clustered tightly around the key coordinates.
- **Physiological Jitter**: Gaussian-distributed micro-variances simulate targeting jitter.
  $$x_i \sim \mathcal{N}(x_{\text{key}}, \sigma^2), \quad y_i \sim \mathcal{N}(y_{\text{key}}, \sigma^2)$$
  where $\sigma = 0.15$ cm.
- **Keyboard Coordinate Geometry**: [keyboard.py](file:///d:/CS%20IEEE/CSIEEE/keyboard.py) implements the physical dimensions of the virtual keyboard grid.

---

## 3. Code Implementation Summary

The data generation process is fully implemented in [create_dataset.py](file:///d:/CS%20IEEE/CSIEEE/create_dataset.py) via the `create_vr_telemetry` function:

```python
def create_vr_telemetry(word, filename="vr_telemetry_dataset.csv", noise_level=0.15):
    """
    Generates a realistic mock dataset mimicking Oculus Quest 2 telemetry at 72 Hz.
    Writes the data to a CSV file.
    """
```

By mathematically generating data using these precise parameters, the script produces a highly realistic `vr_telemetry_dataset.csv` file. This allows our [main.py](file:///d:/CS%20IEEE/CSIEEE/main.py) simulation to accurately represent the threat surface described in the paper by reading external "raw" data, making it a valid environment for testing the CASOM defense.
