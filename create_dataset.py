# create_dataset.py
import csv
import math
import random
import sys
from keyboard import KEYBOARD_LAYOUT

def generate_fitts_movement_time(dist, width=1.0):
    """Fitts' law: MT = a + b * log2(2*D/W)"""
    a, b = 0.2, 0.15
    return a + b * math.log2(2 * max(dist, 0.1) / width)

def minimum_jerk_trajectory(t, duration, p_start, p_end):
    """Standard minimum-jerk trajectory formula for natural human movement"""
    tau = min(t / duration, 1.0)
    scale = 10 * (tau ** 3) - 15 * (tau ** 4) + 6 * (tau ** 5)
    
    x = p_start[0] + (p_end[0] - p_start[0]) * scale
    y = p_start[1] + (p_end[1] - p_start[1]) * scale
    return x, y

def create_vr_telemetry(word, filename="vr_telemetry_dataset.csv", noise_level=0.15):
    """
    Generates a realistic mock dataset mimicking Oculus Quest 2 telemetry at 72 Hz
    using Fitts's Law, Minimum-Jerk trajectories, and physiological tremor.
    Writes the data to a CSV file.
    """
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        # Write the header
        writer.writerow(['timestamp', 'x', 'y', 'z', 'is_typing', 'target_char'])
        
        timestamp = 1620000000.000 # arbitrary starting epoch
        time_step = 1.0 / 72.0     # 72 Hz = 13.8 ms
        
        # Starting position (assume looking at the center of the keyboard initially)
        current_pos = (4.5, 1.0) 
        
        for char in word.lower():
            if char not in KEYBOARD_LAYOUT:
                continue
                
            target_pos = KEYBOARD_LAYOUT[char]
            dist = math.hypot(target_pos[0] - current_pos[0], target_pos[1] - current_pos[1])
            
            # 1. Travel phase (Saccade/Head movement towards the key)
            movement_time = generate_fitts_movement_time(dist)
            num_travel_frames = max(int(movement_time / time_step), 3)
            
            for i in range(num_travel_frames):
                t = i * time_step
                # Base smooth trajectory
                base_x, base_y = minimum_jerk_trajectory(t, movement_time, current_pos, target_pos)
                
                # Add physiological tremor (e.g. 10 Hz) and sensor noise
                tremor_amp = 0.05
                tremor_x = math.sin(2 * math.pi * 10 * timestamp) * tremor_amp
                tremor_y = math.cos(2 * math.pi * 10 * timestamp) * tremor_amp
                noise_x = random.gauss(0, 0.02)
                noise_y = random.gauss(0, 0.02)
                
                px = base_x + tremor_x + noise_x
                py = base_y + tremor_y + noise_y
                pz = random.gauss(0.5, 0.01) # fairly stable depth
                
                writer.writerow([f"{timestamp:.3f}", f"{px:.4f}", f"{py:.4f}", f"{pz:.4f}", 'False', 'None'])
                timestamp += time_step
                
            # 2. Dwell phase (Fixation on the key to simulate a "keypress")
            # Usually takes 150-300ms to register a dwell click
            dwell_time = random.uniform(0.15, 0.3)
            num_dwell_frames = int(dwell_time / time_step)
            
            current_pos = target_pos # Update current position for next letter
            
            for i in range(num_dwell_frames):
                # During dwell, the user tries to hold still, but micro-tremors remain
                tremor_amp = 0.03
                tremor_x = math.sin(2 * math.pi * 10 * timestamp) * tremor_amp
                tremor_y = math.cos(2 * math.pi * 10 * timestamp) * tremor_amp
                noise_x = random.gauss(0, 0.01)
                noise_y = random.gauss(0, 0.01)
                
                px = target_pos[0] + tremor_x + noise_x
                py = target_pos[1] + tremor_y + noise_y
                pz = random.gauss(0.5, 0.005)
                
                writer.writerow([f"{timestamp:.3f}", f"{px:.4f}", f"{py:.4f}", f"{pz:.4f}", 'True', char])
                timestamp += time_step

    print(f"[*] Realistic dataset successfully generated and saved to '{filename}'.")

if __name__ == "__main__":
    # Generate a dataset for testing the attack and defense
    target_word = sys.argv[1] if len(sys.argv) > 1 else "foxenter"
    print(f"[*] Generating realistic VR telemetry dataset for target word: '{target_word}'...")
    create_vr_telemetry(target_word)
