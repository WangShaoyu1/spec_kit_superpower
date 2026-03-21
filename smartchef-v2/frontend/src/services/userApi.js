import api from './api';

export const userApi = {
  listUsers: (params) => api.get('/users', { params }),
  createUser: (data) => api.post('/users', data),
  getUser: (id) => api.get(`/users/${id}`),
  updateUser: (id, data) => api.put(`/users/${id}`, data),
  deleteUser: (id) => api.delete(`/users/${id}`),
  assignRole: (id, roleId) => api.put(`/users/${id}/roles`, { role_id: roleId }),
  resetPassword: (id, password) => api.put(`/users/${id}/password`, { password }),
};

export const roleApi = {
  listRoles: () => api.get('/roles'),
  createRole: (data) => api.post('/roles', data),
  getRole: (id) => api.get(`/roles/${id}`),
  updateRole: (id, data) => api.put(`/roles/${id}`, data),
  deleteRole: (id) => api.delete(`/roles/${id}`),
  getRolePermissions: (id) => api.get(`/roles/${id}/permissions`),
  updateRolePermissions: (id, keys) =>
    api.put(`/roles/${id}/permissions`, { permission_keys: keys }),
};

export const permissionApi = {
  listPermissions: () => api.get('/permissions'),
};
