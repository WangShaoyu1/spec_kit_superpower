import { create } from 'zustand';
import { userApi, roleApi, permissionApi } from '../services/userApi';

const useUserStore = create((set, get) => ({
  // Users
  users: [],
  usersLoading: false,
  usersTotal: 0,
  usersPage: 1,
  usersPageSize: 20,
  usersSearch: '',
  usersStatus: '',

  setUsersSearch: (search) => set({ usersSearch: search, usersPage: 1 }),
  setUsersStatus: (status) => set({ usersStatus: status, usersPage: 1 }),
  setUsersPage: (page) => set({ usersPage: page }),
  setUsersPageSize: (pageSize) => set({ usersPageSize: pageSize, usersPage: 1 }),

  fetchUsers: async () => {
    const { usersPage, usersPageSize, usersSearch, usersStatus } = get();
    set({ usersLoading: true });
    try {
      const params = { page: usersPage, page_size: usersPageSize };
      if (usersSearch) params.search = usersSearch;
      if (usersStatus) params.status = usersStatus;
      const res = await userApi.listUsers(params);
      const data = res.data;
      set({
        users: data.items || [],
        usersTotal: data.total ?? 0,
      });
    } finally {
      set({ usersLoading: false });
    }
  },

  createUser: async (data) => {
    await userApi.createUser(data);
    get().fetchUsers();
  },

  updateUser: async (id, data) => {
    await userApi.updateUser(id, data);
    get().fetchUsers();
  },

  deleteUser: async (id) => {
    await userApi.deleteUser(id);
    get().fetchUsers();
  },

  resetPassword: async (id, password) => {
    await userApi.resetPassword(id, password);
  },

  assignRole: async (id, roleId) => {
    await userApi.assignRole(id, roleId);
    get().fetchUsers();
  },

  // Roles
  roles: [],
  rolesLoading: false,

  fetchRoles: async () => {
    set({ rolesLoading: true });
    try {
      const res = await roleApi.listRoles();
      set({ roles: res.data || [] });
    } finally {
      set({ rolesLoading: false });
    }
  },

  createRole: async (data) => {
    await roleApi.createRole(data);
    get().fetchRoles();
  },

  updateRole: async (id, data) => {
    await roleApi.updateRole(id, data);
    get().fetchRoles();
  },

  deleteRole: async (id) => {
    await roleApi.deleteRole(id);
    get().fetchRoles();
  },

  getRolePermissions: async (id) => {
    const res = await roleApi.getRolePermissions(id);
    return res.data || [];
  },

  updateRolePermissions: async (id, keys) => {
    await roleApi.updateRolePermissions(id, keys);
    get().fetchRoles();
  },

  // Permissions
  permissionModules: [],
  permissionsLoading: false,

  fetchPermissions: async () => {
    set({ permissionsLoading: true });
    try {
      const res = await permissionApi.listPermissions();
      set({ permissionModules: res.data || [] });
    } finally {
      set({ permissionsLoading: false });
    }
  },
}));

export default useUserStore;
