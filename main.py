# main.py
import matplotlib.pyplot as plt
from generator import HeadMovementSimulator
from attacker import SnoopfingerAttacker
from defender import CASOMMiddleware
from keyboard import KEYBOARD_LAYOUT

def plot_simulation(original_points, obfuscated_points, word):
    """
    Visualizes the raw vs obfuscated gaze points on the virtual keyboard.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle(f"SNOOPFINGER Attack Simulation vs CASOM Defense\nTarget Word: '{word}'")

    # Extract X, Y for keyboard keys
    keys_x = [pos[0] for pos in KEYBOARD_LAYOUT.values()]
    keys_y = [pos[1] for pos in KEYBOARD_LAYOUT.values()]
    key_labels = list(KEYBOARD_LAYOUT.keys())

    # --- Plot 1: Unprotected (Attacker's view without defense) ---
    ax1.set_title("Unprotected: Raw Head Movement Data")
    ax1.scatter(keys_x, keys_y, color='lightgray', s=200, marker='s') # Keyboard background
    for i, label in enumerate(key_labels):
        ax1.text(keys_x[i], keys_y[i], label, ha='center', va='center', fontsize=8)
        
    orig_x = [p[0] for p in original_points]
    orig_y = [p[1] for p in original_points]
    ax1.plot(orig_x, orig_y, color='red', alpha=0.5, linestyle='-', linewidth=1, label='Gaze Path')
    ax1.scatter(orig_x, orig_y, color='darkred', s=10, label='Gaze Points (72Hz)')
    ax1.legend()

    # --- Plot 2: Protected (Attacker's view with CASOM defense) ---
    ax2.set_title("Protected: Obfuscated Data (CASOM)")
    ax2.scatter(keys_x, keys_y, color='lightgray', s=200, marker='s')
    for i, label in enumerate(key_labels):
        ax2.text(keys_x[i], keys_y[i], label, ha='center', va='center', fontsize=8)
        
    obf_x = [p[0] for p in obfuscated_points]
    obf_y = [p[1] for p in obfuscated_points]
    ax2.plot(obf_x, obf_y, color='blue', alpha=0.3, linestyle='-', linewidth=1, label='Obfuscated Path')
    ax2.scatter(obf_x, obf_y, color='darkblue', s=10, label='Obfuscated Points')
    ax2.legend()

    plt.tight_layout()
    plt.savefig('simulation_result.png')
    print("Simulation visualization saved to 'simulation_result.png'")


def main():
    target_word = "foxenter"
    
    # 1. Simulate user typing
    simulator = HeadMovementSimulator(noise_level=0.15)
    print(f"[*] Simulating user typing: '{target_word}'")
    raw_gaze_points = simulator.simulate_typing(target_word)
    
    # 2. Attacker tries to infer the word from raw data
    attacker = SnoopfingerAttacker(cluster_threshold=0.8)
    inferred_unprotected = attacker.infer_word(raw_gaze_points)
    print(f"[!] Attacker inference (UNPROTECTED): '{inferred_unprotected}'")
    
    # 3. Apply CASOM defense
    defender = CASOMMiddleware(noise_scale=1.5, use_rounding=False)
    obfuscated_gaze_points = defender.obfuscate_data(raw_gaze_points)
    
    # 4. Attacker tries to infer the word from obfuscated data
    inferred_protected = attacker.infer_word(obfuscated_gaze_points)
    print(f"[+] Attacker inference (PROTECTED): '{inferred_protected}'")
    
    # 5. Visualize
    plot_simulation(raw_gaze_points, obfuscated_gaze_points, target_word)

if __name__ == "__main__":
    main()
