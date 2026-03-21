import { create } from 'zustand';
import { monitoringApi, alertApi } from '../services/monitoringApi';

const useMonitoringStore = create((set, get) => ({
  // Dashboard
  dashboard: null,
  dashboardLoading: false,
  trendData: [],
  trendLoading: false,
  timeRange: '24h',
  /** ISO strings when using RangePicker; when both set, they override timeRange for API calls */
  dashboardCustomStart: null,
  dashboardCustomEnd: null,
  autoRefresh: false,
  autoRefreshTimer: null,
  autoRefreshSecondsLeft: 30,

  setTimeRange: (range) =>
    set({ timeRange: range, dashboardCustomStart: null, dashboardCustomEnd: null }),

  setDashboardCustomRange: (startIso, endIso) =>
    set({
      dashboardCustomStart: startIso,
      dashboardCustomEnd: endIso,
    }),

  _dashboardParams: () => {
    const { timeRange, dashboardCustomStart, dashboardCustomEnd } = get();
    if (dashboardCustomStart && dashboardCustomEnd) {
      return { start_time: dashboardCustomStart, end_time: dashboardCustomEnd };
    }
    return { time_range: timeRange };
  },

  fetchDashboard: async () => {
    set({ dashboardLoading: true });
    try {
      const res = await monitoringApi.getDashboard(get()._dashboardParams());
      set({ dashboard: res.data });
    } finally {
      set({ dashboardLoading: false });
    }
  },

  fetchTrend: async (interval = '1h') => {
    set({ trendLoading: true });
    try {
      const res = await monitoringApi.getTrend({ ...get()._dashboardParams(), interval });
      set({ trendData: res.data || [] });
    } finally {
      set({ trendLoading: false });
    }
  },

  toggleAutoRefresh: () => {
    const { autoRefresh, autoRefreshTimer } = get();
    if (autoRefresh) {
      clearInterval(autoRefreshTimer);
      set({
        autoRefresh: false,
        autoRefreshTimer: null,
        autoRefreshSecondsLeft: 30,
      });
    } else {
      let left = 30;
      set({ autoRefreshSecondsLeft: 30 });
      const timer = setInterval(() => {
        left -= 1;
        if (left <= 0) {
          get().fetchDashboard();
          get().fetchTrend();
          left = 30;
        }
        set({ autoRefreshSecondsLeft: left });
      }, 1000);
      set({ autoRefresh: true, autoRefreshTimer: timer });
    }
  },

  resetAutoRefreshCountdown: () => {
    if (get().autoRefresh) {
      set({ autoRefreshSecondsLeft: 30 });
    }
  },

  clearAutoRefresh: () => {
    const { autoRefreshTimer } = get();
    if (autoRefreshTimer) clearInterval(autoRefreshTimer);
    set({
      autoRefresh: false,
      autoRefreshTimer: null,
      autoRefreshSecondsLeft: 30,
    });
  },

  // Logs
  logs: [],
  logsTotal: 0,
  logsPage: 1,
  logsPageSize: 20,
  logsLoading: false,
  logFilters: {},

  setLogFilters: (filters) => set({ logFilters: filters, logsPage: 1 }),
  setLogsPage: (page) => set({ logsPage: page }),

  fetchLogs: async () => {
    const { logsPage, logsPageSize, logFilters } = get();
    set({ logsLoading: true });
    try {
      const params = { page: logsPage, page_size: logsPageSize, ...logFilters };
      const res = await monitoringApi.queryLogs(params);
      const data = res.data;
      set({ logs: data.items || [], logsTotal: data.total ?? 0 });
    } finally {
      set({ logsLoading: false });
    }
  },

  // Session trace
  sessionTrace: null,
  sessionTraceLoading: false,

  fetchSessionTrace: async (sessionId) => {
    set({ sessionTraceLoading: true });
    try {
      const res = await monitoringApi.getSessionTrace(sessionId);
      set({ sessionTrace: res.data });
    } finally {
      set({ sessionTraceLoading: false });
    }
  },

  // Alert rules
  alertRules: [],
  alertRulesTotal: 0,
  alertRulesPage: 1,
  alertRulesLoading: false,

  setAlertRulesPage: (page) => set({ alertRulesPage: page }),

  fetchAlertRules: async () => {
    const { alertRulesPage } = get();
    set({ alertRulesLoading: true });
    try {
      const res = await alertApi.listRules({ page: alertRulesPage, page_size: 20 });
      const data = res.data;
      set({ alertRules: data.items || [], alertRulesTotal: data.total ?? 0 });
    } finally {
      set({ alertRulesLoading: false });
    }
  },

  createAlertRule: async (data) => {
    await alertApi.createRule(data);
    get().fetchAlertRules();
  },

  updateAlertRule: async (id, data) => {
    await alertApi.updateRule(id, data);
    get().fetchAlertRules();
  },

  deleteAlertRule: async (id) => {
    await alertApi.deleteRule(id);
    get().fetchAlertRules();
  },

  toggleAlertRule: async (id, isEnabled) => {
    await alertApi.toggleRule(id, isEnabled);
    get().fetchAlertRules();
  },

  // Alert events
  alertEvents: [],
  alertEventsTotal: 0,
  alertEventsPage: 1,
  alertEventsLoading: false,

  setAlertEventsPage: (page) => set({ alertEventsPage: page }),

  fetchAlertEvents: async (filters = {}) => {
    const { alertEventsPage } = get();
    set({ alertEventsLoading: true });
    try {
      const res = await alertApi.listEvents({
        page: alertEventsPage,
        page_size: 20,
        ...filters,
      });
      const data = res.data;
      set({ alertEvents: data.items || [], alertEventsTotal: data.total ?? 0 });
    } finally {
      set({ alertEventsLoading: false });
    }
  },
}));

export default useMonitoringStore;
