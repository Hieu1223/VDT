import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API_BASE = `${BACKEND_URL}/api`;

export const TOKEN_KEY = "helpdesk_access_token";
export const REFRESH_KEY = "helpdesk_refresh_token";

export function getAccessToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}
export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_KEY);
}
export function setTokens(access: string, refresh: string) {
  localStorage.setItem(TOKEN_KEY, access);
  localStorage.setItem(REFRESH_KEY, refresh);
}
export function clearTokens() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

export const apiClient = axios.create({ baseURL: API_BASE });

apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = getAccessToken();
  if (token) {
    (config.headers as any) = config.headers || {};
    (config.headers as any).Authorization = `Bearer ${token}`;
  }
  return config;
});

let refreshPromise: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  const refresh = getRefreshToken();
  if (!refresh) return null;
  try {
    const { data } = await axios.post(`${API_BASE}/auth/refresh`, { refresh_token: refresh });
    setTokens(data.access_token, data.refresh_token);
    return data.access_token;
  } catch {
    clearTokens();
    return null;
  }
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as InternalAxiosRequestConfig & { _retried?: boolean };
    if (error.response?.status === 401 && original && !original._retried && getRefreshToken()) {
      original._retried = true;
      if (!refreshPromise) {
        refreshPromise = refreshAccessToken().finally(() => {
          refreshPromise = null;
        });
      }
      const newToken = await refreshPromise;
      if (newToken) {
        (original.headers as any) = original.headers || {};
        (original.headers as any).Authorization = `Bearer ${newToken}`;
        return apiClient(original);
      }
    }
    return Promise.reject(error);
  }
);

export function formatApiError(detail: any): string {
  if (detail == null) return "Something went wrong. Please try again.";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map((e) => (e && typeof e.msg === "string" ? e.msg : JSON.stringify(e))).filter(Boolean).join(" ");
  }
  if (detail && typeof detail.msg === "string") return detail.msg;
  return String(detail);
}

export function getWsUrl(token: string): string {
  const httpBase = BACKEND_URL || "";
  const wsBase = httpBase.replace(/^http/, "ws");
  return `${wsBase}/api/ws?token=${encodeURIComponent(token)}`;
}
