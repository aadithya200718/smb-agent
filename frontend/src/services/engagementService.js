import api from './api';

function getBusinessId() {
  return localStorage.getItem('business_id') || 'BIZ001';
}

export const engagementService = {
  getCampaigns: async () => {
    const res = await api.get('/engagement/events', { params: { business_id: getBusinessId() } });
    return res.data?.events || res.data;
  },
  createCampaign: async (data) => {
    const payload = {
      ...data,
      business_id: data?.business_id || getBusinessId(),
    };
    const res = await api.post('/engagement/campaigns', payload);
    return res.data;
  },
  getAnalytics: async () => {
    const res = await api.get('/engagement/analytics', { params: { business_id: getBusinessId() } });
    return res.data;
  },
  getScheduled: async () => {
    const res = await api.get('/engagement/scheduled', { params: { business_id: getBusinessId() } });
    return res.data;
  },
  optOutUser: async (phone) => {
    const res = await api.post('/engagement/opt-out', null, { params: { phone } });
    return res.data;
  }
};
