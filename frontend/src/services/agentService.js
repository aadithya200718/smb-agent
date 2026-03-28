import api from './api';

export const agentService = {
  getStatus: async () => {
    const res = await api.get('/agent/status');
    return res.data;
  },
  getTraces: async (params) => {
    const res = await api.get('/agent/traces', { params });
    return res.data;
  },
  getMetrics: async (timeRange = '7d') => {
    const res = await api.get('/agent/metrics', { params: { range: timeRange } });
    return res.data;
  },
  getPerformance: async () => {
    const res = await api.get('/agent/performance');
    return res.data;
  },
  updateConfiguration: async (config) => {
    const res = await api.put('/agent/configuration', config);
    return res.data;
  }
};
