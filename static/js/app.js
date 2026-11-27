let trendsChart = null;

function updateClock() {
  const now = new Date();
  const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  const clockEl = document.getElementById('clock-display');
  if (clockEl) clockEl.textContent = timeStr;
}

function initTrendsChart() {
  const ctx = document.getElementById('trendsChart').getContext('2d');
  trendsChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: [],
      datasets: [
        {
          label: 'Temp (°C)',
          data: [],
          borderColor: '#ef4444',
          backgroundColor: 'transparent',
          borderWidth: 2,
          tension: 0.35,
          pointRadius: 0
        },
        {
          label: 'Moisture (%)',
          data: [],
          borderColor: '#10b981',
          backgroundColor: 'transparent',
          borderWidth: 2,
          tension: 0.35,
          pointRadius: 0
        },
        {
          label: 'Humidity (%)',
          data: [],
          borderColor: '#3b82f6',
          backgroundColor: 'transparent',
          borderWidth: 2,
          borderDash: [4, 4],
          tension: 0.35,
          pointRadius: 0
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: { mode: 'index', intersect: false }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { font: { size: 10 }, color: '#94a3b8', maxTicksLimit: 6 }
        },
        y: {
          grid: { color: '#f1f5f9' },
          ticks: { font: { size: 10 }, color: '#94a3b8' },
          min: 10,
          max: 105
        }
      }
    }
  });
}

async function fetchTelemetry() {
  try {
    const res = await fetch('/api/telemetry');
    const data = await res.json();
    renderDashboard(data);
  } catch (err) {
    console.error('Telemetry fetch failed:', err);
  }
}

function renderDashboard(data) {
  const { current, vision, fusion, actuators, history, actions } = data;

  // 1. Metric Cards
  document.getElementById('val-temp').textContent = current.temperature.toFixed(1);
  document.getElementById('val-hum').textContent = current.humidity.toFixed(1);
  document.getElementById('val-moisture').textContent = current.soil_moisture.toFixed(1);
  document.getElementById('val-lux').textContent = current.light_lux;
  document.getElementById('val-ph').textContent = current.soil_ph.toFixed(2);

  // 2. Vision Inference
  document.getElementById('current-leaf-img').src = vision.image;
  const speciesEl = document.getElementById('leaf-species-val');
  if (speciesEl && vision.leaf_species) {
    speciesEl.textContent = vision.leaf_species;
  }
  document.getElementById('cnn-prediction').textContent = vision.disease_name;
  document.getElementById('cnn-conf-bar').style.width = `${vision.disease_confidence}%`;
  document.getElementById('cnn-conf-val').textContent = `${vision.disease_confidence}%`;

  document.getElementById('weed-found-val').textContent = vision.weeds_found ? 'Yes' : 'No';
  document.getElementById('weed-conf-bar').style.width = `${vision.weed_confidence}%`;
  document.getElementById('weed-conf-val').textContent = `${vision.weed_confidence}%`;

  // 3. Adaptive Fusion Gauge
  const score = fusion.composite_score;
  document.getElementById('fusion-score').textContent = score.toFixed(2);

  const meter = document.getElementById('gauge-meter');
  const circumference = 264;
  const offset = circumference - (circumference * score);
  meter.style.strokeDashoffset = offset;

  const actionBtn = document.getElementById('action-badge');
  actionBtn.textContent = fusion.action;
  actionBtn.className = `action-btn ${fusion.action.toLowerCase()}`;
  document.getElementById('action-reason').textContent = fusion.reason;

  if (fusion.action === 'SPRAY') {
    meter.style.stroke = '#ef4444';
  } else if (fusion.action === 'ALERT') {
    meter.style.stroke = '#f59e0b';
  } else {
    meter.style.stroke = '#10b981';
  }

  // Active Model Weights
  const w = fusion.weights;
  document.getElementById('w-disease-bar').style.width = `${w.disease}%`;
  document.getElementById('w-disease-val').textContent = `${w.disease}%`;

  document.getElementById('w-weed-bar').style.width = `${w.weed}%`;
  document.getElementById('w-weed-val').textContent = `${w.weed}%`;

  document.getElementById('w-env-bar').style.width = `${w.env}%`;
  document.getElementById('w-env-val').textContent = `${w.env}%`;

  document.getElementById('w-temporal-bar').style.width = `${w.temporal}%`;
  document.getElementById('w-temporal-val').textContent = `${w.temporal}%`;

  // 4. Actuators
  const pumpToggle = document.getElementById('pump-toggle');
  const sprayerToggle = document.getElementById('sprayer-toggle');
  
  pumpToggle.checked = actuators.water_pump;
  document.getElementById('pump-status-label').textContent = `Status: ${actuators.water_pump ? 'ON' : 'OFF'}`;

  sprayerToggle.checked = actuators.sprayer_valve;
  document.getElementById('sprayer-status-label').textContent = `Status: ${actuators.sprayer_valve ? 'ON (Spraying)' : 'OFF'}`;

  document.getElementById('actuator-last-op').textContent = actuators.last_operation;

  // 5. Trends Chart
  if (trendsChart && history) {
    const labels = history.map(item => {
      const d = new Date(item.timestamp * 1000);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    });
    trendsChart.data.labels = labels;
    trendsChart.data.datasets[0].data = history.map(h => h.temperature);
    trendsChart.data.datasets[1].data = history.map(h => h.soil_moisture);
    trendsChart.data.datasets[2].data = history.map(h => h.humidity);
    trendsChart.update('none');
  }

  // 6. Action Decision History
  if (actions) {
    const tbody = document.getElementById('history-tbody');
    tbody.innerHTML = actions.map(act => {
      const d = new Date(act.timestamp * 1000);
      const timeStr = d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      const actClass = act.action.toLowerCase();
      return `
        <tr>
          <td>${timeStr}</td>
          <td><span class="badge-action ${actClass}">${act.action}</span></td>
          <td>${act.composite_score.toFixed(2)}</td>
        </tr>
      `;
    }).join('');
  }
}

