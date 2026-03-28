import api from './api';

export const menuService = {
  getMenu: async () => {
    const res = await api.get('/menu');
    return res.data?.data || res.data;
  },
  createMenuItem: async (data) => {
    const res = await api.post('/menu', data);
    return res.data?.data || res.data;
  },
  updateMenuItem: async (id, data) => {
    const res = await api.put(`/menu/${id}`, data);
    return res.data?.data || res.data;
  },
  deleteMenuItem: async (id) => {
    const res = await api.delete(`/menu/${id}`);
    return res.data?.data || res.data;
  },
  toggleAvailability: async (id, available) => {
    const res = await api.patch(`/menu/${id}/availability`, { available });
    return res.data?.data || res.data;
  }
};
