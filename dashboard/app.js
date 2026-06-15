// app.js

// 1. Keyboard Layout matching keyboard.py
const KEYBOARD_LAYOUT = {
  'q': [0, 2], 'w': [1, 2], 'e': [2, 2], 'r': [3, 2], 't': [4, 2], 'y': [5, 2], 'u': [6, 2], 'i': [7, 2], 'o': [8, 2], 'p': [9, 2],
  'a': [0.5, 1], 's': [1.5, 1], 'd': [2.5, 1], 'f': [3.5, 1], 'g': [4.5, 1], 'h': [5.5, 1], 'j': [6.5, 1], 'k': [7.5, 1], 'l': [8.5, 1],
  'z': [1, 0], 'x': [2, 0], 'c': [3, 0], 'v': [4, 0], 'b': [5, 0], 'n': [6, 0], 'm': [7, 0],
  'enter': [9, 0],
  'space': [4.5, -1]
};

// 2. Map coordinates to closest key
function getKeyFromPos(x, y, threshold = 0.6) {
  let closestKey = null;
  let minDist = Infinity;
  for (const [key, [kx, ky]] of Object.entries(KEYBOARD_LAYOUT)) {
    const dist = Math.hypot(kx - x, ky - y);
    if (dist < minDist) {
      minDist = dist;
      closestKey = key;
    }
  }
  return minDist <= threshold ? closestKey : null;
}

// 3. Telemetry Generator (mimics create_dataset.py)
function generateTelemetry(word, noiseLevel = 0.15) {
  const fullTelemetry = [];
  let timestamp = 1620000000.000;
  const timeStep = 1.0 / 72.0; // 72 Hz

  for (let char of word.toLowerCase()) {
    if (KEYBOARD_LAYOUT[char]) {
      const [targetX, targetY] = KEYBOARD_LAYOUT[char];
      
      // Simulate Travel Points (is_typing = false)
      const numTravelPoints = Math.floor(Math.random() * 11) + 5; // 5 to 15
      for (let i = 0; i < numTravelPoints; i++) {
        // Wider movement towards the target
        const px = targetX + (Math.random() * 2 - 1);
        const py = targetY + (Math.random() * 2 - 1);
        const pz = Math.random() * 0.2 + 0.5;
        fullTelemetry.push({
          timestamp: timestamp.toFixed(3),
          x: px,
          y: py,
          z: pz,
          isTyping: false,
          targetChar: 'None'
        });
        timestamp += timeStep;
      }

      // Simulate Dwell Points (is_typing = true)
      const numDwellPoints = Math.floor(Math.random() * 6) + 3; // 3 to 8
      for (let i = 0; i < numDwellPoints; i++) {
        const px = targetX + (Math.random() * (noiseLevel * 2) - noiseLevel);
        const py = targetY + (Math.random() * (noiseLevel * 2) - noiseLevel);
        const pz = Math.random() * 0.05 + 0.5;
        fullTelemetry.push({
          timestamp: timestamp.toFixed(3),
          x: px,
          y: py,
          z: pz,
          isTyping: true,
          targetChar: char
        });
        timestamp += timeStep;
      }
    }
  }
  return fullTelemetry;
}

// 4. Attacker Logic (mimics attacker.py)
class SnoopfingerAttacker {
  constructor(clusterThreshold = 0.8) {
    this.clusterThreshold = clusterThreshold;
  }

  extractKeypressClusters(gazePoints) {
    if (!gazePoints || gazePoints.length === 0) return [];

    const clusters = [];
    let currentCluster = [gazePoints[0]];

    for (let i = 1; i < gazePoints.length; i++) {
      const pt = gazePoints[i];
      const lastPt = currentCluster[currentCluster.length - 1];
      const dist = Math.hypot(pt[0] - lastPt[0], pt[1] - lastPt[1]);

      if (dist < this.clusterThreshold) {
        currentCluster.push(pt);
      } else {
        clusters.push(currentCluster);
        currentCluster = [pt];
      }
    }
    if (currentCluster.length > 0) {
      clusters.push(currentCluster);
    }

    // A valid keypress cluster usually has multiple points (gaze pause)
    return clusters.filter(c => c.length >= 2);
  }

