import { create } from 'zustand';
import { profileApi } from '../services/profileApi';

const useProfileStore = create((set, get) => ({
  profiles: [],
  loading: false,
  total: 0,
  page: 1,
  pageSize: 10,
  search: '',
  statusFilter: '',
  stats: { total: 0, draft: 0, active: 0, published_versions: 0 },

  currentProfile: null,
  detailLoading: false,
  personas: [],
  bindings: [],
  versions: [],

  testSessions: [],
  currentSessionId: null,
  messages: [],
  chatLoading: false,

  setSearch: (search) => set({ search, page: 1 }),
  setStatusFilter: (statusFilter) => set({ statusFilter, page: 1 }),
  setPage: (page) => set({ page }),
  setPageSize: (pageSize) => set({ pageSize, page: 1 }),

  fetchStats: async () => {
    try {
      const res = await profileApi.getStats();
      set({ stats: res.data || res });
    } catch { /* ignore */ }
  },

  fetchProfiles: async () => {
    const { page, pageSize, search, statusFilter } = get();
    set({ loading: true });
    try {
      const params = { page, page_size: pageSize };
      if (search) params.search = search;
      if (statusFilter) params.status = statusFilter;
      const res = await profileApi.listProfiles(params);
      const data = res.data;
      set({
        profiles: data.items || data || [],
        total: data.total ?? (data.items || data || []).length,
      });
    } finally {
      set({ loading: false });
    }
  },

  createProfile: async (data) => {
    const res = await profileApi.createProfile(data);
    get().fetchProfiles();
    get().fetchStats();
    return res.data;
  },

  updateProfile: async (id, data) => {
    const res = await profileApi.updateProfile(id, data);
    get().fetchProfiles();
    if (get().currentProfile?.id === id) {
      set((s) => ({ currentProfile: { ...s.currentProfile, ...data } }));
    }
    return res.data;
  },

  deleteProfile: async (id) => {
    await profileApi.deleteProfile(id);
    get().fetchProfiles();
    get().fetchStats();
  },

  fetchDetail: async (id) => {
    set({ detailLoading: true, currentProfile: null });
    try {
      const [profRes, personaRes, bindRes, verRes] = await Promise.all([
        profileApi.getProfile(id),
        profileApi.listPersonas(id),
        profileApi.listBindings(id),
        profileApi.listVersions(id),
      ]);
      set({
        currentProfile: profRes.data,
        personas: personaRes.data || [],
        bindings: bindRes.data || [],
        versions: verRes.data || [],
      });
    } finally {
      set({ detailLoading: false });
    }
  },

  createPersona: async (profileId, data) => {
    await profileApi.createPersona(profileId, data);
    const res = await profileApi.listPersonas(profileId);
    set({ personas: res.data || [] });
  },

  updatePersona: async (profileId, personaId, data) => {
    await profileApi.updatePersona(profileId, personaId, data);
    const res = await profileApi.listPersonas(profileId);
    set({ personas: res.data || [] });
  },

  deletePersona: async (profileId, personaId) => {
    await profileApi.deletePersona(profileId, personaId);
    const res = await profileApi.listPersonas(profileId);
    set({ personas: res.data || [] });
  },

  activatePersona: async (profileId, personaId) => {
    await profileApi.activatePersona(profileId, personaId);
    const res = await profileApi.listPersonas(profileId);
    set({ personas: res.data || [] });
  },

  syncBindings: async (profileId, bindings) => {
    await profileApi.syncBindings(profileId, bindings);
    const res = await profileApi.listBindings(profileId);
    set({ bindings: res.data || [] });
  },

  publish: async (profileId) => {
    await profileApi.publish(profileId);
    const verRes = await profileApi.listVersions(profileId);
    set({ versions: verRes.data || [] });
    get().fetchProfiles();
    get().fetchStats();
  },

  archiveVersion: async (versionId) => {
    await profileApi.archiveVersion(versionId);
    const pid = get().currentProfile?.id;
    if (pid) {
      const verRes = await profileApi.listVersions(pid);
      set({ versions: verRes.data || [] });
    }
  },

  // Test chat
  fetchTestSessions: async (profileId) => {
    try {
      const res = await profileApi.listTestSessions(profileId);
      set({ testSessions: res.data || [] });
    } catch { /* ignore */ }
  },

  createTestSession: async (profileId, name) => {
    const res = await profileApi.createTestSession(profileId, { name });
    get().fetchTestSessions(profileId);
    return res.data;
  },

  deleteTestSession: async (sessionId, profileId) => {
    await profileApi.deleteTestSession(sessionId);
    set((s) => ({
      testSessions: s.testSessions.filter((t) => t.id !== sessionId),
      currentSessionId: s.currentSessionId === sessionId ? null : s.currentSessionId,
      messages: s.currentSessionId === sessionId ? [] : s.messages,
    }));
  },

  renameTestSession: async (sessionId, name) => {
    await profileApi.updateTestSession(sessionId, { name });
    set((s) => ({
      testSessions: s.testSessions.map((t) =>
        t.id === sessionId ? { ...t, name } : t,
      ),
    }));
  },

  setCurrentSession: (sessionId) => set({ currentSessionId: sessionId }),

  fetchMessages: async (sessionId) => {
    set({ chatLoading: true });
    try {
      const res = await profileApi.getMessages(sessionId);
      set({ messages: res.data || [] });
    } finally {
      set({ chatLoading: false });
    }
  },

  sendMessage: async (sessionId, content, extra = {}) => {
    set({ chatLoading: true });
    try {
      const res = await profileApi.sendMessage(sessionId, { content, ...extra });
      const result = res.data;
      set((s) => ({
        messages: [
          ...s.messages,
          result.user_message,
          result.assistant_message,
        ],
      }));
      return result;
    } finally {
      set({ chatLoading: false });
    }
  },

  clearDetail: () =>
    set({
      currentProfile: null,
      personas: [],
      bindings: [],
      versions: [],
    }),
}));

export default useProfileStore;
