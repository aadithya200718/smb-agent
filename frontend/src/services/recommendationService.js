import api from './api';

export const recommendationService = {
  getStats: async () => {
    const res = await api.get('/recommendations/stats');
    return res.data;
  },
  getTopRecommended: async (limit = 10) => {
    const res = await api.get('/recommendations/top', { params: { limit } });
    return res.data;
  },
  getROI: async (timeRange = '30d') => {
    const res = await api.get('/recommendations/roi', { params: { range: timeRange } });
    return res.data;
  }
};