  inferWord(gazePoints, keyMapThreshold = 0.6) {
    const clusters = this.extractKeypressClusters(gazePoints);
    let inferredWord = "";
    const centroids = [];

    for (const cluster of clusters) {
      const avgX = cluster.reduce((sum, p) => sum + p[0], 0) / cluster.length;
      const avgY = cluster.reduce((sum, p) => sum + p[1], 0) / cluster.length;
      centroids.push([avgX, avgY]);

      const inferredKey = getKeyFromPos(avgX, avgY, keyMapThreshold);
      if (inferredKey) {
        inferredWord += inferredKey;
      }
    }
    return { inferredWord, clusters, centroids };
  }
}

// 5. Defender Logic (mimics defender.py)
class CASOMMiddleware {
  constructor(noiseScale = 1.5, useRounding = false) {
    this.noiseScale = noiseScale;
    this.useRounding = useRounding;
  }

  obfuscatePoints(telemetryPoints) {
    return telemetryPoints.map(pt => {
      // Background apps only receive obfuscated coordinates if typing is active
      if (pt.isTyping) {
        let ox, oy;
        if (this.useRounding) {
          ox = Math.round(pt.x);
          oy = Math.round(pt.y);
        } else {
          // Add random uniform noise matching defender.py
          ox = pt.x + (Math.random() * (this.noiseScale * 2) - this.noiseScale);
          oy = pt.y + (Math.random() * (this.noiseScale * 2) - this.noiseScale);
        }
        return { ...pt, x: ox, y: oy };
      }
      return { ...pt }; // Travel points pass through raw
    });
  }
}

// --- RENDERING & INTERACTIVE MANAGEMENT ---

let currentTelemetry = [];
let animationFrameId = null;

// Initialize Keyboard Layouts
function initKeyboard(containerId) {
  const container = document.getElementById(containerId);
  container.innerHTML = '';

  const minX = -0.7;
  const maxX = 9.7;
  const minY = -1.5;
  const maxY = 2.5;

  for (const [key, [kx, ky]] of Object.entries(KEYBOARD_LAYOUT)) {
    const keyEl = document.createElement('div');
    keyEl.className = 'key-element';
    keyEl.textContent = key === 'space' ? '___' : key === 'enter' ? 'enter ↵' : key;
    keyEl.dataset.key = key;

    if (key === 'space') keyEl.classList.add('space-key');
    if (key === 'enter') keyEl.classList.add('enter-key');

    const leftPercent = ((kx - minX) / (maxX - minX)) * 100;
    const topPercent = ((maxY - ky) / (maxY - minY)) * 100;

    keyEl.style.left = `${leftPercent}%`;
    keyEl.style.top = `${topPercent}%`;

    // Sizing
    if (key === 'space') {
      keyEl.style.width = '30%';
      keyEl.style.height = '16%';
    } else if (key === 'enter') {
      keyEl.style.width = '12%';
      keyEl.style.height = '16%';
    } else {
      keyEl.style.width = '8%';
      keyEl.style.height = '16%';
    }

    container.appendChild(keyEl);
  }
}

// Map logical layout to canvas pixels
function getCanvasCoords(x, y, canvas) {
  const minX = -0.7;
  const maxX = 9.7;
  const minY = -1.5;
  const maxY = 2.5;

  const px = ((x - minX) / (maxX - minX)) * canvas.width;
  const py = ((maxY - y) / (maxY - minY)) * canvas.height;
  return [px, py];
}

