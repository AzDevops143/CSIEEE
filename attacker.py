# attacker.py
from keyboard import get_key_from_pos

class SnoopfingerAttacker:
    def __init__(self, cluster_threshold=0.8):
        """
        cluster_threshold: maximum distance between consecutive points 
        to be considered part of the same keypress cluster.
        """
        self.cluster_threshold = cluster_threshold

    def extract_keypress_clusters(self, gaze_points):
        """
        Groups consecutive points that are close to each other into clusters,
        representing a single keypress.
        """
        if not gaze_points:
            return []

        clusters = []
        current_cluster = [gaze_points[0]]

        for pt in gaze_points[1:]:
            last_pt = current_cluster[-1]
            dist = ((pt[0] - last_pt[0])**2 + (pt[1] - last_pt[1])**2)**0.5
            
            if dist < self.cluster_threshold:
                current_cluster.append(pt)
            else:
                clusters.append(current_cluster)
                current_cluster = [pt]
                
        if current_cluster:
            clusters.append(current_cluster)

        # A keypress usually has multiple points (slowdown/pause)
        # Filter out noise (e.g., clusters with too few points)
        valid_clusters = [c for c in clusters if len(c) >= 2]
        return valid_clusters

    def infer_word(self, gaze_points):
        """
        Infers the typed word from the raw 2D gaze points.
        """
        clusters = self.extract_keypress_clusters(gaze_points)
        inferred_word = ""

        for cluster in clusters:
            # Calculate the centroid of the cluster
            avg_x = sum(p[0] for p in cluster) / len(cluster)
            avg_y = sum(p[1] for p in cluster) / len(cluster)

            # Infer the key
            inferred_key = get_key_from_pos(avg_x, avg_y)
            if inferred_key:
                inferred_word += inferred_key

        return inferred_word
