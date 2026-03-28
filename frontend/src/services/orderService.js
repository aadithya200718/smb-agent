import api from './api';

export const orderService = {
  getOrders: async (filters) => {
    const res = await api.get('/orders', { params: filters });
    return res.data?.data || res.data;
  },
  getOrderById: async (id) => {
    const res = await api.get(`/orders/${id}`);
    return res.data?.data || res.data;
  },
  updateOrderStatus: async (id, status) => {
    const res = await api.put(`/orders/${id}/status`, { status });
    return res.data?.data || res.data;
  },
  getOrderStats: async () => {
    const res = await api.get('/orders/stats');
    return res.data?.data || res.data;
  }
};
