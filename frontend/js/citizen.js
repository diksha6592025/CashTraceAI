﻿/**
 * CashTrace AI - Complainant Portal Client Logic
 * Geolocation Auto-Detection, Nearest Police Station Finder, & Filing.
 */

document.addEventListener('DOMContentLoaded', () => {
  const geoBtn = document.getElementById('btn-get-location');
  const latInput = document.getElementById('latitude');
  const lonInput = document.getElementById('longitude');
  const locInput = document.getElementById('location');
  const stationInfoBox = document.getElementById('nearest-station-card');

  // 1. Geolocation API Auto-Detection
  if (geoBtn) {
    geoBtn.addEventListener('click', () => {
      if (!navigator.geolocation) {
        alert('Geolocation is not supported by your browser.');
        return;
      }
      geoBtn.innerText = 'Detecting GPS Coordinates...';
      navigator.geolocation.getCurrentPosition(
        async (pos) => {
          const lat = pos.coords.latitude;
          const lon = pos.coords.longitude;
          latInput.value = lat.toFixed(6);
          lonInput.value = lon.toFixed(6);
          geoBtn.innerText = '✓ Location Acquired';

          // Fetch Nearest Police Station
          fetchNearestPoliceStation(lat, lon);
        },
        (err) => {
          console.warn('Geolocation denied, using default coordinates (Nagpur Center).');
          latInput.value = '21.145800';
          lonInput.value = '79.088200';
          geoBtn.innerText = 'Default Location Set';
          fetchNearestPoliceStation(21.1458, 79.0882);
        }
      );
    });
  }

  async function fetchNearestPoliceStation(lat, lon) {
    const res = await API.get(`/nearby-station?lat=${lat}&lon=${lon}`);
    if (res.success && res.nearest_station && stationInfoBox) {
      const s = res.nearest_station;
      stationInfoBox.style.display = 'block';
      stationInfoBox.innerHTML = `
        <h4 style="color:#38bdf8; margin-bottom:6px;">📍 Assigned Police Station</h4>
        <div style="font-weight:700; font-size:1.05rem;">${s.station_name}</div>
        <div style="color:#94a3b8; font-size:0.85rem; margin-top:4px;">Address: ${s.address}</div>
        <div style="color:#94a3b8; font-size:0.85rem;">Phone: ☎ ${s.phone}</div>
        <div style="color:#10b981; font-size:0.85rem; font-weight:600; margin-top:4px;">📏 Approx Distance: ${s.distance_km} km</div>
      `;
    }
  }

  // 2. Complaint Form Submission
  const complaintForm = document.getElementById('complaint-form');
  if (complaintForm) {
    complaintForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const submitBtn = complaintForm.querySelector('button[type="submit"]');
      submitBtn.disabled = true;
      submitBtn.innerText = 'Submitting Complaint...';

      const payload = Object.fromEntries(new FormData(complaintForm).entries());
      const res = await API.post('/complaints', payload);

      if (res.success) {
        document.getElementById('form-container').style.display = 'none';
        const successBox = document.getElementById('submission-success-box');
        successBox.style.display = 'block';
        document.getElementById('generated-complaint-id').innerText = res.complaint_id;
      } else {
        alert(res.message || 'Error submitting complaint.');
        submitBtn.disabled = false;
        submitBtn.innerText = 'Submit Cyber Crime Complaint';
      }
    });
  }
});
