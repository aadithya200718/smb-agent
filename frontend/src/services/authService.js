import api from './api';

function normalizeUser(raw = {}) {
  const businessName = raw.business_name || raw.name || '';
  const email = raw.email || raw.owner_email || '';

  return {
    ...raw,
    business_name: businessName,
    name: raw.name || businessName,
    email,
  };
}

export const authService = {
  login: async (email, password) => {
    const response = await api.post('/auth/login', { email, password });
    const payload = response.data?.data || {};

    if (payload.access_token) {
      localStorage.setItem('token', payload.access_token);
    }
    if (payload.business_id) {
      localStorage.setItem('business_id', payload.business_id);
    }

    return payload;
  },

  register: async (email, password, businessName, phone) => {
    const response = await api.post('/auth/register', {
      email,
      password,
      business_name: businessName,
      phone
    });

    return response.data?.data || response.data;
  },

  getCurrentUser: async () => {
    const response = await api.get('/auth/me');
    const user = normalizeUser(response.data?.data || {});

    if (user.business_id) {
      localStorage.setItem('business_id', user.business_id);
    }

    return user;
  },

  logout: () => {
    localStorage.removeItem('token');
    localStorage.removeItem('business_id');
  }
};
