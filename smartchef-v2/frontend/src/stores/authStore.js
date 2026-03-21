import { create } from 'zustand';
import { authApi, TOKEN_KEY, REFRESH_TOKEN_KEY } from '../services/api';

const useAuthStore = create((set, get) => ({
  user: null,
  token: localStorage.getItem(TOKEN_KEY) || null,
  refreshToken: localStorage.getItem(REFRESH_TOKEN_KEY) || null,
  capabilities: [],
  isAuthenticated: !!localStorage.getItem(TOKEN_KEY),

  login: async (username, password) => {
    const data = await authApi.login(username, password);
    const { access_token, refresh_token, user } = data;

    localStorage.setItem(TOKEN_KEY, access_token);
    if (refresh_token) {
      localStorage.setItem(REFRESH_TOKEN_KEY, refresh_token);
    }

    set({
      token: access_token,
      refreshToken: refresh_token || null,
      user,
      capabilities: user?.capabilities || [],
      isAuthenticated: true,
    });

    return data;
  },

  logout: async () => {
    try {
      await authApi.logout();
    } catch (_) {
      /* best-effort */
    }

    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);

    set({
      user: null,
      token: null,
      refreshToken: null,
      capabilities: [],
      isAuthenticated: false,
    });

    window.location.href = '/login';
  },

  refreshSession: async () => {
    const currentRefresh = get().refreshToken;
    if (!currentRefresh) return;

    const data = await authApi.refresh(currentRefresh);
    const { access_token, refresh_token } = data;

    localStorage.setItem(TOKEN_KEY, access_token);
    if (refresh_token) {
      localStorage.setItem(REFRESH_TOKEN_KEY, refresh_token);
    }

    set((prev) => ({
      ...prev,
      token: access_token,
      refreshToken: refresh_token || prev.refreshToken,
    }));
  },

  loadUser: async () => {
    if (!get().token) return;

    try {
      const user = await authApi.me();
      set({
        user,
        capabilities: user?.capabilities || [],
        isAuthenticated: true,
      });
    } catch (_) {
      get().logout();
    }
  },
}));

export default useAuthStore;
