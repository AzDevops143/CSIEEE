# generator.py
import random
from keyboard import KEYBOARD_LAYOUT

class HeadMovementSimulator:
    def __init__(self, noise_level=0.15):
        """
        noise_level simulates the natural inaccuracy of a human head
        pointing at a key on a virtual keyboard.
        """
        self.noise_level = noise_level
        self.sampling_rate = 72 # 72 Hz as in the SNOOPFINGER paper

    def simulate_typing(self, word):
        """
        Generates simulated 2D gaze points for a given word.
        Returns a list of (x, y) tuples.
        """
        gaze_points = []
        for char in word.lower():
            if char in KEYBOARD_LAYOUT:
                target_x, target_y = KEYBOARD_LAYOUT[char]
                
                # Simulate the "pause" or slowing down at the keypress
                # We generate a cluster of points around the target key
                num_points_in_cluster = random.randint(3, 8)
                
                for _ in range(num_points_in_cluster):
                    # Add natural human noise
                    px = target_x + random.uniform(-self.noise_level, self.noise_level)
                    py = target_y + random.uniform(-self.noise_level, self.noise_level)
                    gaze_points.append((px, py))
                    
        return gaze_points
