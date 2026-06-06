import axios, { AxiosInstance, AxiosError } from "axios";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export const api: AxiosInstance = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
});

// Attach token - check both localStorage and zustand-persist store
api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    // Try direct localStorage key first, then zustand persist key
    let token = localStorage.getItem("access_token");
    if (!token) {
      try {
        const stored = JSON.parse(
          localStorage.getItem("rag-eval-auth") || "{}"
        );
        token = stored?.state?.accessToken || null;
      } catch {}
    }
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Handle 403 role errors globally
api.interceptors.response.use(
  (res) => res,
  async (error: AxiosError) => {
    const detail = (error.response?.data as any)?.detail || "";
    // If role error, it means token is stale - force re-login
    if (
      error.response?.status === 403 &&
      typeof detail === "string" &&
      detail.includes("role") &&
      typeof window !== "undefined"
    ) {
      // Don't redirect — let components handle it with a friendly message
      return Promise.reject(error);
    }
    return Promise.reject(error);
  }
);

// Auto-refresh on 401
api.interceptors.response.use(
  (res) => res,
  async (error: AxiosError) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      let refreshToken = localStorage.getItem("refresh_token");
      if (!refreshToken) {
        try {
          const stored = JSON.parse(
            localStorage.getItem("rag-eval-auth") || "{}"
          );
          refreshToken = stored?.state?.refreshToken || null;
        } catch {}
      }
      if (refreshToken) {
        try {
          const { data } = await axios.post(`${API_BASE}/auth/refresh`, {
            refresh_token: refreshToken,
          });
          // Update both storage locations
          localStorage.setItem("access_token", data.access_token);
          localStorage.setItem("refresh_token", data.refresh_token);
          try {
            const stored = JSON.parse(
              localStorage.getItem("rag-eval-auth") || "{}"
            );
            stored.state = stored.state || {};
            stored.state.accessToken = data.access_token;
            stored.state.refreshToken = data.refresh_token;
            localStorage.setItem("rag-eval-auth", JSON.stringify(stored));
          } catch {}
          if (error.config) {
            error.config.headers.Authorization = `Bearer ${data.access_token}`;
            return api.request(error.config);
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

// Auth
export const authApi = {
  register: (data: any) => api.post("/auth/register", data),
  login: (data: any) => api.post("/auth/login", data),
  refreshToken: (refreshToken: string) =>
    api.post("/auth/refresh", { refresh_token: refreshToken }),
  requestPasswordReset: (email: string) =>
    api.post("/auth/password-reset/request", { email }),
  confirmPasswordReset: (token: string, new_password: string) =>
    api.post("/auth/password-reset/confirm", { token, new_password }),
};

// Users
export const usersApi = {
  getMe: () => api.get("/users/me"),
  updateMe: (data: any) => api.put("/users/me", data),
  listUsers: (params?: any) => api.get("/users/", { params }),
  updateRole: (userId: string, role: string) =>
    api.put(`/users/${userId}/role`, { role }),
};

// Datasets
export const datasetsApi = {
  create: (data: any) => api.post("/datasets/", data),
  list: (params?: any) => api.get("/datasets/", { params }),
  get: (id: string) => api.get(`/datasets/${id}`),
  update: (id: string, data: any) => api.put(`/datasets/${id}`, data),
  delete: (id: string) => api.delete(`/datasets/${id}`),
  uploadFile: (id: string, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return api.post(`/datasets/${id}/upload`, form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  addQAPairs: (id: string, pairs: any[]) =>
    api.post(`/datasets/${id}/qa-pairs`, pairs),
};

// RAG
export const ragApi = {
  query: (data: any) => api.post("/rag/query", data),
};

// Evaluation
export const evaluationApi = {
  startRun: (data: any) => api.post("/evaluation/run", data),
  getHistory: (params?: any) => api.get("/evaluation/history", { params }),
  getRun: (id: string) => api.get(`/evaluation/${id}`),
  getResults: (runId: string, params?: any) =>
    api.get(`/evaluation/${runId}/results`, { params }),
  deleteRun: (id: string) => api.delete(`/evaluation/${id}`),
};

// Prompts
export const promptsApi = {
  create: (data: any) => api.post("/prompts/", data),
  list: (params?: any) => api.get("/prompts/", { params }),
  get: (id: string) => api.get(`/prompts/${id}`),
  update: (id: string, data: any) => api.put(`/prompts/${id}`, data),
  delete: (id: string) => api.delete(`/prompts/${id}`),
  compare: (data: any) => api.post("/prompts/compare", data),
};

// Models
export const modelsApi = {
  supported: () => api.get("/models/supported"),
  compare: (runIds: string) => api.get("/models/compare", { params: { run_ids: runIds } }),
  fallbackAnalytics: () => api.get("/models/fallback-analytics"),
};

// Feedback
export const feedbackApi = {
  submit: (data: any) => api.post("/feedback/", data),
  getForRun: (runId: string) => api.get(`/feedback/run/${runId}`),
};

// Dashboard
export const dashboardApi = {
  status: () => api.get("/dashboard/status"),
  summary: () => api.get("/dashboard/summary"),
  trends: (days?: number) => api.get("/dashboard/trends", { params: { days } }),
  modelUsage: () => api.get("/dashboard/model-usage"),
  hallucinationReport: (days?: number) =>
    api.get("/dashboard/hallucination-report", { params: { days } }),
};

// Reports
export const reportsApi = {
  exportCsv: (runId: string) =>
    api.get(`/reports/export/csv`, { params: { run_id: runId }, responseType: "blob" }),
  exportExcel: (runId: string) =>
    api.get(`/reports/export/excel`, { params: { run_id: runId }, responseType: "blob" }),
  exportPdf: (runId: string) =>
    api.get(`/reports/export/pdf`, { params: { run_id: runId }, responseType: "blob" }),
};

// Security
export const securityApi = {
  getLogs: (params?: any) => api.get("/security/logs", { params }),
  getStats: () => api.get("/security/stats"),
};
