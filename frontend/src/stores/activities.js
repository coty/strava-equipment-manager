import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { activitiesApi } from '../api/client'
import { mockActivities, formatDistance, formatDuration, formatDate, formatTime } from '../data/mockActivities'

const USE_MOCK_DATA = import.meta.env.VITE_USE_MOCK_DATA === 'true'

export const useActivitiesStore = defineStore('activities', () => {
  const activities = ref([])
  const totalStats = ref({ total_activities: 0, total_distance: 0, total_time: 0 })
  const isLoading = ref(false)
  const isSyncing = ref(false)
  const error = ref(null)
  const backfillStatus = ref(null)
  const isBackfilling = ref(false)

  // Initialize with mock data if in mock mode
  if (USE_MOCK_DATA) {
    activities.value = [...mockActivities]
  }

  async function fetchActivities(filters = {}) {
    if (USE_MOCK_DATA) {
      // Filter mock data locally
      activities.value = mockActivities.filter(activity => {
        if (filters.search && !activity.name.toLowerCase().includes(filters.search.toLowerCase())) {
          return false
        }
        if (filters.activityType && activity.activity_type !== filters.activityType) {
          return false
        }
        if (filters.equipmentId && activity.gear_id !== filters.equipmentId) {
          return false
        }
        if (filters.trainer !== undefined && filters.trainer !== '') {
          const isTrainer = filters.trainer === 'true' || filters.trainer === true
          if (activity.trainer !== isTrainer) return false
        }
        if (filters.dateFrom) {
          const activityDate = new Date(activity.start_date)
          const fromDate = new Date(filters.dateFrom)
          if (activityDate < fromDate) return false
        }
        if (filters.dateTo) {
          const activityDate = new Date(activity.start_date)
          const toDate = new Date(filters.dateTo)
          toDate.setHours(23, 59, 59)
          if (activityDate > toDate) return false
        }
        return true
      })
      return
    }

    isLoading.value = true
    error.value = null

    try {
      const data = await activitiesApi.getAll(filters)
      activities.value = data
    } catch (e) {
      console.error('Failed to fetch activities:', e)
      error.value = e.response?.data?.detail || e.message
    } finally {
      isLoading.value = false
    }
  }

  async function syncFromStrava(days = 30) {
    if (USE_MOCK_DATA) {
      // Simulate sync delay
      isSyncing.value = true
      await new Promise(resolve => setTimeout(resolve, 1000))
      isSyncing.value = false
      return { synced: mockActivities.length, new: 0, updated: 0 }
    }

    isSyncing.value = true
    error.value = null

    try {
      const result = await activitiesApi.sync(days)
      // Refresh activities after sync
      await fetchActivities()
      return result
    } catch (e) {
      console.error('Failed to sync activities:', e)
      error.value = e.response?.data?.detail || e.message
      throw e
    } finally {
      isSyncing.value = false
    }
  }

  async function updateEquipment(activityId, gearId) {
    if (USE_MOCK_DATA) {
      const activity = activities.value.find(a => a.id === activityId)
      if (activity) {
        activity.gear_id = gearId
      }
      return
    }

    try {
      await activitiesApi.updateEquipment(activityId, gearId)
      const activity = activities.value.find(a => a.id === activityId)
      if (activity) {
        activity.gear_id = gearId
      }
    } catch (e) {
      console.error('Failed to update equipment:', e)
      error.value = e.response?.data?.detail || e.message
      throw e
    }
  }

  async function bulkUpdateEquipment(activityIds, gearId) {
    if (USE_MOCK_DATA) {
      activityIds.forEach(id => {
        const activity = activities.value.find(a => a.id === id)
        if (activity) {
          activity.gear_id = gearId
        }
      })
      return { updated: activityIds.length }
    }

    try {
      const result = await activitiesApi.bulkUpdateEquipment(activityIds, gearId)
      // Update local state
      activityIds.forEach(id => {
        const activity = activities.value.find(a => a.id === id)
        if (activity) {
          activity.gear_id = gearId
        }
      })
      return result
    } catch (e) {
      console.error('Failed to bulk update equipment:', e)
      error.value = e.response?.data?.detail || e.message
      throw e
    }
  }

  async function startBackfill() {
    if (USE_MOCK_DATA) {
      return { message: 'Backfill not available in mock mode' }
    }

    try {
      const result = await activitiesApi.startBackfill()
      isBackfilling.value = true
      backfillStatus.value = { status: 'running', activities_found: 0, pages_processed: 0 }
      return result
    } catch (e) {
      console.error('Failed to start backfill:', e)
      error.value = e.response?.data?.detail || e.message
      throw e
    }
  }

  async function checkBackfillStatus() {
    if (USE_MOCK_DATA) {
      return null
    }

    try {
      const status = await activitiesApi.getBackfillStatus()
      backfillStatus.value = status
      isBackfilling.value = status.status === 'running' || status.status === 'rate_limited'
      return status
    } catch (e) {
      console.error('Failed to get backfill status:', e)
      return null
    }
  }

  async function fetchStats() {
    if (USE_MOCK_DATA) {
      totalStats.value = { total_activities: mockActivities.length, total_distance: 0, total_time: 0 }
      return totalStats.value
    }

    try {
      const stats = await activitiesApi.getStats()
      totalStats.value = stats
      return stats
    } catch (e) {
      console.error('Failed to fetch stats:', e)
      return null
    }
  }

  return {
    activities,
    totalStats,
    isLoading,
    isSyncing,
    error,
    backfillStatus,
    isBackfilling,
    fetchActivities,
    fetchStats,
    syncFromStrava,
    updateEquipment,
    bulkUpdateEquipment,
    startBackfill,
    checkBackfillStatus,
    // Re-export utilities
    formatDistance,
    formatDuration,
    formatDate,
    formatTime
  }
})
