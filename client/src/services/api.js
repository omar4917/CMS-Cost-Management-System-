import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

const api = axios.create({
    baseURL: API_URL,
    headers: { 'Content-Type': 'application/json' },
});

// Add auth token to every request
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('cms_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// Handle 401 responses
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            localStorage.removeItem('cms_token');
            localStorage.removeItem('cms_user');
            window.location.href = '/login';
        }
        return Promise.reject(error);
    }
);

// Auth
export const authAPI = {
    login: (data) => api.post('/auth/login', data),
    getProfile: () => api.get('/auth/me'),
    updateProfile: (data) => api.put('/auth/profile', data),
    changePassword: (data) => api.put('/auth/change-password', data),
    getUsers: () => api.get('/auth/users'),
    createUser: (data) => api.post('/auth/users', data),
    updateUser: (id, data) => api.put(`/auth/users/${id}`, data),
};

// Dashboard
export const dashboardAPI = {
    getSummary: () => api.get('/dashboard/summary'),
    getRecentActivity: () => api.get('/dashboard/recent-activity'),
    getProjectProgress: () => api.get('/dashboard/project-progress'),
    getCostBreakdown: () => api.get('/dashboard/cost-breakdown'),
    getInvestmentOverview: () => api.get('/dashboard/investment-overview'),
    getUpcomingPayments: () => api.get('/dashboard/upcoming-payments'),
};

// Projects
export const projectAPI = {
    getAll: (params) => api.get('/projects', { params }),
    getById: (id) => api.get(`/projects/${id}`),
    create: (data) => api.post('/projects', data),
    update: (id, data) => api.put(`/projects/${id}`, data),
    delete: (id) => api.delete(`/projects/${id}`),
    addMilestone: (projectId, data) => api.post(`/projects/${projectId}/milestones`, data),
    updateMilestone: (projectId, id, data) => api.put(`/projects/${projectId}/milestones/${id}`, data),
    deleteMilestone: (projectId, id) => api.delete(`/projects/${projectId}/milestones/${id}`),
    getCosts: (projectId, params) => api.get(`/projects/${projectId}/costs`, { params }),
    addCost: (projectId, data) => api.post(`/projects/${projectId}/costs`, data),
};

// Cost Categories
export const costCategoryAPI = {
    getAll: () => api.get('/cost-categories'),
    create: (data) => api.post('/cost-categories', data),
    update: (id, data) => api.put(`/cost-categories/${id}`, data),
};

// Investors
export const investorAPI = {
    getAll: (params) => api.get('/investors', { params }),
    getById: (id) => api.get(`/investors/${id}`),
    create: (data) => api.post('/investors', data),
    update: (id, data) => api.put(`/investors/${id}`, data),
    delete: (id) => api.delete(`/investors/${id}`),
};

// Investor Types
export const investorTypeAPI = {
    getAll: () => api.get('/investor-types'),
    create: (data) => api.post('/investor-types', data),
    update: (id, data) => api.put(`/investor-types/${id}`, data),
};

// Investments
export const investmentAPI = {
    getAll: (params) => api.get('/investments', { params }),
    create: (data) => api.post('/investments', data),
    update: (id, data) => api.put(`/investments/${id}`, data),
    delete: (id) => api.delete(`/investments/${id}`),
};

// Cost Items
export const costItemAPI = {
    update: (id, data) => api.put(`/costs/${id}`, data),
    delete: (id) => api.delete(`/costs/${id}`),
};

// Payment Schedules
export const paymentScheduleAPI = {
    getAll: (params) => api.get('/payment-schedules', { params }),
    create: (data) => api.post('/payment-schedules', data),
    update: (id, data) => api.put(`/payment-schedules/${id}`, data),
};

// Contractors
export const contractorAPI = {
    getAll: (params) => api.get('/contractors', { params }),
    create: (data) => api.post('/contractors', data),
    update: (id, data) => api.put(`/contractors/${id}`, data),
    delete: (id) => api.delete(`/contractors/${id}`),
    getPayments: (id) => api.get(`/contractors/${id}/payments`),
    addPayment: (id, data) => api.post(`/contractors/${id}/payments`, data),
};

// Currencies
export const currencyAPI = {
    getAll: () => api.get('/currencies'),
    update: (id, data) => api.put(`/currencies/${id}`, data),
};

// Documents
export const documentAPI = {
    getAll: (params) => api.get('/documents', { params }),
    upload: (formData) => api.post('/documents', formData, { headers: { 'Content-Type': 'multipart/form-data' } }),
    download: (id) => api.get(`/documents/${id}/download`, { responseType: 'blob' }),
    delete: (id) => api.delete(`/documents/${id}`),
};

// Emails
export const emailAPI = {
    send: (data) => api.post('/emails/send', data),
    getTemplates: () => api.get('/emails/templates'),
    getLogs: () => api.get('/emails/logs'),
    getAutomationRules: () => api.get('/emails/automation-rules'),
};

// Audit Logs
export const auditLogAPI = {
    getAll: (params) => api.get('/audit-logs', { params }),
};

// Notes
export const noteAPI = {
    getAll: (params) => api.get('/notes', { params }),
    create: (data) => api.post('/notes', data),
};

// Settings
export const settingsAPI = {
    getAll: (params) => api.get('/settings', { params }),
    update: (data) => api.put('/settings', data),
};

// Backup
export const backupAPI = {
    create: () => api.post('/backup/create'),
    list: () => api.get('/backup/list'),
    download: (filename) => api.get(`/backup/download/${filename}`, { responseType: 'blob' }),
};

export default api;
