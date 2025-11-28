import axios from 'axios';

/**
 * API Configuration for LocalMind
 * Educational Note: We create an axios instance with base configuration
 * to avoid repeating the base URL and headers in every request.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api/v1';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor for debugging (educational purposes)
api.interceptors.request.use(
  (config) => {
    console.log('📤 API Request:', config.method?.toUpperCase(), config.url);
    return config;
  },
  (error) => {
    console.error('❌ Request Error:', error);
    return Promise.reject(error);
  }
);

// Add response interceptor for debugging
api.interceptors.response.use(
  (response) => {
    console.log('📥 API Response:', response.status, response.config.url);
    return response;
  },
  (error) => {
    console.error('❌ Response Error:', error.response?.status, error.response?.data);
    return Promise.reject(error);
  }
);

/**
 * Project API Methods
 * Educational Note: These methods abstract the API calls, making them
 * easier to use throughout the application and maintaining consistency.
 */
export const projectsAPI = {
  // List all projects
  list: () => api.get('/projects'),

  // Create a new project
  create: (data: { name: string; description?: string }) =>
    api.post('/projects', data),

  // Get a specific project
  get: (id: string) => api.get(`/projects/${id}`),

  // Update a project
  update: (id: string, data: { name?: string; description?: string }) =>
    api.put(`/projects/${id}`, data),

  // Delete a project
  delete: (id: string) => api.delete(`/projects/${id}`),

  // Open a project (mark as accessed)
  open: (id: string) => api.post(`/projects/${id}/open`),

  // Get project cost tracking data
  getCosts: (id: string) => api.get(`/projects/${id}/costs`),
};

/**
 * Cost Tracking Types
 * Educational Note: These types match the backend cost tracking structure.
 */
export interface ModelCostBreakdown {
  input_tokens: number;
  output_tokens: number;
  cost: number;
}

export interface CostTracking {
  total_cost: number;
  by_model: {
    sonnet: ModelCostBreakdown;
    haiku: ModelCostBreakdown;
  };
}