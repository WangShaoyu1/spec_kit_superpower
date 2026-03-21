import { create } from 'zustand';
import { intentLibraryApi } from '../services/intentLibraryApi';

// D028: 模块级 AbortController，用于取消重复请求（React StrictMode 双挂载）
let listLibrariesAbort = null;

const useIntentLibraryStore = create((set, get) => ({
  libraries: [],
  loading: false,
  total: 0,
  totalZh: 0,
  totalEn: 0,
  page: 1,
  pageSize: 10,
  search: '',
  languageFilter: '',

  currentLibrary: null,
  detailLoading: false,
  models: [],
  modelsLoading: false,

  setSearch: (search) => set({ search, page: 1 }),
  setLanguageFilter: (languageFilter) => set({ languageFilter, page: 1 }),
  setPage: (page) => set({ page }),
  setPageSize: (pageSize) => set({ pageSize, page: 1 }),

  fetchLibraries: async (signal) => {
    const { page, pageSize, search, languageFilter } = get();
    if (listLibrariesAbort) listLibrariesAbort.abort();
    const ac = new AbortController();
    listLibrariesAbort = ac;
    const effectiveSignal = signal || ac.signal;
    set({ loading: true });
    try {
      const params = { page, page_size: pageSize };
      if (search) params.search = search;
      if (languageFilter) params.language = languageFilter;

      const res = await intentLibraryApi.listLibraries(params, { signal: effectiveSignal });
      const data = res.data;
      const rawItems = data.items || data || [];
      const items = rawItems.map((lib) => ({
        ...lib,
        confidence_threshold: lib.confidence_threshold ?? lib.default_confidence_threshold,
        ambiguity_threshold: lib.ambiguity_threshold ?? lib.default_slot_f1_threshold,
      }));
      set({
        libraries: items,
        total: data.total ?? rawItems.length,
        totalZh: data.total_zh ?? 0,
        totalEn: data.total_en ?? 0,
      });
    } catch (err) {
      if (err?.name === 'AbortError' || err?.code === 'ERR_CANCELED') return;
      throw err;
    } finally {
      if (listLibrariesAbort === ac) listLibrariesAbort = null;
      set({ loading: false });
    }
  },

  createLibrary: async (data) => {
    const payload = {
      ...data,
      default_confidence_threshold: data.confidence_threshold ?? data.default_confidence_threshold ?? 0.7,
      default_intent_f1_threshold: data.default_intent_f1_threshold ?? 0.95,
      default_slot_f1_threshold: data.ambiguity_threshold ?? data.default_slot_f1_threshold ?? 0.9,
    };
    const res = await intentLibraryApi.createLibrary(payload);
    get().fetchLibraries();
    return res.data;
  },

  updateLibrary: async (id, data) => {
    const payload = {
      ...data,
      default_confidence_threshold: data.confidence_threshold ?? data.default_confidence_threshold,
      default_intent_f1_threshold: data.default_intent_f1_threshold,
      default_slot_f1_threshold: data.ambiguity_threshold ?? data.default_slot_f1_threshold,
    };
    const res = await intentLibraryApi.updateLibrary(id, payload);
    get().fetchLibraries();
    if (get().currentLibrary?.id === id) {
      set((s) => ({ currentLibrary: { ...s.currentLibrary, ...data } }));
    }
    return res.data;
  },

  deleteLibrary: async (id) => {
    await intentLibraryApi.deleteLibrary(id);
    get().fetchLibraries();
  },

  fetchLibraryDetail: async (id) => {
    set({ detailLoading: true, currentLibrary: null });
    try {
      const res = await intentLibraryApi.getLibrary(id);
      const lib = res.data;
      // D023: 与列表页一致，将 API 字段映射为前端展示字段
      set({
        currentLibrary: {
          ...lib,
          confidence_threshold: lib?.confidence_threshold ?? lib?.default_confidence_threshold,
          ambiguity_threshold: lib?.ambiguity_threshold ?? lib?.default_slot_f1_threshold,
          // D038: 与 DD 字段 default_intent_f1_threshold 对齐，供详情页展示
          intent_f1_threshold: lib?.intent_f1_threshold ?? lib?.default_intent_f1_threshold,
        },
      });
    } finally {
      set({ detailLoading: false });
    }
  },

  fetchModels: async (libId, opts = {}) => {
    const silent = opts.silent === true;
    if (!silent) set({ modelsLoading: true });
    try {
      const res = await intentLibraryApi.listModels(libId);
      const data = res.data;
      set({ models: data.items || data || [] });
    } finally {
      if (!silent) set({ modelsLoading: false });
    }
  },

  /** 仅提交训练任务并刷新列表（HTTP 应尽快返回） */
  startTrainJob: async (modelId, trainConfig) => {
    await intentLibraryApi.trainModel(modelId, trainConfig);
    const lib = get().currentLibrary;
    if (lib) await get().fetchModels(lib.id, { silent: true });
  },

  /**
   * 轮询直到模型进入终态：trained / failed，或超时。
   * @returns {{ ok: true, model }} | {{ ok: false, model, error }} | {{ ok: null, timeout: true }}
   */
  pollTrainingUntilDone: async (modelId, libraryId, opts = {}) => {
    const maxMs = opts.maxMs ?? 30 * 60 * 1000;
    const interval = opts.interval ?? 2000;
    const start = Date.now();
    const idStr = String(modelId);

    const mergeModel = (m) => {
      if (!m) return;
      set((s) => ({
        models: s.models.some((x) => String(x.id) === idStr)
          ? s.models.map((x) => (String(x.id) === idStr ? { ...x, ...m } : x))
          : [...s.models, m],
      }));
    };

    let first = true;
    while (Date.now() - start < maxMs) {
      if (!first) {
        await new Promise((r) => setTimeout(r, interval));
      }
      first = false;
      try {
        const res = await intentLibraryApi.getModel(modelId);
        const m = res.data;
        mergeModel(m);
        if (m.status === 'trained') return { ok: true, model: m };
        if (m.status === 'failed') return { ok: false, model: m, error: m.notes || '训练失败' };
      } catch {
        await get().fetchModels(libraryId, { silent: true });
        const models = get().models;
        const m = models.find((x) => String(x.id) === idStr);
        if (m?.status === 'trained') return { ok: true, model: m };
        if (m?.status === 'failed') return { ok: false, model: m, error: m.notes || '训练失败' };
      }
    }
    return { ok: null, timeout: true };
  },

  trainModel: async (modelId, trainConfig) => {
    await get().startTrainJob(modelId, trainConfig);
  },

  evaluateModel: async (modelId, data) => {
    await intentLibraryApi.evaluateModel(modelId, data);
    const lib = get().currentLibrary;
    if (lib) get().fetchModels(lib.id);
  },

  setTestable: async (modelId) => {
    await intentLibraryApi.setTestable(modelId);
    const lib = get().currentLibrary;
    if (lib) get().fetchModels(lib.id);
  },

  publishModel: async (modelId) => {
    await intentLibraryApi.publishModel(modelId);
    const lib = get().currentLibrary;
    if (lib) get().fetchModels(lib.id);
  },

  archiveModel: async (modelId) => {
    await intentLibraryApi.archiveModel(modelId);
    const lib = get().currentLibrary;
    if (lib) get().fetchModels(lib.id);
  },

  restoreModel: async (modelId) => {
    await intentLibraryApi.restoreModel(modelId);
    const lib = get().currentLibrary;
    if (lib) get().fetchModels(lib.id);
  },

  createModel: async (libId, data) => {
    const res = await intentLibraryApi.createModel(libId, data);
    get().fetchModels(libId);
    return res.data;
  },

  clearDetail: () => set({ currentLibrary: null, models: [] }),
}));

export default useIntentLibraryStore;
