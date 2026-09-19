﻿/**
 * CashTrace AI - Privacy-Preserving Similar Incident Viewer
 */

async function loadSimilarIncidents(complaintId) {
  const container = document.getElementById('similar-incidents-container');
  if (!container) return;

  container.innerHTML = '<div style="color:#94a3b8;">Analyzing historical complaint vectors...</div>';
  const res = await API.get(`/similar-incidents/${complaintId}`);

  if (res.found && res.results.length > 0) {
    container.innerHTML = `
      <div class="alert-box alert-info" style="margin-bottom:20px;">
        <div>
          <strong>${res.total_similar} Similar Historical Patterns Detected</strong><br>
          <span style="font-size:0.8rem;">${res.disclaimer}</span>
        </div>
      </div>
      <div class="grid-2">
        ${res.results.map(r => `
          <div class="cyber-card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <span style="font-family:var(--font-mono); color:#94a3b8; font-size:0.8rem;">${r.anonymized_id}</span>
              <span class="badge badge-assigned">${r.similarity_level} (${r.similarity_score}%)</span>
            </div>
            <h4 style="margin:10px 0 4px; color:#38bdf8;">${r.crime_type}</h4>
            <div style="font-size:0.85rem; color:#cbd5e1;">📍 General Area: ${r.general_area}</div>
            <div style="font-size:0.85rem; color:#94a3b8;">📅 Approximate Date: ${r.approximate_date}</div>
            <div style="font-size:0.85rem; color:#94a3b8;">📏 Proximity: ~${r.approx_distance_km} km away</div>
          </div>
        `).join('')}
      </div>
    `;
  } else {
    container.innerHTML = `
      <div class="cyber-card" style="text-align:center; padding:40px;">
        <h4 style="color:#94a3b8;">No direct historical cluster detected for this complaint vector.</h4>
        <p style="font-size:0.85rem; color:#64748b; margin-top:6px;">Your report has been logged to help protect citizens in your precinct.</p>
      </div>
    `;
  }
}
