﻿/**
 * CashTrace AI — AI Predictive Analytics & Chart.js Visualization Engine
 */

let chartInstance1 = null;
let chartInstance2 = null;
let chartInstance3 = null;

async function loadPredictionDashboard() {
  const container = document.getElementById('predictions-list');
  if (!container) return;

  const res = await API.get('/predictions');
  if (res.success && res.predictions) {
    container.innerHTML = res.predictions.map(p => {
      const riskClass = p.risk_level.toLowerCase();
      return `
        <div class="cyber-card" style="border-left: 4px solid ${p.risk_score >= 80 ? 'var(--danger-red)' : 'var(--warning-orange)'}; margin-bottom:16px;">
          <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:10px;">
            <div>
              <span class="badge badge-${riskClass}">${p.risk_level} RISK</span>
              <h3 style="margin-top:6px; color:#fff; font-size:1.25rem;">${p.area}</h3>
              <div style="color:#94a3b8; font-size:0.85rem;">Primary Vector: <strong style="color:#f87171;">${p.crime_type}</strong> | Forecast Horizon: <strong>${p.forecast_period}</strong></div>
            </div>
            <div style="text-align:right;">
              <div style="font-size:2.2rem; font-weight:800; color:var(--accent-cyan); font-family:var(--font-mono);">${p.risk_score}<span style="font-size:1rem; color:#94a3b8;">/100</span></div>
              <small style="color:var(--text-muted); font-size:0.75rem; text-transform:uppercase;">AI Historical Risk Index</small>
            </div>
          </div>

          <div style="margin-top:14px; background:rgba(30,41,59,0.7); padding:14px; border-radius:8px; border-left:3px solid var(--accent-cyan);">
            <strong style="color:#e2e8f0; font-size:0.82rem; display:block; margin-bottom:4px;">🏧 PREDICTED CASH WITHDRAWAL HOTSPOT (SIH-26184):</strong>
            <div style="color:var(--accent-cyan); font-weight:700; font-size:0.95rem;">${p.predicted_withdrawal_hotspot}</div>
          </div>

          <div style="margin-top:14px; font-size:0.82rem; color:#94a3b8;">
            <strong style="color:#cbd5e1; display:block; margin-bottom:6px;">EXPLAINABLE AI (XAI) DECISION DRIVERS:</strong>
            <ul style="padding-left:18px; margin:0; line-height:1.6;">
              ${p.explainable_reasons.map(r => `<li><span style="color:var(--accent-cyan);">✓</span> ${r}</li>`).join('')}
            </ul>
          </div>
        </div>
      `;
    }).join('');
  }
}

async function renderPredictionCharts() {
  const res = await API.get('/predictions/trends');
  if (!res.success) return;

  // Chart Palette
  const colors = ['#38bdf8', '#ef4444', '#f59e0b', '#10b981', '#a855f7', '#6366f1'];

  // 1. Crime Type Distribution (Doughnut Chart)
  const ctx1 = document.getElementById('chart-crime-types');
  if (ctx1) {
    if (chartInstance1) chartInstance1.destroy();
    chartInstance1 = new Chart(ctx1, {
      type: 'doughnut',
      data: {
        labels: Object.keys(res.crime_type_distribution),
        datasets: [{
          data: Object.values(res.crime_type_distribution),
          backgroundColor: colors,
          borderColor: '#0f172a',
          borderWidth: 2
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'right',
            labels: { color: '#cbd5e1', font: { size: 11 } }
          }
        }
      }
    });
  }

  // 2. Regional Incident Density (Bar Chart)
  const ctx2 = document.getElementById('chart-areas');
  if (ctx2) {
    if (chartInstance2) chartInstance2.destroy();
    chartInstance2 = new Chart(ctx2, {
      type: 'bar',
      data: {
        labels: Object.keys(res.area_distribution),
        datasets: [{
          label: 'Logged Complaints',
          data: Object.values(res.area_distribution),
          backgroundColor: 'rgba(56, 189, 248, 0.75)',
          borderColor: '#38bdf8',
          borderWidth: 1,
          borderRadius: 4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { ticks: { color: '#94a3b8', font: { size: 10 } }, grid: { color: 'rgba(255,255,255,0.05)' } },
          y: { ticks: { color: '#94a3b8', stepSize: 1 }, grid: { color: 'rgba(255,255,255,0.05)' } }
        },
        plugins: {
          legend: { display: false }
        }
      }
    });
  }

  // 3. Hourly Cash Withdrawal Risk Curve (Line Chart)
  const ctx3 = document.getElementById('chart-hourly-trend');
  if (ctx3 && res.hourly_withdrawal_curve) {
    if (chartInstance3) chartInstance3.destroy();
    chartInstance3 = new Chart(ctx3, {
      type: 'line',
      data: {
        labels: Object.keys(res.hourly_withdrawal_curve),
        datasets: [{
          label: 'ATM Cash-Out Probability (%)',
          data: Object.values(res.hourly_withdrawal_curve),
          borderColor: '#ef4444',
          backgroundColor: 'rgba(239, 68, 68, 0.15)',
          fill: true,
          tension: 0.4,
          pointRadius: 4,
          pointBackgroundColor: '#ef4444'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } },
          y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' }, max: 100 }
        },
        plugins: {
          legend: { labels: { color: '#cbd5e1' } }
        }
      }
    });
  }
}
