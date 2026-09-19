﻿/**
 * CashTrace AI — Officer Command Dashboard Master Controller
 */

let allComplaintsData = [];
let statusChartInstance = null;
let trendChartInstance = null;
let officerMapInstance = null;
let tacticalBufferCircle = null;
let tacticalSearchMarker = null;
let complaintMapMarkers = [];

document.addEventListener('DOMContentLoaded', async () => {
  await loadDashboardStatistics();
  await loadAnalyticsCharts('month');
  await loadComplaintsTable();
  await initTacticalOfficerMap();
  await loadActivityFeed();
  setupFilterHandlers();
});

// 1. Load 8 KPI Statistic Cards
async function loadDashboardStatistics() {
  const res = await API.get('/officer/dashboard-stats');
  if (res.success && res.stats) {
    const s = res.stats;
    const setIfExists = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.innerText = val;
    };

    setIfExists('kpi-total', s.total);
    setIfExists('kpi-new', s.new_cases);
    setIfExists('kpi-inv', s.under_investigation);
    setIfExists('kpi-solved', s.solved);
    setIfExists('kpi-pending', s.pending);
    setIfExists('kpi-closed', s.closed);
    setIfExists('kpi-high-risk', s.high_risk);
    setIfExists('kpi-today', s.today_cases);
    
    // Officer Workload
    setIfExists('wl-active-count', `${s.under_investigation} Active Cases`);
    setIfExists('wl-rate', s.resolution_rate);
  }
}

