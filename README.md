# CSL6010-Cybersecurity Major Project

## SNOOPFINGER Attack Analysis & Defense Simulation

This repository contains the source code for the major project analyzing and proposing a defense against the **SNOOPFINGER** side-channel attack in AR/VR environments.

### The Problem (SNOOPFINGER)
The "Eyes on Your Typing" IEEE paper demonstrates that subtle head movements during direct hand-based typing on virtual keyboards can inadvertently leak typed text. The SNOOPFINGER attack exploits the unrestricted access to head orientation data (a zero-permission sensor) by background applications to infer keystrokes.

### The Gap & Limitation
The paper identifies several countermeasures, such as adaptive sensor data obfuscation, but does not provide a practical implementation or evaluate its effectiveness.

### The Proposed Solution
We propose the **Context-Aware Sensor Obfuscation Middleware (CASOM)**. This middleware runs at the OS level and detects when a user is actively typing. Upon detection, it dynamically adds Laplacian noise to the head orientation data broadcasted to background applications, while passing clean data to the foreground application (the virtual keyboard) to maintain user experience.

### Implementation Details
This repository features a Python simulation to demonstrate the effectiveness of the CASOM defense:
- `keyboard.py`: Defines the 2D layout of the virtual keyboard.
- `generator.py`: Simulates the natural head movements (gaze points) of a user typing a word.
- `attacker.py`: Simulates the SNOOPFINGER attack, attempting to cluster the raw gaze points and infer the typed text.
- `defender.py`: Implements the CASOM middleware, applying adaptive noise to the data.
- `main.py`: Runs the simulation, comparing the attacker's success on unprotected (raw) data versus protected (obfuscated) data.

### How to Run
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the simulation:
   ```bash
   python main.py
   ```
3. A visualization image `simulation_result.png` will be generated, illustrating how the defense scatters the gaze points and breaks the attacker's inference capabilities.
