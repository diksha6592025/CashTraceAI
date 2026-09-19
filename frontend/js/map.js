﻿/**
 * CashTrace AI — Tactical GIS & Google Earth Mapping Engine with Real-World Geocoding
 */

let activeMap = null;
let currentSearchMarker = null;
let directionPolyline = null;
let bufferCircle = null;

// Tile Layers
const GOOGLE_EARTH_SATELLITE = L.tileLayer('https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', {
  maxZoom: 20,
  attribution: '© Google Earth'
});

const GOOGLE_STREET_MAP = L.tileLayer('https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}', {
  maxZoom: 20,
  attribution: '© Google Maps'
});

const ESRI_SATELLITE = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
  maxZoom: 19,
  attribution: '© Esri Satellite'
});

// Custom Map Markers
const createCustomIcon = (iconChar, bgColor, pulse = false) => {
  return L.divIcon({
    className: 'custom-div-icon',
    html: `
      <div style="
        background: ${bgColor};
        width: 34px; height: 34px;
        border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        color: #fff; font-size: 16px; font-weight: bold;
        border: 2px solid #fff;
        box-shadow: 0 0 15px ${bgColor};
        ${pulse ? 'animation: markerPulse 1.5s infinite;' : ''}
      ">${iconChar}</div>
    `,
    iconSize: [34, 34],
    iconAnchor: [17, 17]
  });
};

const ICONS = {
  citizen: createCustomIcon('📍', '#38bdf8', true),
  police: createCustomIcon('👮', '#2563eb'),
  crime: createCustomIcon('⚠️', '#ef4444'),
  atm: createCustomIcon('🏧', '#f59e0b')
};

// -------------------------------------------------------------
// 1. CITIZEN MAP INITIALIZATION
// -------------------------------------------------------------
async function initCitizenMap() {
  const mapContainer = document.getElementById('map');
  if (!mapContainer) return;

  activeMap = L.map('map', {
    center: [21.1458, 79.0882], // Default: Nagpur Center
    zoom: 13,
    layers: [GOOGLE_EARTH_SATELLITE]
  });

  L.control.layers({
    "🛰️ Google Earth Hybrid Satellite": GOOGLE_EARTH_SATELLITE,
    "🗺️ Google Street Map": GOOGLE_STREET_MAP,
    "🌍 Esri Satellite": ESRI_SATELLITE
  }).addTo(activeMap);

  // Load All Police Stations
  const stationsRes = await API.get('/police-stations');
  const stations = (stationsRes.success && stationsRes.stations) ? stationsRes.stations : [];

  stations.forEach(s => {
    const lat = parseFloat(s.latitude);
    const lon = parseFloat(s.longitude);
    const googleEarthUrl = `https://earth.google.com/web/@${lat},${lon},300a,800d,35y,0t,0r`;
    const googleMapsDirUrl = `https://www.google.com/maps/dir/?api=1&destination=${lat},${lon}`;

    const marker = L.marker([lat, lon], { icon: ICONS.police }).addTo(activeMap);
    marker.bindPopup(`
      <div style="color:#0f172a; font-family:sans-serif; min-width:220px;">
        <h4 style="margin:0 0 4px; color:#1e1b4b;">👮 ${s.station_name}</h4>
        <div style="font-size:12px; color:#475569; margin-bottom:6px;">${s.address}</div>
        <div style="font-size:12px; margin-bottom:8px;"><strong>📞 Helpline:</strong> <a href="tel:${s.phone}">${s.phone}</a></div>
        <div style="display:flex; gap:6px; flex-direction:column;">
          <a href="${googleMapsDirUrl}" target="_blank" style="background:#2563eb; color:#fff; padding:5px 8px; border-radius:4px; text-decoration:none; text-align:center; font-size:11px; font-weight:bold;">🧭 Get Driving Directions</a>
          <a href="${googleEarthUrl}" target="_blank" style="background:#0f172a; color:#38bdf8; padding:5px 8px; border-radius:4px; text-decoration:none; text-align:center; font-size:11px; font-weight:bold;">🛰️ Open in Google Earth 3D ↗</a>
        </div>
      </div>
    `);
  });

  // Handle Search Input & Geocoding
  setupLocationSearch(activeMap, async (lat, lon, displayName) => {
    findAndRouteNearestStations(lat, lon, stations, displayName);
  });
}

