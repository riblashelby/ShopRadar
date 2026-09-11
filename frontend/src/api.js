import axios from 'axios'

const API_BASE_URL = '/api/v1'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Stores API
export const storesApi = {
  list: () => api.get('/stores').then(res => res.data),
  get: (id) => api.get(`/stores/${id}`).then(res => res.data),
  create: (data) => api.post('/stores', data).then(res => res.data),
  update: (id, data) => api.put(`/stores/${id}`, data).then(res => res.data),
  delete: (id) => api.delete(`/stores/${id}`).then(res => res.data),
  getChains: () => api.get('/stores/chains').then(res => res.data),
}

// Search API
export const searchApi = {
  search: (query, options = {}) => 
    api.post('/search', { query, ...options }).then(res => res.data),
  getHistory: (limit = 20) => 
    api.get(`/search/history?limit=${limit}`).then(res => res.data),
}

// Products API
export const productsApi = {
  get: (id) => api.get(`/products/${id}`).then(res => res.data),
  getByStore: (storeId, limit = 50) => 
    api.get(`/products/store/${storeId}?limit=${limit}`).then(res => res.data),
}

// Shopping Lists API
export const shoppingListsApi = {
  list: () => api.get('/shopping-lists').then(res => res.data),
  get: (id) => api.get(`/shopping-lists/${id}`).then(res => res.data),
  create: (data) => api.post('/shopping-lists', data).then(res => res.data),
  update: (id, data) => api.put(`/shopping-lists/${id}`, data).then(res => res.data),
  delete: (id) => api.delete(`/shopping-lists/${id}`).then(res => res.data),
}

// Favorites API
export const favoritesApi = {
  list: () => api.get('/favorites').then(res => res.data),
  add: (data) => api.post('/favorites', data).then(res => res.data),
  delete: (id) => api.delete(`/favorites/${id}`).then(res => res.data),
}

export default api
