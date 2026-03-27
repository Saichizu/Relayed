import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: BASE_URL,
  withCredentials: false,
});

// Auth
export const login = (password) => api.post("/auth/login", { password });
export const logout = () => api.post("/auth/logout");
export const getMe = () => api.get("/auth/me");

// Users
export const listUsers = () => api.get("/auth/users");
export const createUser = (data) => api.post("/auth/users", data);
export const updateUser = (id, data) => api.put(`/auth/users/${id}`, data);
export const deleteUser = (id) => api.delete(`/auth/users/${id}`);

// Tables
export const listTables = () => api.get("/tables");
export const getTable = (ch) => api.get(`/tables/${ch}`);
export const startTimer = (ch, data) => api.post(`/tables/${ch}/start`, data);
export const openTable = (ch, data) => api.post(`/tables/${ch}/open`, data);
export const addTime = (ch, data) => api.post(`/tables/${ch}/add-time`, data);
export const finishTable = (ch, data) => api.post(`/tables/${ch}/finish`, data);
export const outageAdjust = (ch, data) => api.post(`/tables/${ch}/outage-adjust`, data);

// Queue
export const listQueue = () => api.get("/tables/queue/list");
export const addToQueue = (data) => api.post("/tables/queue/add", data);
export const removeFromQueue = (id) => api.delete(`/tables/queue/${id}`);
export const assignQueue = (data) => api.post("/tables/queue/assign", data);

// History
export const getHistory = (params) => api.get("/history", { params });

// System
export const getEspStatus = () => api.get("/system/esp/status");
export const getDemoMode = () => api.get("/system/demo-mode");
export const setDemoMode = (enabled) => api.post("/system/demo-mode", { enabled });
export const processPending = () => api.post("/system/pending/process");

export default api;