// Compute distances to all stations and draw direct route
function findAndRouteNearestStations(userLat, userLon, stations, locationName) {
  if (!stations.length) return;

  // Calculate distance for all stations
  const ranked = stations.map(s => {
    const d = calculateHaversine(userLat, userLon, parseFloat(s.latitude), parseFloat(s.longitude));
    return { ...s, distance_km: d };
  }).sort((a, b) => a.distance_km - b.distance_km);

  const nearest = ranked[0];

  // Draw or update Route Line
  if (directionPolyline) activeMap.removeLayer(directionPolyline);
  directionPolyline = L.polyline([
    [userLat, userLon],
    [parseFloat(nearest.latitude), parseFloat(nearest.longitude)]
  ], {
    color: '#38bdf8',
    weight: 4,
    dashArray: '8, 8',
    opacity: 0.9
  }).addTo(activeMap);

  // Update UI Sidebar List
  const resultsBox = document.getElementById('search-results-list');
  if (resultsBox) {
    const googleEarthUser = `https://earth.google.com/web/@${userLat},${userLon},300a,800d,35y,0t,0r`;
    const googleMapsDir = `https://www.google.com/maps/dir/?api=1&origin=${userLat},${userLon}&destination=${nearest.latitude},${nearest.longitude}`;

    resultsBox.innerHTML = `
      <div class="cyber-card" style="margin-bottom:12px; border-color:var(--accent-cyan); background:rgba(56,189,248,0.08); padding:14px;">
        <div style="font-size:0.75rem; color:var(--accent-cyan); font-weight:bold;">YOUR SEARCHED LOCATION:</div>
        <div style="color:#fff; font-size:0.95rem; font-weight:bold; margin-bottom:4px;">${locationName}</div>
        <div style="font-size:0.75rem; color:#94a3b8; margin-bottom:10px;">GPS: ${userLat.toFixed(4)}, ${userLon.toFixed(4)}</div>
        <div style="display:flex; gap:8px; flex-wrap:wrap;">
          <a href="${googleEarthUser}" target="_blank" class="btn btn-secondary btn-sm" style="font-size:0.75rem;">🛰️ Open Your Location in Google Earth 3D ↗</a>
          <a href="${googleMapsDir}" target="_blank" class="btn btn-primary btn-sm" style="font-size:0.75rem;">🧭 Navigate to Nearest Police Station ↗</a>
        </div>
      </div>

      <h4 style="color:#fff; margin-bottom:8px; font-size:0.9rem;">📍 Nearby Police Stations Ranked by Distance:</h4>
      ${ranked.map((s, idx) => `
        <div style="background:#1e293b; padding:10px 14px; border-radius:8px; margin-bottom:8px; border-left:3px solid ${idx === 0 ? 'var(--accent-cyan)' : 'var(--border-color)'};">
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <strong style="color:#fff; font-size:0.88rem;">${idx === 0 ? '⭐ [NEAREST] ' : ''}${s.station_name}</strong>
            <span style="color:var(--accent-cyan); font-weight:bold; font-family:var(--font-mono); font-size:0.82rem;">${s.distance_km.toFixed(2)} km</span>
          </div>
          <div style="font-size:0.78rem; color:#94a3b8; margin:2px 0 6px;">${s.address} • Phone: ${s.phone}</div>
          <div style="display:flex; gap:6px;">
            <a href="https://www.google.com/maps/dir/?api=1&origin=${userLat},${userLon}&destination=${s.latitude},${s.longitude}" target="_blank" style="font-size:0.75rem; color:var(--accent-cyan);">🧭 Get Directions</a>
            <span style="color:#64748b;">•</span>
            <a href="https://earth.google.com/web/@${s.latitude},${s.longitude},300a,800d,35y,0t,0r" target="_blank" style="font-size:0.75rem; color:#94a3b8;">🛰️ Google Earth View</a>
          </div>
        </div>
      `).join('')}
    `;
  }
}

