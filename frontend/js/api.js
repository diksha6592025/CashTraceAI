/**
 * CashTrace AI — Universal API Helper
 */

const API = {
  async get(endpoint) {
    try {
      const res = await fetch(`/api${endpoint}`);
      if (!res.ok) {
        return { success: false, authenticated: false };
      }
      return await res.json();
    } catch (err) {
      console.warn(`API GET error on ${endpoint}:`, err);
      return { success: false, authenticated: false };
    }
  },

  async post(endpoint, data = {}) {
    try {
      const res = await fetch(`/api${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
      });
      return await res.json();
    } catch (err) {
      console.warn(`API POST error on ${endpoint}:`, err);
      return { success: false, message: 'Could not connect to server.' };
    }
  }
};
