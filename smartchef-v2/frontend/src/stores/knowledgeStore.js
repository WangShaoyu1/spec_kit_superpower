import { create } from 'zustand';
import { knowledgeApi } from '../services/knowledgeApi';

const useKnowledgeStore = create((set, get) => ({
  categories: [],
  categoriesLoading: false,

  documents: [],
  documentsLoading: false,
  total: 0,
  page: 1,
  pageSize: 20,
  search: '',
  categoryFilter: null,
  statusFilter: '',

  currentDocument: null,
  detailLoading: false,

  searchResults: [],
  searchLoading: false,

  setSearch: (search) => set({ search, page: 1 }),
  setCategoryFilter: (categoryFilter) => set({ categoryFilter, page: 1 }),
  setStatusFilter: (statusFilter) => set({ statusFilter, page: 1 }),
  setPage: (page) => set({ page }),
  setPageSize: (pageSize) => set({ pageSize, page: 1 }),

  fetchCategories: async () => {
    set({ categoriesLoading: true });
    try {
      const res = await knowledgeApi.listCategories();
      set({ categories: res.data || [] });
    } finally {
      set({ categoriesLoading: false });
    }
  },

  createCategory: async (data) => {
    await knowledgeApi.createCategory(data);
    get().fetchCategories();
  },

  updateCategory: async (id, data) => {
    await knowledgeApi.updateCategory(id, data);
    get().fetchCategories();
  },

  deleteCategory: async (id) => {
    await knowledgeApi.deleteCategory(id);
    get().fetchCategories();
  },

  fetchDocuments: async () => {
    const { page, pageSize, search, categoryFilter, statusFilter } = get();
    set({ documentsLoading: true });
    try {
      const params = { page, page_size: pageSize };
      if (search) params.search = search;
      if (categoryFilter) params.category_id = categoryFilter;
      if (statusFilter) params.status = statusFilter;

      const res = await knowledgeApi.listDocuments(params);
      const data = res.data;
      set({
        documents: data.items || [],
        total: data.total ?? 0,
      });
    } finally {
      set({ documentsLoading: false });
    }
  },

  uploadDocument: async (formData) => {
    const res = await knowledgeApi.uploadDocument(formData);
    get().fetchDocuments();
    return res.data;
  },

  updateDocument: async (id, data) => {
    const res = await knowledgeApi.updateDocument(id, data);
    get().fetchDocuments();
    return res.data;
  },

  deleteDocument: async (id) => {
    await knowledgeApi.deleteDocument(id);
    get().fetchDocuments();
  },

  reindexDocument: async (id) => {
    const res = await knowledgeApi.reindexDocument(id);
    if (get().currentDocument?.id === id) {
      get().fetchDocumentDetail(id);
    }
    get().fetchDocuments();
    return res.data;
  },

  fetchDocumentDetail: async (id) => {
    set({ detailLoading: true, currentDocument: null });
    try {
      const res = await knowledgeApi.getDocument(id);
      set({ currentDocument: res.data });
    } finally {
      set({ detailLoading: false });
    }
  },

  searchKnowledge: async (query, categoryId, topK) => {
    set({ searchLoading: true });
    try {
      const res = await knowledgeApi.search({
        query,
        category_id: categoryId || undefined,
        top_k: topK || 10,
      });
      set({ searchResults: res.data || [] });
    } finally {
      set({ searchLoading: false });
    }
  },

  clearDetail: () => set({ currentDocument: null }),
  clearSearch: () => set({ searchResults: [] }),
}));

export default useKnowledgeStore;