// -------------------------------------------------------------
// 2. OFFICER MAP INITIALIZATION (Similar Incidents + Buffers)
// -------------------------------------------------------------
async function initOfficerMap() {
  const mapContainer = document.getElementById('map');
  if (!mapContainer) return;

  activeMap = L.map('map', {
    center: [21.1458, 79.0882],
    zoom: 13,
    layers: [GOOGLE_EARTH_SATELLITE]
  });

  L.control.layers({
    "🛰️ Google Earth Hybrid Satellite": GOOGLE_EARTH_SATELLITE,
    "🗺️ Google Street Map": GOOGLE_STREET_MAP,
    "🌍 Esri Satellite": ESRI_SATELLITE
  }).addTo(activeMap);

  // Load All Complaints / Incidents
  const res = await API.get('/complaints/map');
  const markers = (res.success && res.markers) ? res.markers : [];

  markers.forEach(c => {
    const lat = parseFloat(c.latitude);
    const lon = parseFloat(c.longitude);
    const earthUrl = `https://earth.google.com/web/@${lat},${lon},300a,1000d,35y,0t,0r`;

    const marker = L.marker([lat, lon], { icon: ICONS.crime }).addTo(activeMap);
    marker.bindPopup(`
      <div style="color:#0f172a; font-family:sans-serif; min-width:240px;">
        <div style="background:#ef4444; color:#fff; font-size:10px; font-weight:bold; padding:2px 6px; border-radius:3px; display:inline-block; margin-bottom:4px;">INCIDENT ${c.id}</div>
        <h4 style="margin:2px 0 4px; color:#1e1b4b;">⚠️ ${c.crime_type}</h4>
        <div style="font-size:12px; color:#475569;">📍 ${c.general_area} • ${c.approx_date}</div>
        <div style="font-size:12px; margin:4px 0 8px;"><strong>Status:</strong> <span style="color:#2563eb; font-weight:bold;">${c.status}</span></div>
        <div style="display:flex; flex-direction:column; gap:4px;">
          <a href="/similar_incidents.html?id=${c.id}" class="btn btn-secondary btn-sm" style="background:#0f172a; color:#38bdf8; text-decoration:none; padding:4px 8px; font-size:11px; text-align:center; border-radius:4px; font-weight:bold;">🔍 Find Similar Crime Vectors</a>
          <a href="${earthUrl}" target="_blank" style="background:#2563eb; color:#fff; text-decoration:none; padding:4px 8px; font-size:11px; text-align:center; border-radius:4px; font-weight:bold;">🛰️ Open in Google Earth 3D ↗</a>
        </div>
      </div>
    `);
  });

  // Setup Officer Geocoding Search
  setupLocationSearch(activeMap, (lat, lon, displayName) => {
    renderOfficerTacticalSearch(lat, lon, displayName, markers);
  });
}

function renderOfficerTacticalSearch(lat, lon, displayName, markers) {
  // Draw 800-meter tactical buffer radius
  if (bufferCircle) activeMap.removeLayer(bufferCircle);
  bufferCircle = L.circle([lat, lon], {
    radius: 800,
    color: '#ef4444',
    fillColor: '#ef4444',
    fillOpacity: 0.18,
    weight: 2,
    dashArray: '6, 6'
  }).addTo(activeMap);

  // Find all similar incidents within 5km radius
  const nearbyIncidents = markers.map(m => {
    const d = calculateHaversine(lat, lon, parseFloat(m.latitude), parseFloat(m.longitude));
    return { ...m, distance_km: d };
  }).filter(m => m.distance_km <= 5.0).sort((a, b) => a.distance_km - b.distance_km);

  const resultsBox = document.getElementById('search-results-list');
  if (resultsBox) {
    const earthUrl = `https://earth.google.com/web/@${lat},${lon},300a,1200d,35y,0t,0r`;
    resultsBox.innerHTML = `
      <div class="cyber-card" style="margin-bottom:12px; border-color:var(--danger-red); background:rgba(239,68,68,0.08); padding:14px;">
        <div style="font-size:0.75rem; color:var(--danger-red); font-weight:bold;">TACTICAL ZONE INSPECTION:</div>
        <div style="color:#fff; font-size:0.95rem; font-weight:bold; margin-bottom:4px;">${displayName}</div>
        <div style="font-size:0.75rem; color:#94a3b8; margin-bottom:8px;">800m Threat Buffer Active | ${nearbyIncidents.length} Related Crime Cases Found</div>
        <a href="${earthUrl}" target="_blank" class="btn btn-primary btn-sm" style="font-size:0.75rem; width:100%; text-align:center;">🛰️ Launch Tactical View in Google Earth 3D ↗</a>
      </div>

      <h4 style="color:#fff; margin-bottom:8px; font-size:0.9rem;">⚠️ Similar Incidents in this Perimeter:</h4>
      ${nearbyIncidents.length === 0 ? '<p style="color:var(--text-muted); font-size:0.8rem;">No recent incidents logged in this immediate 5km radius.</p>' : 
        nearbyIncidents.map(c => `
          <div style="background:#1e293b; padding:10px 14px; border-radius:8px; margin-bottom:8px; border-left:3px solid var(--danger-red);">
            <div style="display:flex; justify-content:space-between;">
              <strong style="color:#fff; font-size:0.85rem;">${c.crime_type}</strong>
              <span style="color:var(--danger-red); font-weight:bold; font-size:0.8rem;">${c.distance_km.toFixed(2)} km away</span>
            </div>
            <div style="font-size:0.75rem; color:#94a3b8; margin:2px 0 6px;">📍 ${c.general_area} • Status: ${c.status}</div>
            <a href="https://earth.google.com/web/@${c.latitude},${c.longitude},300a,800d,35y,0t,0r" target="_blank" style="font-size:0.75rem; color:var(--accent-cyan);">🛰️ Inspect Incident Point in Google Earth 3D →</a>
          </div>
        `).join('')}
    `;
  }
}

