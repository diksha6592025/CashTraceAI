﻿/**
 * CashTrace AI — Geospatial Hotspot & Cash Mule Cluster Analytics Controller
 */

let hotspotMap = null;
let allHotspotsData = [];
let clusterMarkers = [];
let clusterCircles = [];

const SATELLITE_LAYER = L.tileLayer('https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', {
  maxZoom: 20,
  attribution: '© Google Earth'
});

const STREET_LAYER = L.tileLayer('https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}', {
  maxZoom: 20,
  attribution: '© Google Maps'
});

document.addEventListener('DOMContentLoaded', async () => {
  await initHotspotMap();
  await loadHotspotsData();
  setupHotspotFilters();
});

async function initHotspotMap() {
  const mapEl = document.getElementById('hotspot-map');
  if (!mapEl) return;

  hotspotMap = L.map('hotspot-map', {
    center: [21.1458, 79.0882],
    zoom: 12,
    layers: [SATELLITE_LAYER]
  });

  L.control.layers({
    '🛰️ Google Earth Satellite': SATELLITE_LAYER,
    '🗺️ Google Street Maps': STREET_LAYER
  }).addTo(hotspotMap);
}

async function loadHotspotsData() {
  const res = await API.get('/hotspots');
  if (!res.success || !res.hotspots) return;

  allHotspotsData = res.hotspots;
  const summary = res.summary;

  // 1. Populate 4 KPI Stat Cards
  const elTot = document.getElementById('kpi-hs-total');
  const elCrit = document.getElementById('kpi-hs-critical');
  const elEmg = document.getElementById('kpi-hs-emerging');
  const elDec = document.getElementById('kpi-hs-declining');

  if (elTot) elTot.innerText = summary.total_hotspots;
  if (elCrit) elCrit.innerText = summary.critical_count;
  if (elEmg) elEmg.innerText = summary.emerging_count;
  if (elDec) elDec.innerText = summary.declining_count;

  // 2. Render Map Clusters & ATM Risk Zones
  renderMapClusters(allHotspotsData);

  // 3. Render Ranking Table
  renderRankingTable(allHotspotsData);
}

function renderMapClusters(hotspots) {
  if (!hotspotMap) return;

  // Clear existing markers & circles
  clusterMarkers.forEach(m => hotspotMap.removeLayer(m));
  clusterCircles.forEach(c => hotspotMap.removeLayer(c));
  clusterMarkers = [];
  clusterCircles = [];

  hotspots.forEach(h => {
    const lat = h.latitude;
    const lon = h.longitude;
    const color = h.marker_color;
    const radius = Math.max(600, h.case_count * 50);

    // Glowing Density Circle
    const circle = L.circle([lat, lon], {
      radius: radius,
      color: color,
      fillColor: color,
      fillOpacity: 0.22,
      weight: 2,
      dashArray: '4, 4'
    }).addTo(hotspotMap);
    clusterCircles.push(circle);

    // Marker Pin
    const icon = L.divIcon({
      className: 'hotspot-pin',
      html: `
        <div style="
          background: ${color};
          width: 34px; height: 34px;
          border-radius: 50%;
          border: 2px solid #fff;
          display: flex; align-items: center; justify-content: center;
          color: #fff; font-size: 14px; font-weight: bold;
          box-shadow: 0 0 16px ${color};
        ">#${h.rank}</div>
      `,
      iconSize: [34, 34],
      iconAnchor: [17, 17]
    });

    const gEarthUrl = `https://earth.google.com/web/@${lat},${lon},300a,1200d,35y,0t,0r`;
    const gMapsUrl = `https://www.google.com/maps/search/?api=1&query=${lat},${lon}`;

    const marker = L.marker([lat, lon], { icon: icon }).addTo(hotspotMap);
    marker.bindPopup(`
      <div style="font-family:sans-serif; min-width:240px; color:#0f172a;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
          <span style="background:${color}; color:#fff; font-size:10px; font-weight:bold; padding:2px 6px; border-radius:3px;">${h.density_level}</span>
          <span style="font-size:12px; font-weight:bold; color:#1e293b;">Score: ${h.risk_score}/100</span>
        </div>
        <h4 style="margin:4px 0 2px; color:#0f172a; font-size:14px;">${h.area_name}</h4>
        <div style="font-size:11px; color:#475569; margin-bottom:6px;">🏛️ ${h.assigned_station}</div>
        
        <div style="background:#f1f5f9; padding:8px; border-radius:6px; margin-bottom:8px; font-size:11px; line-height:1.5;">
          • <strong>Logged Cases:</strong> ${h.case_count} (High Risk: ${h.high_risk_count})<br>
          • <strong>Total Loss:</strong> ₹${h.total_financial_loss.toLocaleString('en-IN')}<br>
          • <strong>Primary Crime:</strong> <span style="color:#2563eb; font-weight:bold;">${h.top_crime_type}</span><br>
          • <strong>Trend:</strong> ${h.trend}
        </div>

        <div style="font-size:10.5px; color:#334155; font-style:italic; margin-bottom:8px;">
          🛡️ <em>${h.recommended_action}</em>
        </div>

        <div style="display:flex; gap:6px;">
          <a href="${gMapsUrl}" target="_blank" style="flex:1; background:#2563eb; color:#fff; text-decoration:none; text-align:center; padding:5px; border-radius:4px; font-size:11px; font-weight:bold;">🗺️ Google Maps</a>
          <a href="${gEarthUrl}" target="_blank" style="flex:1; background:#0f172a; color:#38bdf8; text-decoration:none; text-align:center; padding:5px; border-radius:4px; font-size:11px; font-weight:bold;">🛰️ Google Earth</a>
        </div>
      </div>
    `);
    clusterMarkers.push(marker);
  });
}

