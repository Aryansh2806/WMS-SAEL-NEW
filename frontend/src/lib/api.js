import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Create axios instance with credentials
const api = axios.create({
  baseURL: API,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Auth APIs
export const authAPI = {
  login: (data) => api.post('/auth/login', data),
  register: (data) => api.post('/auth/register', data),
  logout: () => api.post('/auth/logout'),
  me: () => api.get('/auth/me'),
  session: (sessionId) => api.post('/auth/session', { session_id: sessionId })
};

// User APIs
export const userAPI = {
  getAll: () => api.get('/users'),
  create: (data) => api.post('/users', data),
  update: (userId, data) => api.put(`/users/${userId}`, data),
  updateRole: (userId, role) => api.put(`/users/${userId}/role?role=${role}`),
  toggleStatus: (userId) => api.put(`/users/${userId}/status`),
  delete: (userId) => api.delete(`/users/${userId}`),
  getRoles: () => api.get('/users/roles')
};

// Audit Log APIs
export const auditAPI = {
  getAll: (params) => api.get('/audit-logs', { params }),
  getEntityHistory: (entityType, entityId) => api.get(`/audit-logs/entity/${entityType}/${entityId}`),
  getSummary: (days = 7) => api.get(`/audit-logs/summary?days=${days}`)
};

// Material APIs
export const materialAPI = {
  getAll: (params) => api.get('/materials', { params }),
  getById: (id) => api.get(`/materials/${id}`),
  create: (data) => api.post('/materials', data),
  update: (id, data) => api.put(`/materials/${id}`, data),
  delete: (id) => api.delete(`/materials/${id}`),
  getCategories: () => api.get('/materials/categories/list')
};

// GRN APIs
export const grnAPI = {
  getAll: (params) => api.get('/grn', { params }),
  getById: (id) => api.get(`/grn/${id}`),
  create: (data) => api.post('/grn', data),
  complete: (id) => api.put(`/grn/${id}/complete`),
  updateInspection: (id, data) => api.put(`/grn/${id}/inspect`, data),
  getByMaterial: (materialId) => api.get(`/grn/by-material/${materialId}`),
  getVendors: () => api.get('/grn/vendors/list')
};

// Bin APIs
export const binAPI = {
  getAll: (params) => api.get('/bins', { params }),
  getById: (id) => api.get(`/bins/${id}`),
  create: (data) => api.post('/bins', data),
  update: (id, data) => api.put(`/bins/${id}`, data),
  updateStatus: (id, status) => api.put(`/bins/${id}/status?status=${status}`),
  getZones: () => api.get('/bins/zones/list')
};

// Putaway APIs
export const putawayAPI = {
  getAll: (params) => api.get('/putaway', { params }),
  create: (data) => api.post('/putaway', data),
  complete: (id) => api.put(`/putaway/${id}/complete`)
};

// Issue APIs
export const issueAPI = {
  getAll: (params) => api.get('/issues', { params }),
  getById: (id) => api.get(`/issues/${id}`),
  create: (data) => api.post('/issues', data),
  complete: (id) => api.put(`/issues/${id}/complete`)
};

// FIFO/LIFO Rule Engine APIs
export const fifoLifoAPI = {
  getRecommendation: (materialId, quantityNeeded) => 
    api.get(`/fifo-lifo/recommendation/${materialId}?quantity_needed=${quantityNeeded}`),
  validateSelection: (materialId, selectedBatch, quantity) => 
    api.post(`/fifo-lifo/validate-selection?material_id=${materialId}&selected_batch=${selectedBatch}&quantity=${quantity}`),
  logException: (data) => {
    const params = new URLSearchParams({
      material_id: data.material_id,
      selected_batch: data.selected_batch,
      recommended_batch: data.recommended_batch,
      override_reason: data.override_reason,
      ...(data.issue_id && { issue_id: data.issue_id }),
      ...(data.issue_number && { issue_number: data.issue_number })
    });
    return api.post(`/fifo-lifo/log-exception?${params.toString()}`);
  },
  getExceptions: (params) => api.get('/fifo-lifo/exceptions', { params }),
  getExceptionSummary: (days = 30) => api.get(`/fifo-lifo/exceptions/summary?days=${days}`),
  getMaterialConfig: (materialId) => api.get(`/fifo-lifo/material-config/${materialId}`),
  updateMaterialConfig: (materialId, stockMethod) => 
    api.put(`/fifo-lifo/material-config/${materialId}?stock_method=${stockMethod}`)
};

// Label APIs
export const labelAPI = {
  getAll: (params) => api.get('/labels', { params }),
  getById: (id) => api.get(`/labels/${id}`),
  create: (data) => api.post('/labels', data),
  getByGRN: (grnId) => api.get(`/labels/by-grn/${grnId}`),
  logPrint: (id, copies = 1) => api.post(`/labels/${id}/print?copies=${copies}`),
  logReprint: (id, data) => api.post(`/labels/${id}/reprint`, data),
  bulkPrint: (data) => api.post('/labels/bulk-print', data),
  getPrintHistory: (id) => api.get(`/labels/${id}/print-history`),
  getAllPrintLogs: (params) => api.get('/print-logs', { params })
};

// Movement APIs
export const movementAPI = {
  getAll: (params) => api.get('/movements', { params })
};

// Dashboard APIs
export const dashboardAPI = {
  getStats: () => api.get('/dashboard/stats'),
  stockSummary: () => api.get('/dashboard/stock-summary'),
  stockAging: () => api.get('/dashboard/stock-aging'),
  slowMoving: (days = 60) => api.get(`/dashboard/slow-moving?days_threshold=${days}`),
  binUtilization: () => api.get('/dashboard/bin-utilization'),
  fifoAlerts: () => api.get('/dashboard/fifo-alerts'),
  materialStock: () => api.get('/dashboard/material-stock')
};

// Report APIs
export const reportAPI = {
  getTypes: () => api.get('/reports/types'),
  // Individual reports with filters
  grnStock: (params) => api.get('/reports/grn-stock', { params }),
  batchStock: (params) => api.get('/reports/batch-stock', { params }),
  binStock: (params) => api.get('/reports/bin-stock', { params }),
  movementHistory: (params) => api.get('/reports/movement-history', { params }),
  fifoCompliance: (params) => api.get('/reports/fifo-compliance', { params }),
  nonFifoExceptions: (params) => api.get('/reports/non-fifo-exceptions', { params }),
  putawayPending: (params) => api.get('/reports/putaway-pending', { params }),
  stockAging: (params) => api.get('/reports/stock-aging', { params }),
  deadSlowStock: (params) => api.get('/reports/dead-slow-stock', { params }),
  dailySummary: (params) => api.get('/reports/daily-summary', { params }),
  userActivity: (params) => api.get('/reports/user-activity', { params }),
  reprintLog: (params) => api.get('/reports/reprint-log', { params }),
  stockReconciliation: (params) => api.get('/reports/stock-reconciliation', { params }),
  stockSummary: (params) => api.get('/reports/stock-summary', { params }),
  binUtilization: (params) => api.get('/reports/bin-utilization', { params }),
  // Export functions with token
  exportExcel: (reportType, params = {}) => {
    const token = localStorage.getItem('token');
    const queryParams = new URLSearchParams({ report_type: reportType, ...params });
    return `${API}/reports/export/excel?${queryParams.toString()}&token=${token}`;
  },
  exportPDF: (reportType, params = {}) => {
    const token = localStorage.getItem('token');
    const queryParams = new URLSearchParams({ report_type: reportType, ...params });
    return `${API}/reports/export/pdf?${queryParams.toString()}&token=${token}`;
  }
};

// Seed API
export const seedAPI = {
  seed: () => api.post('/seed')
};

export default api;
