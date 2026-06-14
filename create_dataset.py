# create_dataset.py
import csv
import random
from keyboard import KEYBOARD_LAYOUT

def create_vr_telemetry(word, filename="vr_telemetry_dataset.csv", noise_level=0.15):
    """
    Generates a realistic mock dataset mimicking Oculus Quest 2 telemetry at 72 Hz.
    Writes the data to a CSV file.
    """
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        # Write the header
        writer.writerow(['timestamp', 'x', 'y', 'z', 'is_typing', 'target_char'])
        
        timestamp = 1620000000.000 # arbitrary starting epoch
        time_step = 1.0 / 72.0     # 72 Hz = 13.8 ms
        
        for char in word.lower():
            if char in KEYBOARD_LAYOUT:
                target_x, target_y = KEYBOARD_LAYOUT[char]
                
                # Simulate the "travel" or moving towards the key (non-typing data)
                num_travel_points = random.randint(5, 15)
                for _ in range(num_travel_points):
                    px = target_x + random.uniform(-1.0, 1.0) # wilder movement
                    py = target_y + random.uniform(-1.0, 1.0)
                    pz = random.uniform(0.5, 0.7) # arbitrary depth
                    writer.writerow([f"{timestamp:.3f}", f"{px:.4f}", f"{py:.4f}", f"{pz:.4f}", 'False', 'None'])
                    timestamp += time_step

                # Simulate the "dwell" or slowing down at the keypress (typing data)
                # The attacker uses this to infer the keystroke
                num_points_in_cluster = random.randint(3, 8)
                for _ in range(num_points_in_cluster):
                    px = target_x + random.uniform(-noise_level, noise_level)
                    py = target_y + random.uniform(-noise_level, noise_level)
                    pz = random.uniform(0.5, 0.55)
                    writer.writerow([f"{timestamp:.3f}", f"{px:.4f}", f"{py:.4f}", f"{pz:.4f}", 'True', char])
                    timestamp += time_step

    print(f"[*] Dataset successfully generated and saved to '{filename}'.")

if __name__ == "__main__":
    # Generate a dataset for testing the attack and defense
    target_word = "foxenter"
    print(f"[*] Generating VR telemetry dataset for target word: '{target_word}'...")
    create_vr_telemetry(target_word)
