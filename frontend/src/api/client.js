import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const client = axios.create({
  baseURL: `${API_URL}/api`,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Auth API
export const authApi = {
  getLoginUrl: () => `${API_URL}/api/auth/login`,

  getStatus: async () => {
    const response = await client.get('/auth/status')
    return response.data
  },

  logout: async () => {
    const response = await client.post('/auth/logout')
    return response.data
  },
}

// Activities API
export const activitiesApi = {
  getStats: async () => {
    const response = await client.get('/activities/stats')
    return response.data
  },

  getAll: async (filters = {}) => {
    const params = new URLSearchParams()
    if (filters.search) params.append('search', filters.search)
    if (filters.activityType) params.append('activity_type', filters.activityType)
    if (filters.equipmentId) params.append('equipment_id', filters.equipmentId)
    if (filters.trainer !== undefined && filters.trainer !== '') {
      params.append('trainer', filters.trainer)
    }
    if (filters.dateFrom) params.append('date_from', filters.dateFrom)
    if (filters.dateTo) params.append('date_to', filters.dateTo)
    if (filters.sortBy) params.append('sort_by', filters.sortBy)
    if (filters.sortOrder) params.append('sort_order', filters.sortOrder)
    if (filters.limit) params.append('limit', filters.limit)
    if (filters.offset !== undefined) params.append('offset', filters.offset)

    const response = await client.get(`/activities?${params.toString()}`)
    return response.data
  },

  getById: async (id) => {
    const response = await client.get(`/activities/${id}`)
    return response.data
  },

  updateEquipment: async (id, gearId) => {
    const response = await client.patch(`/activities/${id}/equipment`, {
      gear_id: gearId,
    })
    return response.data
  },

  bulkUpdateEquipment: async (activityIds, gearId) => {
    const response = await client.post('/activities/bulk-update', {
      activity_ids: activityIds,
      gear_id: gearId,
    })
    return response.data
  },

  sync: async (days = 30) => {
    const response = await client.post(`/activities/sync?days=${days}`)
    return response.data
  },

  startBackfill: async () => {
    const response = await client.post('/activities/backfill')
    return response.data
  },

  getBackfillStatus: async () => {
    const response = await client.get('/activities/backfill/status')
    return response.data
  },
}

// Equipment API
export const equipmentApi = {
  getAll: async (includeRetired = false) => {
    const response = await client.get(`/equipment?include_retired=${includeRetired}`)
    return response.data
  },

  getStats: async (includeRetired = false) => {
    const response = await client.get(`/equipment/stats?include_retired=${includeRetired}`)
    return response.data
  },

  getById: async (id) => {
    const response = await client.get(`/equipment/${id}`)
    return response.data
  },

  sync: async () => {
    const response = await client.post('/equipment/sync')
    return response.data
  },

  getUsageHistory: async (months = 6) => {
    const response = await client.get(`/equipment/usage-history?months=${months}`)
    return response.data
  },
}

// Rules API
export const rulesApi = {
  getAll: async () => {
    const response = await client.get('/rules')
    return response.data
  },

  getById: async (id) => {
    const response = await client.get(`/rules/${id}`)
    return response.data
  },

  create: async (rule) => {
    const response = await client.post('/rules', rule)
    return response.data
  },

  update: async (id, rule) => {
    const response = await client.put(`/rules/${id}`, rule)
    return response.data
  },

  delete: async (id) => {
    const response = await client.delete(`/rules/${id}`)
    return response.data
  },

  preview: async (id) => {
    const response = await client.post(`/rules/${id}/preview`)
    return response.data
  },

  apply: async (id, activityIds = null) => {
    const response = await client.post(`/rules/${id}/apply`, activityIds)
    return response.data
  },

  getApplyStatus: async (id) => {
    const response = await client.get(`/rules/${id}/apply/status`)
    return response.data
  },
}

export default client
