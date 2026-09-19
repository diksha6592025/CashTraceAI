/* CashTrace AI — Alerts page loader */
document.addEventListener('DOMContentLoaded', async () => {
  const host = document.getElementById('alerts-log-container');
  if (!host) return;
  const esc = v => String(v ?? '').replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
  host.innerHTML = '<div class="empty">Loading alerts…</div>';
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 10000);
    const res = await fetch('/api/alerts', {
      method:'GET', credentials:'same-origin', cache:'no-store',
      headers:{'Accept':'application/json'}, signal:controller.signal
    });
    clearTimeout(timeout);
    let data = {};
    try { data = await res.json(); } catch (_) {}
    if (!res.ok || !data.success) throw new Error(data.message || `HTTP ${res.status}`);
    const alerts = Array.isArray(data.alerts) ? data.alerts : [];
    if (!alerts.length) {
      host.innerHTML = '<div class="empty">No intelligence alerts recorded yet.</div>';
      return;
    }
    host.innerHTML = alerts.map(a => `
      <article class="alert-log-item">
        <div class="alert-log-top"><span class="badge">${esc(a.severity || 'INFO')}</span><small class="muted">${esc(a.created_at || a.timestamp || '')}</small></div>
        <h3>${esc(a.title || a.alert_type || 'Intelligence alert')}</h3>
        <p class="muted">${esc(a.message || 'No additional message available.')}</p>
        ${a.area ? `<span class="muted alert-area">${esc(a.area)}</span>` : ''}
      </article>`).join('');
  } catch (e) {
    host.innerHTML = `<div class="empty">Unable to load alerts. ${esc(e.name === 'AbortError' ? 'Request timed out.' : e.message)}</div>`;
  }
});