// Drawing Gaze Data
function drawGaze(canvas, points, centroids, colorTheme, activeIndex = -1) {
  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  if (points.length === 0) return;

  const limit = activeIndex === -1 ? points.length : activeIndex;

  // 1. Draw Travel Path & Gaze Path
  ctx.beginPath();
  let first = true;
  for (let i = 0; i < limit; i++) {
    const pt = points[i];
    const [px, py] = getCanvasCoords(pt.x, pt.y, canvas);
    if (first) {
      ctx.moveTo(px, py);
      first = false;
    } else {
      ctx.lineTo(px, py);
    }
  }
  ctx.strokeStyle = colorTheme.path;
  ctx.lineWidth = 1.5;
  ctx.stroke();

  // 2. Draw Individual Points
  for (let i = 0; i < limit; i++) {
    const pt = points[i];
    const [px, py] = getCanvasCoords(pt.x, pt.y, canvas);

    ctx.beginPath();
    if (pt.isTyping) {
      ctx.arc(px, py, 4, 0, 2 * Math.PI);
      ctx.fillStyle = colorTheme.dwell;
    } else {
      ctx.arc(px, py, 2.5, 0, 2 * Math.PI);
      ctx.fillStyle = colorTheme.travel;
    }
    ctx.fill();
  }

  // 3. Draw Centroids (if animation is done or near complete)
  if (activeIndex === -1 || activeIndex >= points.length - 2) {
    for (const [cx, cy] of centroids) {
      const [px, py] = getCanvasCoords(cx, cy, canvas);
      
      // Draw crosshair or circle representing isolated keystroke
      ctx.beginPath();
      ctx.arc(px, py, 8, 0, 2 * Math.PI);
      ctx.strokeStyle = colorTheme.centroid;
      ctx.lineWidth = 2;
      ctx.stroke();
      
      ctx.beginPath();
      ctx.arc(px, py, 2, 0, 2 * Math.PI);
      ctx.fillStyle = colorTheme.centroid;
      ctx.fill();
    }
  }
}

// Manage Interactive Simulation Run
function runSimulation() {
  if (animationFrameId) {
    cancelAnimationFrame(animationFrameId);
  }

  const targetWord = document.getElementById('target-word').value.trim() || 'foxenter';
  const noiseScale = parseFloat(document.getElementById('noise-scale').value);
  const clusterThreshold = parseFloat(document.getElementById('cluster-threshold').value);
  const keyMapThreshold = parseFloat(document.getElementById('key-map-threshold').value);
  const useRounding = document.getElementById('defense-mode').checked;

  // Step 1: Generate Raw Telemetry
  currentTelemetry = generateTelemetry(targetWord);

  // Step 2: Extract typing points for Attacker on raw data
  const rawTypingPoints = currentTelemetry.filter(p => p.isTyping).map(p => [p.x, p.y]);
  const attacker = new SnoopfingerAttacker(clusterThreshold);
  const rawResult = attacker.inferWord(rawTypingPoints, keyMapThreshold);

  // Step 3: Run CASOM Defense on telemetry
  const defender = new CASOMMiddleware(noiseScale, useRounding);
  const protectedTelemetry = defender.obfuscatePoints(currentTelemetry);
  const protectedTypingPoints = protectedTelemetry.filter(p => p.isTyping).map(p => [p.x, p.y]);
  const protectedResult = attacker.inferWord(protectedTypingPoints, keyMapThreshold);

  // Update Statistics UI
  document.getElementById('stat-target').textContent = targetWord;
  document.getElementById('stat-raw-word').textContent = rawResult.inferredWord || '[None]';
  document.getElementById('stat-protected-word').textContent = protectedResult.inferredWord || '[None]';

  const rawSuccess = rawResult.inferredWord.toLowerCase() === targetWord.toLowerCase();
  const protectedSuccess = protectedResult.inferredWord.toLowerCase() === targetWord.toLowerCase();

  // Attack status formatting
  const rawStatus = document.getElementById('stat-raw-status');
  if (rawSuccess) {
    rawStatus.textContent = '100% Successful';
    rawStatus.className = 'stat-value red';
  } else {
    rawStatus.textContent = 'Failed';
    rawStatus.className = 'stat-value';
  }

  const protectedStatus = document.getElementById('stat-protected-status');
  if (protectedSuccess) {
    protectedStatus.textContent = 'Successful';
    protectedStatus.className = 'stat-value red';
  } else {
    protectedStatus.textContent = 'Defeated (0%)';
    protectedStatus.className = 'stat-value green';
  }

  // Set up canvases
  const rawCanvas = document.getElementById('raw-canvas');
  const protCanvas = document.getElementById('prot-canvas');
  rawCanvas.width = rawCanvas.clientWidth;
  rawCanvas.height = rawCanvas.clientHeight;
  protCanvas.width = protCanvas.clientWidth;
  protCanvas.height = protCanvas.clientHeight;

  const redTheme = {
    path: 'rgba(239, 68, 68, 0.4)',
    dwell: '#ef4444',
    travel: 'rgba(148, 163, 184, 0.5)',
    centroid: '#b91c1c'
  };

  const blueTheme = {
    path: 'rgba(37, 99, 235, 0.3)',
    dwell: '#2563eb',
    travel: 'rgba(148, 163, 184, 0.5)',
    centroid: '#1d4ed8'
  };

  // Animate Gaze Playback
  let activeIndex = 0;
  const speed = 2; // draw 2 points per frame

  function animate() {
    activeIndex += speed;
    if (activeIndex <= currentTelemetry.length) {
      drawGaze(rawCanvas, currentTelemetry, rawResult.centroids, redTheme, activeIndex);
      drawGaze(protCanvas, protectedTelemetry, protectedResult.centroids, blueTheme, activeIndex);
      
      // Light up keyboard keys as the gaze is near them
      highlightKeys(currentTelemetry[Math.min(activeIndex, currentTelemetry.length - 1)], 'raw-keyboard');
      highlightKeys(protectedTelemetry[Math.min(activeIndex, protectedTelemetry.length - 1)], 'prot-keyboard');

      animationFrameId = requestAnimationFrame(animate);
    } else {
      // Draw final state
      drawGaze(rawCanvas, currentTelemetry, rawResult.centroids, redTheme, -1);
      drawGaze(protCanvas, protectedTelemetry, protectedResult.centroids, blueTheme, -1);
      clearKeyHighlights('raw-keyboard');
      clearKeyHighlights('prot-keyboard');
      cancelAnimationFrame(animationFrameId);
    }
  }

  animate();
}