// -------------------------------------------------------------
// 3. UNIVERSAL REAL-WORLD GEOCODING SEARCH BAR
// -------------------------------------------------------------
function setupLocationSearch(map, onLocationSelected) {
  const input = document.getElementById('search-location-input');
  const suggestionsBox = document.getElementById('search-suggestions');
  if (!input) return;

  let debounceTimer = null;

  input.addEventListener('input', () => {
    clearTimeout(debounceTimer);
    const query = input.value.trim();
    if (query.length < 3) {
      if (suggestionsBox) suggestionsBox.style.display = 'none';
      return;
    }

    debounceTimer = setTimeout(async () => {
      try {
        const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&countrycodes=in&limit=5`;
        const res = await fetch(url);
        const results = await res.json();

        if (suggestionsBox) {
          if (results.length === 0) {
            suggestionsBox.innerHTML = '<div style="padding:8px 12px; font-size:0.8rem; color:#94a3b8;">No locations found.</div>';
          } else {
            suggestionsBox.innerHTML = results.map(item => `
              <div class="search-item" style="padding:8px 12px; cursor:pointer; font-size:0.82rem; border-bottom:1px solid rgba(255,255,255,0.06); color:#cbd5e1;" 
                   data-lat="${item.lat}" data-lon="${item.lon}" data-name="${item.display_name}">
                📍 <strong>${item.display_name.split(',')[0]}</strong> <small style="color:#94a3b8;">${item.display_name.split(',').slice(1, 3).join(',')}</small>
              </div>
            `).join('');

            suggestionsBox.querySelectorAll('.search-item').forEach(el => {
              el.addEventListener('click', () => {
                const lat = parseFloat(el.getAttribute('data-lat'));
                const lon = parseFloat(el.getAttribute('data-lon'));
                const name = el.getAttribute('data-name');

                input.value = name.split(',')[0];
                suggestionsBox.style.display = 'none';

                // Move Map
                map.flyTo([lat, lon], 15, { animate: true, duration: 1.5 });

                // Place Pin
                if (currentSearchMarker) map.removeLayer(currentSearchMarker);
                currentSearchMarker = L.marker([lat, lon], { icon: ICONS.citizen }).addTo(map);
                currentSearchMarker.bindPopup(`<b>📍 ${name.split(',')[0]}</b><br><small>${name}</small>`).openPopup();

                if (onLocationSelected) onLocationSelected(lat, lon, name);
              });
            });
          }
          suggestionsBox.style.display = 'block';
        }
      } catch (e) {
        console.error('Geocoding error:', e);
      }
    }, 350);
  });

  // GPS Auto-detect Button
  const gpsBtn = document.getElementById('btn-detect-gps');
  if (gpsBtn) {
    gpsBtn.onclick = () => {
      if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition((pos) => {
          const lat = pos.coords.latitude;
          const lon = pos.coords.longitude;
          input.value = `My Live Location (${lat.toFixed(4)}, ${lon.toFixed(4)})`;
          map.flyTo([lat, lon], 15);
          if (currentSearchMarker) map.removeLayer(currentSearchMarker);
          currentSearchMarker = L.marker([lat, lon], { icon: ICONS.citizen }).addTo(map).bindPopup('<b>📍 Your Live Location</b>').openPopup();
          if (onLocationSelected) onLocationSelected(lat, lon, 'Your Live GPS Location');
        }, () => {
          alert('Could not access live GPS. Please enter location in search bar.');
        });
      }
    };
  }
}

// Haversine Distance Calculation (km)
function calculateHaversine(lat1, lon1, lat2, lon2) {
  const R = 6371;
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
            Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
            Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}
