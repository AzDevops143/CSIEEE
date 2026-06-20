# CASOM: How the Protection Works (v2)

This document describes the operational flow and mechanism of the **Context-Aware Sensor Obfuscation Middleware (CASOM)**, illustrating how it defends against side-channel virtual keystroke attacks like SNOOPFINGER.

---

## 1. Operational Flow & Architecture

The protection operates as an OS-level middleware service in the AR/VR system. Below is the technical architecture showing the data routing and the security boundary:

```mermaid
flowchart TD
    A[AR/VR Headset Sensor Hardware <br> IMU, Cameras, Quaternions] --> B[OS Sensor Manager]
    
    subgraph CASOM [CASOM Middleware Protection Layer]
        B --> C{Context Analyzer <br> Is Typing Active?}
        C -- YES --> D[Stream Bifurcator / Router]
        C -- NO --> E[Pass-through Mode]
        
        D -->|Route A: Foreground| F[Clean High-Fidelity Data Stream]
        D -->|Route B: Background| G[Obfuscation Engine <br> Inject Block Laplace Noise]
    end
    
    F --> H[Foreground App <br> Virtual Keyboard]
    G --> I[Background App <br> Malicious Keystroke Logger]
    E --> I
    
    style CASOM fill:#f5f5f5,stroke:#333,stroke-width:2px,stroke-dasharray: 5 5
    style G fill:#f9d,stroke:#333,stroke-width:2px
    style H fill:#bbf,stroke:#333,stroke-width:2px
    style I fill:#fbb,stroke:#333,stroke-width:2px
```

---

## 2. Phase 1: Context-Aware Detection

> [!NOTE]
> Obfuscating sensor data continuously would degrade user experience (UX) for regular activities such as playing games, painting, or using VR gestures that require millimeter-level precision.
>
> To avoid this, CASOM is **context-aware** and only activates its obfuscation routine when typing is active.

- It monitors system focus events (e.g., when the Virtual Keyboard focus goes high).
- It analyzes head motion stability. Typing requires focusing on keys, which creates a signature pattern of micro-pauses.
- Once these triggers are detected, the middleware activates its **obfuscation routine**.

---

## 3. Phase 2: Stream Bifurcation (Data Separation)

Once typing is detected, CASOM separates the sensor streams between apps based on their permissions and window focus state:

1. **Foreground Application (Virtual Keyboard)**:
   - Receives the **raw, clean, high-precision** sensor coordinate data.
   - **Result**: Legitimate typing actions are processed with 100% accuracy and zero latency.
   
2. **Background Applications (Potential Spyware)**:
   - Blocked from reading raw sensor registers.
   - Forced to receive the output of the **obfuscation engine**.
   - **Result**: Malicious background trackers cannot access the high-resolution movements required to map gaze to keys.

---

## 4. Phase 3: Obfuscation Engine (Block Laplace Noise)

The SNOOPFINGER attack relies on **spatial-temporal clustering**. When a user types, their head pauses on key locations, creating dense clusters of gaze points. The attacker uses distance-based clustering algorithms to calculate the centroids of these clusters and matches them to standard keyboard coordinates.

CASOM v2 destroys this threat mathematically by applying **Block Laplace Noise** to the background data stream. Rather than perturbing each frame independently (which can be bypassed by averaging), the middleware shifts each dwell block by a single constant offset drawn from the Laplace distribution:

$$x' = x + \text{Noise}_x$$
$$y' = y + \text{Noise}_y$$

By setting the noise scale parameter to $1.5$ cm (which is larger than the width of a virtual key) and maintaining this offset over blocks of 15 frames, the points are scattered across multiple key boundaries, scrambling key centroids and breaking the relative geometry vectors.

---

## 5. Python Implementation Reference

In our codebase, this logic is implemented in [casom_defense.py](file:///d:/CS%20IEEE/CSIEEE/casom_defense.py):

```python
def obfuscate(self, gaze_points, segments=None):
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

def _block(self, pts):
    out = []
    ox = oy = 0.0
    for i, (x, y) in enumerate(pts):
        if i % self.block_samples == 0:
            ox = self._laplace(self.noise_scale)
            oy = self._laplace(self.noise_scale)
        out.append((x + ox, y + oy))
    return out
```

---

## 6. How it Thwarts the Attacker

The diagram below illustrates how raw coordinate clusters are processed by the attacker in both unprotected and protected scenarios, demonstrating why the defense is successful:

```mermaid
flowchart TD
    subgraph Scenario_1 [Unprotected Scenario: Raw Coordinates]
        direction TB
        A1["Raw Gaze Points: <br> (2.05, 1.01), (1.98, 0.98), (2.02, 1.02)"] --> B1["Temporal Cluster Centroid: <br> (2.01, 1.00)"]
        B1 --> C1["Distance Lookup: <br> Key 'F' (2.0, 1.0) is closest"]
        C1 --> D1["Inferred Character: 'F'"]
    end
    
    subgraph Scenario_2 [Protected Scenario: CASOM Block Active]
        direction TB
        A2["Raw Gaze Points: <br> (2.05, 1.01), (1.98, 0.98), (2.02, 1.02)"] --> B2["CASOM: Apply Constant Block Offset <br> (ox = 1.34, oy = 0.85)"]
        B2 --> C2["Obfuscated Points: <br> (3.39, 1.86), (3.32, 1.83), (3.36, 1.87)"]
        C2 --> D2["Averaged Centroid Shifted: <br> (3.35, 1.85)"]
        D2 --> E2["Distance Lookups: <br> Centroid maps to 'R' (3.0, 2.0) instead of 'F'"]
        E2 --> F2["Inferred Characters: Scrambled <br> (Gibberish Output)"]
    end

    style Scenario_1 fill:#e6ffe6,stroke:#333
    style Scenario_2 fill:#ffe6e6,stroke:#333
```

- **Unprotected**: Points form a tight cluster centered at `x = 2.01, y = 1.00` (Key: `F`). The centroid calculation points directly to `F`.
- **Protected by CASOM**: Points are shifted consistently by the block offset. The resulting centroid is calculated at `x = 3.35, y = 1.85`, which maps to `R` (or another adjacent key), creating complete gibberish (e.g. `'zrf'`). Because the offset is constant across the dwell block, the attacker cannot cancel it out by averaging.
