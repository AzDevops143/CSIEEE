# keyboard.py

# A simplified 2D representation of a QWERTY virtual keyboard
# Coordinates are (x, y) where x is horizontal and y is vertical.
# Let's assume keys are spaced by 1 unit.

KEYBOARD_LAYOUT = {
    'q': (0, 2), 'w': (1, 2), 'e': (2, 2), 'r': (3, 2), 't': (4, 2), 'y': (5, 2), 'u': (6, 2), 'i': (7, 2), 'o': (8, 2), 'p': (9, 2),
    'a': (0.5, 1), 's': (1.5, 1), 'd': (2.5, 1), 'f': (3.5, 1), 'g': (4.5, 1), 'h': (5.5, 1), 'j': (6.5, 1), 'k': (7.5, 1), 'l': (8.5, 1),
    'z': (1, 0), 'x': (2, 0), 'c': (3, 0), 'v': (4, 0), 'b': (5, 0), 'n': (6, 0), 'm': (7, 0),
    'enter': (9, 0),
    'space': (4.5, -1)
}

def get_key_from_pos(x, y, threshold=0.6):
    """Finds the closest key to a given (x, y) coordinate."""
    closest_key = None
    min_dist = float('inf')
    
    for key, (kx, ky) in KEYBOARD_LAYOUT.items():
        dist = ((kx - x)**2 + (ky - y)**2)**0.5
        if dist < min_dist:
            min_dist = dist
            closest_key = key
            
    if min_dist <= threshold:
        return closest_key
    return None