// 2. Load Chart.js Analytics Suite
async function loadAnalyticsCharts(period = 'month') {
  // Highlight period buttons
  document.querySelectorAll('.btn-period-toggle').forEach(btn => {
    if (btn.getAttribute('data-period') === period) {
      btn.classList.add('btn-primary');
      btn.classList.remove('btn-secondary');
    } else {
      btn.classList.remove('btn-primary');
      btn.classList.add('btn-secondary');
    }
  });

  const res = await API.get(`/officer/analytics-trends?period=${period}`);
  if (!res.success) return;

  // Doughnut Chart: Status Distribution with Click-to-Filter
  const ctxStatus = document.getElementById('chart-status-doughnut');
  if (ctxStatus) {
    if (statusChartInstance) statusChartInstance.destroy();
    statusChartInstance = new Chart(ctxStatus, {
      type: 'doughnut',
      data: {
        labels: Object.keys(res.status_distribution),
        datasets: [{
          data: Object.values(res.status_distribution),
          backgroundColor: ['#38bdf8', '#818cf8', '#10b981', '#64748b'],
          borderColor: '#111827',
          borderWidth: 2,
          hoverOffset: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        onClick: (evt, elements) => {
          if (elements && elements.length > 0) {
            const idx = elements[0].index;
            const label = Object.keys(res.status_distribution)[idx];
            let targetStatus = 'ALL';
            if (label.includes('New')) targetStatus = 'NEW';
            else if (label.includes('Investigation')) targetStatus = 'UNDER INVESTIGATION';
            else if (label.includes('Solved')) targetStatus = 'SOLVED';
            else if (label.includes('Closed')) targetStatus = 'CLOSED';

            const statusSelect = document.getElementById('filter-status');
            if (statusSelect) {
              statusSelect.value = targetStatus;
              statusSelect.dispatchEvent(new Event('input'));
              const compSection = document.getElementById('complaints-section');
              if (compSection) compSection.scrollIntoView({ behavior: 'smooth' });
            }
          }
        },
        plugins: {
          legend: { position: 'right', labels: { color: '#cbd5e1', font: { size: 11 } } },
          tooltip: {
            callbacks: {
              afterLabel: () => '👉 Click slice to filter cases'
            }
          }
        }
      }
    });
  }

  // Line Chart: Trend Over Time
  const ctxTrend = document.getElementById('chart-trend-line');
  if (ctxTrend) {
    if (trendChartInstance) trendChartInstance.destroy();
    trendChartInstance = new Chart(ctxTrend, {
      type: 'line',
      data: {
        labels: res.trend.labels,
        datasets: [{
          label: 'Logged Complaints',
          data: res.trend.values,
          borderColor: '#38bdf8',
          backgroundColor: 'rgba(56, 189, 248, 0.12)',
          fill: true,
          tension: 0.35,
          pointRadius: 4,
          pointHoverRadius: 6,
          pointBackgroundColor: '#38bdf8'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.04)' } },
          y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.04)' } }
        },
        plugins: { legend: { display: false } }
      }
    });
  }

  // Crime Type Category Bars (Clickable to Filter)
  const catContainer = document.getElementById('categories-progress-list');
  if (catContainer && res.categories) {
    catContainer.innerHTML = res.categories.map(c => `
      <div style="margin-bottom:10px; cursor:pointer;" onclick="filterByCrimeCategory('${c.name}')" title="Click to filter by ${c.name}">
        <div style="display:flex; justify-content:space-between; font-size:0.78rem; margin-bottom:3px;">
          <span style="color:#e2e8f0; font-weight:600;">${c.name}</span>
          <span style="color:var(--officer-cyan); font-family:var(--font-mono);">${c.count} (${c.pct})</span>
        </div>
        <div style="background:rgba(255,255,255,0.06); border-radius:999px; height:6px; overflow:hidden;">
          <div style="background:linear-gradient(90deg, #2563eb, #38bdf8); width:${c.pct}; height:100%;"></div>
        </div>
      </div>
    `).join('');
  }
}

function filterByCrimeCategory(crimeName) {
  const searchInp = document.getElementById('filter-search');
  if (searchInp) {
    searchInp.value = crimeName.split('&')[0].trim();
    searchInp.dispatchEvent(new Event('input'));
    const compSection = document.getElementById('complaints-section');
    if (compSection) compSection.scrollIntoView({ behavior: 'smooth' });
  }
}

// 3. Load All Complaints Table with Search & Filters
async function loadComplaintsTable() {
  const res = await API.get('/officer/complaints');
  if (res.success && res.complaints) {
    allComplaintsData = res.complaints;
    renderFilteredTable(allComplaintsData);
  }
}

function renderFilteredTable(data) {
  const tbody = document.getElementById('complaints-table-tbody');
  if (!tbody) return;

  if (data.length === 0) {
    tbody.innerHTML = '<tr><td colspan="9" style="text-align:center; padding:24px; color:#94a3b8;">No matching complaint records found.</td></tr>';
    return;
  }

  tbody.innerHTML = data.map(c => {
    const riskBadgeClass = c.risk_level === 'HIGH' ? 'badge-risk-high' : (c.risk_level === 'MEDIUM' ? 'badge-risk-medium' : 'badge-risk-low');
    const statusBadgeClass = c.status === 'SOLVED' || c.status === 'RESOLVED' ? 'badge-st-solved' : (c.status === 'UNDER INVESTIGATION' ? 'badge-st-investigation' : (c.status === 'PENDING' ? 'badge-st-pending' : 'badge-st-new'));

    return `
      <tr>
        <td style="font-family:var(--font-mono); font-weight:700; color:var(--officer-cyan);">${c.complaint_id}</td>
        <td style="font-size:0.75rem; color:#94a3b8;">${c.incident_date}</td>
        <td><strong style="color:#fff;">${c.citizen_name}</strong></td>
        <td style="font-family:var(--font-mono); font-size:0.78rem;">${c.masked_phone}</td>
        <td><span style="color:#e2e8f0; font-weight:600;">${c.crime_type}</span></td>
        <td>📍 ${c.location.split(',')[0]}</td>
        <td><span class="badge ${riskBadgeClass}">${c.risk_level}</span></td>
        <td><span class="badge ${statusBadgeClass}">${c.status}</span></td>
        <td>
          <div style="display:flex; gap:6px;">
            <button class="btn btn-secondary btn-sm" style="font-size:0.72rem; padding:4px 8px;" onclick="openCaseDossier('${c.complaint_id}')">👁️ View</button>
            <button class="btn btn-primary btn-sm" style="font-size:0.72rem; padding:4px 8px;" onclick="openStatusUpdateDialog('${c.complaint_id}', '${c.status}')">✏️ Status</button>
          </div>
        </td>
      </tr>
    `;
  }).join('');
}

function setupFilterHandlers() {
  const searchInp = document.getElementById('filter-search');
  const statusSelect = document.getElementById('filter-status');
  const riskSelect = document.getElementById('filter-risk');
  const crimeSelect = document.getElementById('filter-crime');
  const sortSelect = document.getElementById('filter-sort');

  const applyFilters = () => {
    let list = [...allComplaintsData];
    const q = (searchInp?.value || '').toLowerCase().trim();
    const st = statusSelect?.value || 'ALL';
    const rk = riskSelect?.value || 'ALL';
    const cr = crimeSelect?.value || 'ALL';
    const sort = sortSelect?.value || 'NEWEST';

    if (q) {
      list = list.filter(c => 
        c.complaint_id.toLowerCase().includes(q) ||
        c.citizen_name.toLowerCase().includes(q) ||
        c.location.toLowerCase().includes(q) ||
        c.crime_type.toLowerCase().includes(q)
      );
    }
    if (st !== 'ALL') list = list.filter(c => c.status === st);
    if (rk !== 'ALL') list = list.filter(c => c.risk_level === rk);
    if (cr !== 'ALL') list = list.filter(c => c.crime_type === cr);

    if (sort === 'NEWEST') list.sort((a, b) => b.id - a.id);
    if (sort === 'OLDEST') list.sort((a, b) => a.id - b.id);
    if (sort === 'HIGH_RISK') list.sort((a, b) => (b.amount || 0) - (a.amount || 0));

    renderFilteredTable(list);
  };

  [searchInp, statusSelect, riskSelect, crimeSelect, sortSelect].forEach(el => {
    if (el) el.addEventListener('input', applyFilters);
    if (el) el.addEventListener('change', applyFilters);
  });
}

// 4. View Case Dossier Modal
async function openCaseDossier(complaintId) {
  const res = await API.get(`/officer/complaint/${complaintId}`);
  if (!res.success) {
    alert('Could not load case dossier.');
    return;
  }

  const c = res.complaint;
  const p = res.predictive_analysis;
  const t = res.timeline;

  document.getElementById('md-cid').innerText = c.complaint_id;
  document.getElementById('md-name').innerText = c.citizen_name;
  document.getElementById('md-phone').innerText = c.citizen_phone;
  document.getElementById('md-email').innerText = c.citizen_email;
  document.getElementById('md-crime').innerText = c.crime_type;
  document.getElementById('md-amount').innerText = `₹${parseFloat(c.amount || 0).toLocaleString('en-IN')}`;
  document.getElementById('md-date').innerText = `${c.incident_date} at ${c.incident_time || '14:00'}`;
  document.getElementById('md-loc').innerText = c.location;
  document.getElementById('md-desc').innerText = c.description;

  document.getElementById('md-risk-score').innerText = `${p.risk_score}/100`;
  document.getElementById('md-risk-level').innerText = `${p.risk_level} RISK`;
  document.getElementById('md-risk-pattern').innerText = p.predicted_pattern;
  document.getElementById('md-risk-action').innerText = p.recommended_action;

  // Timeline
  const tlContainer = document.getElementById('md-timeline');
  if (tlContainer && t) {
    tlContainer.innerHTML = t.map(item => `
      <li class="activity-timeline-item">
        <div style="display:flex; justify-content:space-between; font-size:0.8rem;">
          <strong style="color:#fff;">${item.action_text}</strong>
          <span style="color:#94a3b8; font-size:0.72rem;">${item.timestamp}</span>
        </div>
        <div style="font-size:0.75rem; color:#cbd5e1;">Officer: ${item.officer_name}</div>
        ${item.remarks ? `<div style="font-size:0.72rem; color:#94a3b8; font-style:italic;">Note: ${item.remarks}</div>` : ''}
      </li>
    `).join('');
  }

  document.getElementById('caseDossierModal').classList.add('active');
  document.body.style.overflow = 'hidden';
}

function closeCaseDossier() {
  document.getElementById('caseDossierModal').classList.remove('active');
  document.body.style.overflow = 'auto';
}

// 5. Change Case Status Dialog
let activeUpdateComplaintId = null;

function openStatusUpdateDialog(complaintId, currentStatus) {
  activeUpdateComplaintId = complaintId;
  document.getElementById('st-modal-cid').innerText = complaintId;
  document.getElementById('st-modal-current').innerText = currentStatus;
  document.getElementById('st-modal-select').value = currentStatus;
  document.getElementById('st-modal-remarks').value = '';
  document.getElementById('statusUpdateModal').classList.add('active');
}

function closeStatusUpdateDialog() {
  document.getElementById('statusUpdateModal').classList.remove('active');
}

async function confirmStatusUpdate() {
  const newSt = document.getElementById('st-modal-select').value;
  const remarks = document.getElementById('st-modal-remarks').value.trim();

  const res = await API.post('/officer/update-status', {
    complaint_id: activeUpdateComplaintId,
    status: newSt,
    remarks: remarks || 'Status updated via command console.'
  });

  if (res.success) {
    closeStatusUpdateDialog();
    await loadDashboardStatistics();
    await loadComplaintsTable();
    await loadAnalyticsCharts('month');
    await loadActivityFeed();
    alert(`Case ${activeUpdateComplaintId} successfully updated to '${newSt}'.`);
  }
}

// 6. Tactical Map & Google Earth/Maps Launchers
async function initTacticalOfficerMap() {
  const mapEl = document.getElementById('tactical-map');
  if (!mapEl) return;

  const GOOGLE_EARTH_SATELLITE = L.tileLayer('https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', { maxZoom: 20, attribution: '© Google Earth' });
  const GOOGLE_STREETS = L.tileLayer('https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}', { maxZoom: 20, attribution: '© Google Maps' });

  officerMapInstance = L.map('tactical-map', { center: [21.1458, 79.0882], zoom: 13, layers: [GOOGLE_EARTH_SATELLITE] });
  L.control.layers({ "🛰️ Google Earth Satellite": GOOGLE_EARTH_SATELLITE, "🗺️ Google Street Maps": GOOGLE_STREETS }).addTo(officerMapInstance);

  const res = await API.get('/complaints/map');
  if (res.success && res.markers) {
    res.markers.forEach(m => {
      const color = m.risk_level === 'HIGH' ? '#ef4444' : (m.risk_level === 'MEDIUM' ? '#f59e0b' : '#10b981');
      const icon = L.divIcon({
        className: 'custom-pin',
        html: `<div style="background:${color}; width:28px; height:28px; border-radius:50%; border:2px solid #fff; display:flex; align-items:center; justify-content:center; color:#fff; font-size:12px; font-weight:bold; box-shadow:0 0 12px ${color};">⚠️</div>`,
        iconSize: [28, 28], iconAnchor: [14, 14]
      });

      const gEarthUrl = `https://earth.google.com/web/@${m.latitude},${m.longitude},300a,1000d,35y,0t,0r`;

      const marker = L.marker([m.latitude, m.longitude], { icon: icon }).addTo(officerMapInstance);
      marker.bindPopup(`
        <div style="font-family:sans-serif; min-width:210px; color:#0f172a;">
          <h4 style="margin:0 0 4px; color:#1e1b4b;">${m.id} — ${m.crime_type}</h4>
          <div style="font-size:12px; color:#475569;">📍 ${m.general_area} • ${m.approx_date}</div>
          <div style="margin:4px 0 8px; font-size:11px;">Status: <strong>${m.status}</strong> | Risk: <strong style="color:${color};">${m.risk_level}</strong></div>
          <div style="display:flex; flex-direction:column; gap:4px;">
            <button onclick="openCaseDossier('${m.id}')" style="background:#2563eb; color:#fff; border:none; padding:5px 8px; border-radius:4px; font-size:11px; cursor:pointer; width:100%;">Inspect Case Dossier</button>
            <a href="${gEarthUrl}" target="_blank" style="background:#0f172a; color:#38bdf8; text-decoration:none; text-align:center; padding:4px 8px; border-radius:4px; font-size:11px; font-weight:bold;">🛰️ Open in Google Earth 3D</a>
          </div>
        </div>
      `);
      complaintMapMarkers.push(marker);
    });
  }

  // Location Geocoding & Hotspot Analysis
  const searchInput = document.getElementById('map-search-input');
  if (searchInput) {
    const doSearch = async () => {
      const query = searchInput.value.trim();
      if (!query) return;
      try {
        const geoRes = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&countrycodes=in&limit=1`);
        const data = await geoRes.json();
        if (data && data.length > 0) {
          const lat = parseFloat(data[0].lat);
          const lon = parseFloat(data[0].lon);
          selectLocationOnMap(lat, lon, query);
        }
      } catch (e) {
        console.error(e);
      }
    };

    searchInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') doSearch();
    });
  }
}

async function selectLocationOnMap(lat, lon, queryName) {
  if (!officerMapInstance) return;
  officerMapInstance.flyTo([lat, lon], 15, { duration: 1.2 });

  if (tacticalSearchMarker) officerMapInstance.removeLayer(tacticalSearchMarker);
  tacticalSearchMarker = L.marker([lat, lon]).addTo(officerMapInstance).bindPopup(`<b>📍 ${queryName}</b>`).openPopup();

  // 800-Meter Tactical Buffer
  if (tacticalBufferCircle) officerMapInstance.removeLayer(tacticalBufferCircle);
  tacticalBufferCircle = L.circle([lat, lon], {
    radius: 800,
    color: '#ef4444',
    fillColor: '#ef4444',
    fillOpacity: 0.15,
    weight: 2,
    dashArray: '6, 6'
  }).addTo(officerMapInstance);

  // Update Location Analysis Box
  const analysisRes = await API.get(`/officer/location-analysis?location=${encodeURIComponent(queryName)}`);
  if (analysisRes.success) {
    const setIf = (id, val) => { const el = document.getElementById(id); if (el) el.innerText = val; };
    setIf('loc-title', `📍 Hotspot Analysis: ${queryName}`);
    setIf('loc-total', analysisRes.total_complaints);
    setIf('loc-common', analysisRes.most_common_crime);
    setIf('loc-high', analysisRes.high_risk_cases);
    setIf('loc-solved', analysisRes.solved_cases);
    setIf('loc-inv', analysisRes.under_investigation);
    setIf('loc-trend', analysisRes.trend);

    // Direct Google Maps & Google Earth Launchers
    const btnGmaps = document.getElementById('btn-open-gmaps');
    const btnGearth = document.getElementById('btn-open-gearth');
    if (btnGmaps) btnGmaps.href = `https://www.google.com/maps/search/?api=1&query=${lat},${lon}`;
    if (btnGearth) btnGearth.href = `https://earth.google.com/web/@${lat},${lon},300a,1000d,35y,0t,0r`;
  }
}

// 7. Activity Feed
async function loadActivityFeed() {
  const res = await API.get('/officer/activity-feed');
  const feedEl = document.getElementById('recent-activity-list');
  if (feedEl && res.success && res.activities) {
    feedEl.innerHTML = res.activities.map(a => `
      <div style="padding:10px 0; border-bottom:1px solid rgba(255,255,255,0.05); font-size:0.78rem;">
        <div style="color:#fff; font-weight:600;">${a.action_text}</div>
        <div style="display:flex; justify-content:space-between; color:#94a3b8; font-size:0.72rem; margin-top:2px;">
          <span>Officer: ${a.officer_name}</span>
          <span>${a.timestamp}</span>
        </div>
      </div>
    `).join('');
  }
}
