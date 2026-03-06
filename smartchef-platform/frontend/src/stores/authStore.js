import { create } from 'zustand';
import api from '../services/api';

export const useAuthStore = create((set) => ({
  token: localStorage.getItem('smartchef_token') || null,
  user: null,

  login: async (username, password) => {
    const res = await api.post('/auth/login', { username, password });
    const { access_token } = res.data;
    localStorage.setItem('smartchef_token', access_token);
    set({ token: access_token });
    const me = await api.get('/auth/me');
    set({ user: me.data });
  },

  fetchMe: async () => {
    try {
      const res = await api.get('/auth/me');
      set({ user: res.data });
    } catch {
      set({ token: null, user: null });
      localStorage.removeItem('smartchef_token');
    }
  },

  logout: () => {
    localStorage.removeItem('smartchef_token');
    set({ token: null, user: null });
    window.location.href = '/login';
  },
}));
