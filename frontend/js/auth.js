/**
 * CashTrace AI — Client-Side Authentication & Session Controller
 */

document.addEventListener('DOMContentLoaded', async () => {
  // 1. Attach Logout Event Handlers
  document.querySelectorAll('.btn-logout').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      try {
        await API.post('/logout', {});
      } catch (err) {
        console.warn('Logout error:', err);
      }
      window.location.href = '/index.html';
    });
  });

  // 2. Fetch and Update User Identity
  try {
    const res = await API.get('/auth/status');
    if (res && res.authenticated) {
      const nameDisplays = document.querySelectorAll('#user-name-display, .user-name-target');
      nameDisplays.forEach(el => {
        el.innerText = res.name || (res.role === 'officer' ? 'Officer' : 'Complainant');
      });

      const badgeDisplays = document.querySelectorAll('#user-badge-display, .user-badge-target');
      badgeDisplays.forEach(el => {
        if (res.badge) el.innerText = res.badge;
      });
    }
  } catch (err) {
    console.debug('Auth status check note:', err);
  }
});
