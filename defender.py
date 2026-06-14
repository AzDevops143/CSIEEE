# defender.py
import random

class CASOMMiddleware:
    def __init__(self, noise_scale=1.5, use_rounding=False):
        """
        Context-Aware Sensor Obfuscation Middleware (CASOM)
        noise_scale: The amount of Laplacian noise to add when typing is detected.
        use_rounding: If True, reduces the precision of the float instead of adding noise.
        """
        self.noise_scale = noise_scale
        self.use_rounding = use_rounding

    def obfuscate_data(self, gaze_points):
        """
        Takes raw gaze points (as they would be collected by a background app)
        and applies obfuscation.
        """
        obfuscated_points = []
        for (x, y) in gaze_points:
            if self.use_rounding:
                # Reduce precision (e.g., round to nearest integer)
                ox = round(x)
                oy = round(y)
            else:
                # Add Laplacian noise to scatter the points, breaking the clusters
                ox = x + random.uniform(-self.noise_scale, self.noise_scale)
                oy = y + random.uniform(-self.noise_scale, self.noise_scale)
            
            obfuscated_points.append((ox, oy))
            
        return obfuscated_points
