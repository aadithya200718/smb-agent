import api from './api';

export const analyticsService = {
  getOverview: async () => {
    const res = await api.get('/analytics/overview');
    return res.data?.data || res.data;
  },
  getOrdersByDay: async (days = 7) => {
    const res = await api.get('/analytics/orders-by-day', { params: { days } });
    return res.data?.data || res.data;
  },
  getTopItems: async () => {
    const res = await api.get('/analytics/top-items');
    return res.data?.data || res.data;
  }
};
