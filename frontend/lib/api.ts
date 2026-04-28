import axios, { AxiosError } from "axios";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const apiClient = axios.create({
  baseURL: `${BASE_URL}/api/v1`,
  headers: { "Content-Type": "application/json" },
  timeout: 30_000,
});

// Attach token on every request
apiClient.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auto-refresh on 401
apiClient.interceptors.response.use(
  (res) => res,
  async (error: AxiosError) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      const refresh = localStorage.getItem("refresh_token");
      if (refresh) {
        try {
          const { data } = await axios.post(`${BASE_URL}/api/v1/auth/refresh`, {
            refresh_token: refresh,
          });
          localStorage.setItem("access_token", data.access_token);
          localStorage.setItem("refresh_token", data.refresh_token);
          if (error.config) {
            error.config.headers.Authorization = `Bearer ${data.access_token}`;
            return apiClient(error.config);
          }
        } catch {
          localStorage.clear();
          window.location.href = "/login";
        }
      } else {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

// ─── Auth ─────────────────────────────────────────────────────────────────────
export const authApi = {
  login: (email: string, password: string) =>
    apiClient.post("/auth/login", { email, password }),
  me: () => apiClient.get("/auth/me"),
  refresh: (refresh_token: string) =>
    apiClient.post("/auth/refresh", { refresh_token }),
  changePassword: (current_password: string, new_password: string) =>
    apiClient.put("/auth/me/password", { current_password, new_password }),
};

// ─── Accounts ─────────────────────────────────────────────────────────────────
export const accountsApi = {
  list: () => apiClient.get("/accounts"),
  get: (id: number) => apiClient.get(`/accounts/${id}`),
  sync: (id: number) => apiClient.post(`/accounts/${id}/sync`),
  update: (id: number, data: Record<string, unknown>) =>
    apiClient.patch(`/accounts/${id}`, data),
};

// ─── Dashboard ────────────────────────────────────────────────────────────────
export const dashboardApi = {
  get: (params: {
    account_id?: string;
    date_from?: string;
    date_to?: string;
  }) => apiClient.get("/dashboard", { params }),
};

// ─── Campaigns ────────────────────────────────────────────────────────────────
export const campaignsApi = {
  list: (params: {
    account_id: string;
    date_from?: string;
    date_to?: string;
    status?: string;
    sort_by?: string;
    sort_dir?: string;
    page?: number;
    page_size?: number;
  }) => apiClient.get("/campaigns", { params }),
  action: (campaign_id: string, account_id: string, action: string) =>
    apiClient.post("/campaigns/action", { campaign_id, account_id, action }),
  updateBudget: (
    campaign_id: string,
    account_id: string,
    new_daily_budget: number,
    reason?: string
  ) =>
    apiClient.post("/campaigns/budget", {
      campaign_id,
      account_id,
      new_daily_budget,
      reason,
    }),
};

// ─── Keywords ─────────────────────────────────────────────────────────────────
export const keywordsApi = {
  searchTerms: (account_id: string, date_from?: string, date_to?: string) =>
    apiClient.get("/keywords/search-terms", {
      params: { account_id, date_from, date_to },
    }),
  ngrams: (account_id: string, n?: number) =>
    apiClient.get("/keywords/ngrams", { params: { account_id, n } }),
  negativeSuggestions: (account_id: string) =>
    apiClient.get("/keywords/negative-suggestions", {
      params: { account_id },
    }),
};

// ─── Automation ───────────────────────────────────────────────────────────────
export const automationApi = {
  listRules: (account_id?: string) =>
    apiClient.get("/automation/rules", { params: { account_id } }),
  createRule: (data: Record<string, unknown>) =>
    apiClient.post("/automation/rules", data),
  toggleRule: (id: number, status: string) =>
    apiClient.patch(`/automation/rules/${id}/status`, { status }),
  seedTemplates: () => apiClient.post("/automation/rules/seed-templates"),
  listLogs: (rule_id?: number) =>
    apiClient.get("/automation/logs", { params: { rule_id } }),
  listAlerts: (account_id?: string, unread_only?: boolean) =>
    apiClient.get("/automation/alerts", {
      params: { account_id, unread_only },
    }),
  markAlertRead: (id: number) =>
    apiClient.post(`/automation/alerts/${id}/read`),
};

// ─── Users ────────────────────────────────────────────────────────────────────
export const usersApi = {
  list: () => apiClient.get("/users"),
  create: (data: Record<string, unknown>) =>
    apiClient.post("/users", data),
  update: (id: number, data: Record<string, unknown>) =>
    apiClient.patch(`/users/${id}`, data),
};