function renderRankingTable(hotspots) {
  const tbody = document.getElementById('hotspots-table-tbody');
  if (!tbody) return;

  if (hotspots.length === 0) {
    tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; padding:24px; color:#94a3b8;">No matching hotspot zones found.</td></tr>';
    return;
  }

  tbody.innerHTML = hotspots.map(h => {
    const badgeBg = h.marker_color + '22';
    const gEarthUrl = `https://earth.google.com/web/@${h.latitude},${h.longitude},300a,1000d,35y,0t,0r`;

    return `
      <tr>
        <td style="font-family:var(--font-mono); font-weight:800; color:var(--officer-cyan); font-size:1.05rem;">#${h.rank}</td>
        <td>
          <div style="font-weight:700; color:#fff; font-size:0.92rem;">${h.area_name}</div>
          <div style="font-size:0.75rem; color:#94a3b8;">🏛️ ${h.assigned_station}</div>
        </td>
        <td><span style="color:#cbd5e1; font-size:0.82rem;">${h.city_precinct}</span></td>
        <td>
          <div style="display:flex; align-items:center; gap:8px;">
            <span style="font-weight:800; font-family:var(--font-mono); font-size:0.95rem; color:#fff;">${h.case_count}</span>
            <small style="color:#94a3b8; font-size:0.72rem;">cases</small>
          </div>
        </td>
        <td style="font-family:var(--font-mono); font-weight:700; color:#fca5a5;">₹${h.total_financial_loss.toLocaleString('en-IN')}</td>
        <td>
          <span style="color:var(--officer-cyan); font-weight:600; font-size:0.82rem;">${h.top_crime_type}</span>
          <div style="font-size:0.72rem; color:#94a3b8;">${h.trend}</div>
        </td>
        <td>
          <span class="badge" style="background:${badgeBg}; color:${h.marker_color}; border:1px solid ${h.marker_color}; font-size:0.72rem;">
            ${h.risk_score}/100 • ${h.density_code}
          </span>
        </td>
        <td>
          <div style="display:flex; gap:6px;">
            <button class="btn btn-secondary btn-sm" style="font-size:0.72rem; padding:4px 8px;" onclick="focusHotspotOnMap(${h.latitude}, ${h.longitude}, ${h.rank - 1})">📍 Map</button>
            <a href="${gEarthUrl}" target="_blank" class="btn btn-primary btn-sm" style="font-size:0.72rem; padding:4px 8px; text-decoration:none;">🛰️ 3D</a>
          </div>
        </td>
      </tr>
    `;
  }).join('');
}

function focusHotspotOnMap(lat, lon, markerIdx) {
  if (!hotspotMap) return;
  hotspotMap.flyTo([lat, lon], 15, { animate: true, duration: 1.2 });
  if (clusterMarkers[markerIdx]) {
    clusterMarkers[markerIdx].openPopup();
  }
  document.getElementById('hotspot-map').scrollIntoView({ behavior: 'smooth', block: 'center' });
}

function setupHotspotFilters() {
  const searchInput = document.getElementById('hs-filter-search');
  const riskSelect = document.getElementById('hs-filter-risk');

  const applyFilters = () => {
    let list = [...allHotspotsData];
    const q = (searchInput?.value || '').toLowerCase().trim();
    const rk = riskSelect?.value || 'ALL';

    if (q) {
      list = list.filter(h =>
        h.area_name.toLowerCase().includes(q) ||
        h.city_precinct.toLowerCase().includes(q) ||
        h.top_crime_type.toLowerCase().includes(q) ||
        h.assigned_station.toLowerCase().includes(q)
      );
    }

    if (rk !== 'ALL') {
      list = list.filter(h => h.density_code === rk);
    }

    renderRankingTable(list);
  };

  if (searchInput) searchInput.addEventListener('input', applyFilters);
  if (riskSelect) riskSelect.addEventListener('change', applyFilters);
}