function highlightKeys(point, keyboardId) {
  clearKeyHighlights(keyboardId);
  if (!point || !point.isTyping) return;

  const key = getKeyFromPos(point.x, point.y, 0.6);
  if (key) {
    const keyEl = document.querySelector(`#${keyboardId} .key-element[data-key="${key}"]`);
    if (keyEl) {
      keyEl.classList.add('active-keypress');
    }
  }
}

function clearKeyHighlights(keyboardId) {
  const keys = document.querySelectorAll(`#${keyboardId} .key-element`);
  keys.forEach(k => k.classList.remove('active-keypress'));
}

// Initial Loading Setup
window.addEventListener('load', () => {
  initKeyboard('raw-keyboard');
  initKeyboard('prot-keyboard');

  // Sliders visual updating
  const sliders = [
    { id: 'noise-scale', valId: 'noise-scale-val' },
    { id: 'cluster-threshold', valId: 'cluster-threshold-val' },
    { id: 'key-map-threshold', valId: 'key-map-threshold-val' }
  ];

  sliders.forEach(s => {
    const el = document.getElementById(s.id);
    const valEl = document.getElementById(s.valId);
    el.addEventListener('input', () => {
      valEl.textContent = el.value;
    });
  });

  // Run initial simulation
  runSimulation();
});

// Re-run simulation when clicking Run
document.getElementById('btn-run').addEventListener('click', runSimulation);

// Re-initialize canvases on window resize
window.addEventListener('resize', () => {
  const rawCanvas = document.getElementById('raw-canvas');
  const protCanvas = document.getElementById('prot-canvas');
  if (rawCanvas && protCanvas) {
    rawCanvas.width = rawCanvas.clientWidth;
    rawCanvas.height = rawCanvas.clientHeight;
    protCanvas.width = protCanvas.clientWidth;
    protCanvas.height = protCanvas.clientHeight;
    runSimulation();
  }
});