// Event Listeners for Interactive Controls
function setupControls() {
  // Scenario Selection
  document.querySelectorAll('.btn-scenario').forEach(btn => {
    btn.addEventListener('click', async () => {
      document.querySelectorAll('.btn-scenario').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const scenario = btn.dataset.scenario;
      await fetch('/api/scenario', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario })
      });
      fetchTelemetry();
    });
  });

  // Mock Leaf Selection
  document.querySelectorAll('.btn-leaf').forEach(btn => {
    btn.addEventListener('click', async () => {
      document.querySelectorAll('.btn-leaf').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const leaf = btn.dataset.leaf;
      await fetch('/api/leaf', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ leaf })
      });
      fetchTelemetry();
    });
  });

  // Custom Leaf Photo Upload
  const uploadInput = document.getElementById('leaf-upload-input');
  const uploadHint = document.getElementById('upload-hint');
  if (uploadInput) {
    uploadInput.addEventListener('change', async (e) => {
      const file = e.target.files[0];
      if (!file) return;

      uploadHint.textContent = `Analyzing ${file.name}...`;
      document.querySelectorAll('.btn-leaf').forEach(b => b.classList.remove('active'));

      const formData = new FormData();
      formData.append('image', file);

      try {
        const res = await fetch('/api/upload', {
          method: 'POST',
          body: formData
        });
        const result = await res.json();
        if (result.success) {
          uploadHint.textContent = `Identified: ${result.vision.leaf_species}`;
          fetchTelemetry();
        } else {
          uploadHint.textContent = 'Upload failed. Try another image.';
        }
      } catch (err) {
        uploadHint.textContent = 'Error processing upload.';
      }
    });
  }

  // Live Camera Capture
  let activeStream = null;
  const cameraModal = document.getElementById('camera-modal');
  const cameraVideo = document.getElementById('camera-video');
  const btnOpenCamera = document.getElementById('btn-open-camera');
  const btnCloseCamera = document.getElementById('btn-close-camera');
  const btnSnapPhoto = document.getElementById('btn-snap-photo');
  const cameraCanvas = document.getElementById('camera-canvas');

  if (btnOpenCamera) {
    btnOpenCamera.addEventListener('click', async () => {
      try {
        cameraModal.style.display = 'flex';
        activeStream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: 'environment', width: { ideal: 640 }, height: { ideal: 480 } }
        });
        cameraVideo.srcObject = activeStream;
      } catch (err) {
        alert('Could not access device camera: ' + err.message);
        cameraModal.style.display = 'none';
      }
    });
  }

  function stopCamera() {
    if (activeStream) {
      activeStream.getTracks().forEach(t => t.stop());
      activeStream = null;
    }
    cameraModal.style.display = 'none';
  }

  if (btnCloseCamera) {
    btnCloseCamera.addEventListener('click', stopCamera);
  }

  if (btnSnapPhoto) {
    btnSnapPhoto.addEventListener('click', () => {
      if (!activeStream) return;

      cameraCanvas.width = cameraVideo.videoWidth || 640;
      cameraCanvas.height = cameraVideo.videoHeight || 480;
      const ctx = cameraCanvas.getContext('2d');
      ctx.drawImage(cameraVideo, 0, 0, cameraCanvas.width, cameraCanvas.height);

      cameraCanvas.toBlob(async (blob) => {
        stopCamera();
        if (!blob) return;

        uploadHint.textContent = 'Classifying captured snapshot...';
        document.querySelectorAll('.btn-leaf').forEach(b => b.classList.remove('active'));

        const formData = new FormData();
        formData.append('image', blob, 'camera_capture.jpg');

        try {
          const res = await fetch('/api/upload', {
            method: 'POST',
            body: formData
          });
          const result = await res.json();
          if (result.success) {
            uploadHint.textContent = `Identified: ${result.vision.leaf_species}`;
            fetchTelemetry();
          }
        } catch (err) {
          uploadHint.textContent = 'Camera snapshot processing failed.';
        }
      }, 'image/jpeg', 0.9);
    });
  }

  // Actuator Toggles
  document.getElementById('pump-toggle').addEventListener('change', async (e) => {
    await fetch('/api/actuators', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ device: 'pump', state: e.target.checked })
    });
    fetchTelemetry();
  });

  document.getElementById('sprayer-toggle').addEventListener('change', async (e) => {
    await fetch('/api/actuators', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ device: 'sprayer', state: e.target.checked })
    });
    fetchTelemetry();
  });

  // Calibration Buttons
  document.querySelectorAll('.btn-calib').forEach(btn => {
    btn.addEventListener('click', async () => {
      const model = btn.dataset.model;
      await fetch('/api/calibrate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model })
      });
      fetchTelemetry();
    });
  });
}

document.addEventListener('DOMContentLoaded', () => {
  initTrendsChart();
  setupControls();
  updateClock();
  setInterval(updateClock, 1000);
  fetchTelemetry();
  setInterval(fetchTelemetry, 2500);
});
