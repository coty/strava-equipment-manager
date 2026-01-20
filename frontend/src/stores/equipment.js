import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { equipmentApi } from '../api/client'
import { mockEquipment, formatDistance } from '../data/mockEquipment'
import { mockActivities } from '../data/mockActivities'

const USE_MOCK_DATA = import.meta.env.VITE_USE_MOCK_DATA === 'true'

export const useEquipmentStore = defineStore('equipment', () => {
  const equipment = ref([])
  const isLoading = ref(false)
  const isSyncing = ref(false)
  const error = ref(null)

  // Initialize with mock data if in mock mode
  if (USE_MOCK_DATA) {
    equipment.value = [...mockEquipment]
  }

  const bikes = computed(() => equipment.value.filter(e => e.equipment_type === 'bike'))
  const shoes = computed(() => equipment.value.filter(e => e.equipment_type === 'shoes'))
  const activeBikes = computed(() => bikes.value.filter(e => !e.is_retired))
  const activeShoes = computed(() => shoes.value.filter(e => !e.is_retired))
  const activeEquipment = computed(() => equipment.value.filter(e => !e.is_retired))

  async function fetchEquipment(includeRetired = false) {
    if (USE_MOCK_DATA) {
      if (includeRetired) {
        equipment.value = [...mockEquipment]
      } else {
        equipment.value = mockEquipment.filter(e => !e.is_retired)
      }
      return
    }

    isLoading.value = true
    error.value = null

    try {
      // Use stats endpoint to get equipment with activity counts
      const data = await equipmentApi.getStats(includeRetired)
      equipment.value = data
    } catch (e) {
      console.error('Failed to fetch equipment:', e)
      error.value = e.response?.data?.detail || e.message
    } finally {
      isLoading.value = false
    }
  }

  async function syncFromStrava() {
    if (USE_MOCK_DATA) {
      isSyncing.value = true
      await new Promise(resolve => setTimeout(resolve, 1000))
      isSyncing.value = false
      return { synced: mockEquipment.length }
    }

    isSyncing.value = true
    error.value = null

    try {
      const result = await equipmentApi.sync()
      await fetchEquipment(true)
      return result
    } catch (e) {
      console.error('Failed to sync equipment:', e)
      error.value = e.response?.data?.detail || e.message
      throw e
    } finally {
      isSyncing.value = false
    }
  }

  function getEquipmentById(id) {
    return equipment.value.find(e => e.id === id)
  }

  function getEquipmentName(gearId) {
    const eq = equipment.value.find(e => e.id === gearId)
    return eq?.name || 'Unknown'
  }

  // Stats functions for equipment view
  function getActivityCount(gearId) {
    if (USE_MOCK_DATA) {
      return mockActivities.filter(a => a.gear_id === gearId).length
    }
    // Get from equipment stats data
    const eq = equipment.value.find(e => e.id === gearId)
    return eq?.activity_count || 0
  }

  function getTotalTime(gearId) {
    if (USE_MOCK_DATA) {
      const activities = mockActivities.filter(a => a.gear_id === gearId)
      const totalSeconds = activities.reduce((sum, a) => sum + a.moving_time, 0)
      const hours = Math.floor(totalSeconds / 3600)
      return `${hours}h`
    }
    // Get from equipment stats data
    const eq = equipment.value.find(e => e.id === gearId)
    const totalSeconds = eq?.total_time || 0
    const hours = Math.floor(totalSeconds / 3600)
    const minutes = Math.floor((totalSeconds % 3600) / 60)
    if (hours > 0) {
      return `${hours}h ${minutes}m`
    }
    return `${minutes}m`
  }

  function getUsagePercentage(eq) {
    const maxDistance = Math.max(...equipment.value.map(e => e.distance || 0))
    if (maxDistance === 0) return 0
    return ((eq.distance || 0) / maxDistance) * 100
  }

  return {
    equipment,
    bikes,
    shoes,
    activeBikes,
    activeShoes,
    activeEquipment,
    isLoading,
    isSyncing,
    error,
    fetchEquipment,
    syncFromStrava,
    getEquipmentById,
    getEquipmentName,
    getActivityCount,
    getTotalTime,
    getUsagePercentage,
    formatDistance
  }
})
