import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.reload();
    }
    return Promise.reject(error);
  }
);

export const authService = {
  async register(userData) {
    const response = await api.post('/api/auth/register', userData);
    return response.data;
  },

  async login(email, password) {
    const response = await api.post('/api/auth/login', null, {
      params: { email, password },
    });
    return response.data.access_token;
  },

  async getCurrentUser() {
    const response = await api.get('/api/auth/me');
    return response.data;
  },
};

export const chatService = {
  async sendMessage(message, contextId = null) {
    const response = await api.post('/api/chat', {
      message,
      context_id: contextId,
    });
    return response.data;
  },

  async getHistory(limit = 50) {
    const response = await api.get('/api/chat/history', {
      params: { limit },
    });
    return response.data;
  },

  async saveConversation(conversationId, title = null) {
    const response = await api.post('/api/chat/save-conversation', {
      conversation_id: conversationId,
      title: title,
    });
    return response.data;
  },

  async uploadFile(formData) {
    const response = await api.post('/api/files/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  async sendMessageWithFiles(message, files, contextId = null) {
    const response = await api.post('/api/chat/with-files', {
      message,
      files,
      context_id: contextId,
    });
    return response.data;
  },
};

export default api;


