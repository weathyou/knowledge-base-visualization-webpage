import axios from 'axios'

const directOrigins = ['http://127.0.0.1:8000', 'http://localhost:8000', '']

const requestWithOrigins = async ({ url, method = 'get', data, timeoutMs = 8000 }) => {
  let lastError = null

  for (const baseURL of directOrigins) {
    try {
      const response = await axios.request({
        url,
        method,
        data,
        baseURL,
        timeout: timeoutMs,
      })
      return response.data
    } catch (error) {
      lastError = error
    }
  }

  throw lastError
}

export const getPlans = async () => {
  return requestWithOrigins({ url: '/api/plans', method: 'get', timeoutMs: 6000 })
}

export const getPlanById = async (id) => {
  return requestWithOrigins({ url: `/api/plans/${id}`, method: 'get', timeoutMs: 10000 })
}

export const getPlanDocument = async (id) => {
  return requestWithOrigins({ url: `/api/plans/${id}/document`, method: 'get', timeoutMs: 15000 })
}

export const getCategories = async () => {
  return requestWithOrigins({ url: '/api/categories', method: 'get', timeoutMs: 10000 })
}

export const createCategory = async (payload) => {
  return requestWithOrigins({ url: '/api/categories', method: 'post', data: payload, timeoutMs: 15000 })
}

export const movePlan = async (planId, payload) => {
  return requestWithOrigins({ url: `/api/plans/${planId}/move`, method: 'post', data: payload, timeoutMs: 30000 })
}

export const updateDocumentCell = async (planId, payload) => {
  return requestWithOrigins({ url: `/api/plans/${planId}/document/cell`, method: 'patch', data: payload, timeoutMs: 180000 })
}

export const syncPlans = async () => {
  return requestWithOrigins({ url: '/api/sync', method: 'post', timeoutMs: 180000 })
}
