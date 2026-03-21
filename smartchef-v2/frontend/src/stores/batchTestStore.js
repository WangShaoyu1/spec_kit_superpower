import { create } from 'zustand';
import { batchTestApi } from '../services/batchTestApi';

const useBatchTestStore = create((set, get) => ({
  batches: [],
  loading: false,
  total: 0,
  page: 1,
  pageSize: 10,
  search: '',
  statusFilter: '',
  stats: { total: 0, running: 0, completed: 0, avg_accuracy: null },

  currentBatch: null,
  detailLoading: false,

  cases: [],
  casesTotal: 0,
  casesPage: 1,
  casesLoading: false,

  runs: [],
  runsTotal: 0,
  runsPage: 1,
  runsLoading: false,

  analysis: null,
  analysisLoading: false,

  executing: false,

  setSearch: (search) => set({ search, page: 1 }),
  setStatusFilter: (statusFilter) => set({ statusFilter, page: 1 }),
  setPage: (page) => set({ page }),
  setPageSize: (pageSize) => set({ pageSize, page: 1 }),
  setCasesPage: (casesPage) => set({ casesPage }),
  setRunsPage: (runsPage) => set({ runsPage }),

  fetchStats: async () => {
    try {
      const res = await batchTestApi.getStats();
      set({ stats: res.data || res });
    } catch { /* ignore */ }
  },

  fetchBatches: async () => {
    const { page, pageSize, search, statusFilter } = get();
    set({ loading: true });
    try {
      const params = { page, page_size: pageSize };
      if (search) params.search = search;
      if (statusFilter) params.status = statusFilter;
      const res = await batchTestApi.list(params);
      const data = res.data;
      set({
        batches: data.items || [],
        total: data.total ?? 0,
      });
    } finally {
      set({ loading: false });
    }
  },

  createBatch: async (data) => {
    const res = await batchTestApi.create(data);
    get().fetchBatches();
    get().fetchStats();
    return res.data;
  },

  deleteBatch: async (id) => {
    await batchTestApi.delete(id);
    get().fetchBatches();
    get().fetchStats();
  },

  fetchDetail: async (id) => {
    set({ detailLoading: true, currentBatch: null });
    try {
      const res = await batchTestApi.get(id);
      set({ currentBatch: res.data });
    } finally {
      set({ detailLoading: false });
    }
  },

  fetchCases: async (batchId) => {
    const { casesPage } = get();
    set({ casesLoading: true });
    try {
      const res = await batchTestApi.listCases(batchId, { page: casesPage, page_size: 50 });
      const data = res.data;
      set({ cases: data.items || [], casesTotal: data.total ?? 0 });
    } finally {
      set({ casesLoading: false });
    }
  },

  addCase: async (batchId, data) => {
    await batchTestApi.addCase(batchId, data);
    await get().fetchCases(batchId);
    await get().fetchDetail(batchId);
  },

  updateCase: async (batchId, caseId, data) => {
    await batchTestApi.updateCase(batchId, caseId, data);
    await get().fetchCases(batchId);
  },

  deleteCase: async (batchId, caseId) => {
    await batchTestApi.deleteCase(batchId, caseId);
    await get().fetchCases(batchId);
    await get().fetchDetail(batchId);
  },

  importCases: async (batchId, cases) => {
    const res = await batchTestApi.importCases(batchId, cases);
    await get().fetchCases(batchId);
    await get().fetchDetail(batchId);
    return res.data;
  },

  exportCases: async (batchId) => {
    const res = await batchTestApi.exportCases(batchId);
    return res.data;
  },

  executeBatch: async (batchId) => {
    set({ executing: true });
    try {
      const res = await batchTestApi.execute(batchId);
      set((s) =>
        s.currentBatch?.id === batchId ? { currentBatch: res.data } : {},
      );
      return res.data;
    } finally {
      set({ executing: false });
    }
  },

  generateCases: async (batchId, body) => {
    await batchTestApi.generateCases(batchId, body);
    await get().fetchCases(batchId);
    await get().fetchDetail(batchId);
    get().fetchBatches();
    get().fetchStats();
  },

  fetchRuns: async (batchId) => {
    const { runsPage } = get();
    set({ runsLoading: true });
    try {
      const res = await batchTestApi.listRuns(batchId, { page: runsPage, page_size: 50 });
      const data = res.data;
      set({ runs: data.items || [], runsTotal: data.total ?? 0 });
    } finally {
      set({ runsLoading: false });
    }
  },

  fetchAnalysis: async (batchId) => {
    set({ analysisLoading: true });
    try {
      const res = await batchTestApi.getAnalysis(batchId);
      set({ analysis: res.data });
    } finally {
      set({ analysisLoading: false });
    }
  },

  triggerAnalysis: async (batchId) => {
    set({ analysisLoading: true });
    try {
      const res = await batchTestApi.triggerAnalysis(batchId);
      set({ analysis: res.data });
      return res.data;
    } finally {
      set({ analysisLoading: false });
    }
  },

  clearDetail: () =>
    set({
      currentBatch: null,
      cases: [],
      casesTotal: 0,
      runs: [],
      runsTotal: 0,
      analysis: null,
    }),
}));

export default useBatchTestStore;
