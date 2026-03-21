import axios from 'axios';
import { message } from 'antd';

const SUCCESS_CODE = '000000';
const AUTH_ERROR_PREFIX = 'E101';
const FORBIDDEN_CODE = 'E10107';
const TOKEN_KEY = 'smartchef_token';
const REFRESH_TOKEN_KEY = 'smartchef_refresh_token';

class ApiBusinessError extends Error {
  constructor(msg, code, status) {
    super(msg || 'Business error');
    this.name = 'ApiBusinessError';
    this.code = code;
    this.status = status;
  }
}

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

/** D037: 请求被 AbortController 取消时不应弹出全局错误提示（StrictMode 双挂载/路由切换常见） */
function isRequestCanceled(error) {
  return (
    axios.isCancel?.(error) === true ||
    error?.code === 'ERR_CANCELED' ||
    error?.name === 'CanceledError' ||
    error?.name === 'AbortError'
  );
}

api.interceptors.response.use(
  (response) => {
    const payload = response?.data;
    if (!payload || typeof payload !== 'object' || !('code' in payload)) {
      return response;
    }

    const { code, data, msg } = payload;

    if (code === SUCCESS_CODE) {
      response.data = data;
      return response;
    }

    if (typeof code === 'string' && code === FORBIDDEN_CODE) {
      window.location.href = '/403';
      return Promise.reject(new ApiBusinessError(msg, code, response.status));
    }

    if (typeof code === 'string' && code.startsWith(AUTH_ERROR_PREFIX)) {
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(REFRESH_TOKEN_KEY);
      window.location.href = '/login';
      return Promise.reject(new ApiBusinessError(msg, code, response.status));
    }

    message.error(msg || '请求失败');
    return Promise.reject(new ApiBusinessError(msg, code, response.status));
  },
  (error) => {
    if (isRequestCanceled(error)) {
      return Promise.reject(error);
    }

    const status = error.response?.status;
    const payload = error.response?.data;

    if (payload && typeof payload === 'object' && 'code' in payload) {
      const { code, msg } = payload;

      if (typeof code === 'string' && code === FORBIDDEN_CODE) {
        window.location.href = '/403';
        return Promise.reject(new ApiBusinessError(msg, code, status));
      }

      if (typeof code === 'string' && code.startsWith(AUTH_ERROR_PREFIX)) {
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(REFRESH_TOKEN_KEY);
        window.location.href = '/login';
        return Promise.reject(new ApiBusinessError(msg, code, status));
      }

      message.error(msg || '请求失败');
      return Promise.reject(new ApiBusinessError(msg, code, status));
    }

    if (status === 401) {
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(REFRESH_TOKEN_KEY);
      window.location.href = '/login';
    } else if (status === 403) {
      window.location.href = '/403';
    } else {
      message.error(error.message || '网络错误');
    }

    return Promise.reject(error);
  },
);

export const authApi = {
  login: (username, password) =>
    api.post('/auth/login', { username, password }).then((r) => r.data),

  logout: () => api.post('/auth/logout').then((r) => r.data),

  me: () => api.get('/auth/me').then((r) => r.data),

  refresh: (refreshToken) =>
    api.post('/auth/refresh', { refresh_token: refreshToken }).then((r) => r.data),
};

export default api;
export { ApiBusinessError, SUCCESS_CODE, TOKEN_KEY, REFRESH_TOKEN_KEY };
