<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useActivitiesStore } from '../stores/activities'
import { useEquipmentStore } from '../stores/equipment'
import { activitiesApi } from '../api/client'

const route = useRoute()
const router = useRouter()
const activitiesStore = useActivitiesStore()
const equipmentStore = useEquipmentStore()

const activity = ref(null)
const isLoading = ref(true)
const error = ref(null)
const isUpdating = ref(false)
const showEquipmentModal = ref(false)
const selectedGearId = ref('')

const activityId = computed(() => parseInt(route.params.id))

onMounted(async () => {
  await equipmentStore.fetchEquipment()
  await fetchActivity()
})

async function fetchActivity() {
  isLoading.value = true
  error.value = null

  try {
    const response = await activitiesApi.getById(activityId.value)
    activity.value = response
    selectedGearId.value = activity.value.gear_id || ''
  } catch (e) {
    console.error('Failed to fetch activity:', e)
    error.value = e.response?.data?.detail || 'Failed to load activity'
  } finally {
    isLoading.value = false
  }
}

async function updateEquipment() {
  isUpdating.value = true

  try {
    await activitiesStore.updateEquipment(activityId.value, selectedGearId.value || null)
    activity.value.gear_id = selectedGearId.value || null
    showEquipmentModal.value = false
  } catch (e) {
    console.error('Failed to update equipment:', e)
    error.value = e.response?.data?.detail || 'Failed to update equipment'
  } finally {
    isUpdating.value = false
  }
}

function openEquipmentModal() {
  selectedGearId.value = activity.value?.gear_id || ''
  showEquipmentModal.value = true
}

function getActivityIcon(type) {
  if (type?.includes('Ride')) return 'bike'
  if (type?.includes('Run')) return 'run'
  return 'other'
}

function formatPace(distance, time) {
  if (!distance || !time) return '-'
  const paceSeconds = time / (distance / 1000)
  const minutes = Math.floor(paceSeconds / 60)
  const seconds = Math.round(paceSeconds % 60)
  return `${minutes}:${seconds.toString().padStart(2, '0')} /km`
}

function formatSpeed(speed) {
  if (!speed) return '-'
  return `${(speed * 3.6).toFixed(1)} km/h`
}

function formatElevation(elevation) {
  if (!elevation) return '-'
  return `${Math.round(elevation)} m`
}
</script>

<template>
  <div class="p-8 max-w-4xl mx-auto">
    <!-- Back Button -->
    <button
      @click="router.push('/activities')"
      class="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-6"
    >
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
      </svg>
      Back to Activities
    </button>

    <!-- Loading State -->
    <div v-if="isLoading" class="card p-12 text-center">
      <svg class="w-8 h-8 text-strava-orange mx-auto mb-4 animate-spin" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      <p class="text-gray-500">Loading activity...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="card p-12 text-center">
      <svg class="w-12 h-12 text-red-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
      <p class="text-gray-600 mb-4">{{ error }}</p>
      <button @click="fetchActivity" class="btn btn-primary">Try Again</button>
    </div>

    <!-- Activity Details -->
    <template v-else-if="activity">
      <!-- Header -->
      <div class="card mb-6">
        <div class="flex items-start gap-4">
          <!-- Activity Icon -->
          <div
            class="w-14 h-14 rounded-xl flex items-center justify-center flex-shrink-0"
            :class="getActivityIcon(activity.activity_type) === 'bike' ? 'bg-strava-orange/10' : 'bg-blue-100'"
          >
            <svg v-if="getActivityIcon(activity.activity_type) === 'bike'" class="w-7 h-7 text-strava-orange" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <circle cx="5.5" cy="17.5" r="3.5" stroke-width="2"/>
              <circle cx="18.5" cy="17.5" r="3.5" stroke-width="2"/>
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 17.5l-2-6 4-3 3 1" />
            </svg>
            <svg v-else class="w-7 h-7 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>

          <!-- Title & Meta -->
          <div class="flex-1 min-w-0">
            <h1 class="text-2xl font-bold text-gray-900 mb-1">{{ activity.name }}</h1>
            <div class="flex flex-wrap items-center gap-3 text-sm text-gray-500">
              <span>{{ activitiesStore.formatDate(activity.start_date) }}</span>
              <span>{{ activitiesStore.formatTime(activity.start_date) }}</span>
              <span class="px-2 py-0.5 bg-gray-100 rounded text-gray-700">{{ activity.sport_type || activity.activity_type }}</span>
              <span v-if="activity.trainer" class="px-2 py-0.5 bg-blue-100 text-blue-700 rounded">Indoor</span>
              <span v-if="activity.commute" class="px-2 py-0.5 bg-green-100 text-green-700 rounded">Commute</span>
            </div>
          </div>

          <!-- Strava Link -->
          <a
            :href="`https://www.strava.com/activities/${activity.strava_activity_id}`"
            target="_blank"
            rel="noopener noreferrer"
            class="btn btn-outline text-sm"
          >
            <svg class="w-4 h-4 mr-2 inline" viewBox="0 0 24 24" fill="currentColor">
              <path d="M15.387 17.944l-2.089-4.116h-3.065L15.387 24l5.15-10.172h-3.066m-7.008-5.599l2.836 5.598h4.172L10.463 0l-7 13.828h4.169"/>
            </svg>
            View on Strava
          </a>
        </div>
      </div>

      <!-- Stats Grid -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div class="card text-center">
          <p class="text-sm text-gray-500 mb-1">Distance</p>
          <p class="text-2xl font-bold text-gray-900">{{ activitiesStore.formatDistance(activity.distance) }}</p>
        </div>
        <div class="card text-center">
          <p class="text-sm text-gray-500 mb-1">Duration</p>
          <p class="text-2xl font-bold text-gray-900">{{ activitiesStore.formatDuration(activity.moving_time) }}</p>
        </div>
        <div class="card text-center">
          <p class="text-sm text-gray-500 mb-1">Elevation</p>
          <p class="text-2xl font-bold text-gray-900">{{ formatElevation(activity.total_elevation_gain) }}</p>
        </div>
        <div class="card text-center">
          <p class="text-sm text-gray-500 mb-1">{{ activity.activity_type?.includes('Run') ? 'Pace' : 'Avg Speed' }}</p>
          <p class="text-2xl font-bold text-gray-900">
            {{ activity.activity_type?.includes('Run')
              ? formatPace(activity.distance, activity.moving_time)
              : formatSpeed(activity.average_speed)
            }}
          </p>
        </div>
      </div>

      <!-- Additional Stats -->
      <div class="card mb-6">
        <h2 class="text-lg font-semibold text-gray-900 mb-4">Details</h2>
        <div class="grid grid-cols-2 md:grid-cols-3 gap-y-4">
          <div>
            <p class="text-sm text-gray-500">Elapsed Time</p>
            <p class="font-medium text-gray-900">{{ activitiesStore.formatDuration(activity.elapsed_time) }}</p>
          </div>
          <div>
            <p class="text-sm text-gray-500">Max Speed</p>
            <p class="font-medium text-gray-900">{{ formatSpeed(activity.max_speed) }}</p>
          </div>
          <div>
            <p class="text-sm text-gray-500">Device</p>
            <p class="font-medium text-gray-900">{{ activity.device_name || '-' }}</p>
          </div>
          <div>
            <p class="text-sm text-gray-500">Activity Type</p>
            <p class="font-medium text-gray-900">{{ activity.activity_type }}</p>
          </div>
          <div>
            <p class="text-sm text-gray-500">Sport Type</p>
            <p class="font-medium text-gray-900">{{ activity.sport_type || '-' }}</p>
          </div>
          <div>
            <p class="text-sm text-gray-500">Manual Entry</p>
            <p class="font-medium text-gray-900">{{ activity.manual ? 'Yes' : 'No' }}</p>
          </div>
        </div>
      </div>

      <!-- Equipment Section -->
      <div class="card">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-semibold text-gray-900">Equipment</h2>
          <button @click="openEquipmentModal" class="btn btn-outline text-sm">
            Change Equipment
          </button>
        </div>

        <div v-if="activity.gear_id" class="flex items-center gap-4 p-4 bg-gray-50 rounded-lg">
          <div class="w-12 h-12 bg-strava-orange/10 rounded-lg flex items-center justify-center">
            <svg class="w-6 h-6 text-strava-orange" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <circle cx="5.5" cy="17.5" r="3.5" stroke-width="2"/>
              <circle cx="18.5" cy="17.5" r="3.5" stroke-width="2"/>
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 17.5l-2-6 4-3 3 1" />
            </svg>
          </div>
          <div>
            <p class="font-medium text-gray-900">{{ equipmentStore.getEquipmentName(activity.gear_id) }}</p>
            <p class="text-sm text-gray-500">
              {{ equipmentStore.formatDistance(equipmentStore.getEquipmentById(activity.gear_id)?.distance) }} total
            </p>
          </div>
        </div>

        <div v-else class="p-4 bg-gray-50 rounded-lg text-center">
          <p class="text-gray-500">No equipment assigned</p>
          <button @click="openEquipmentModal" class="mt-2 text-strava-orange hover:underline text-sm">
            Assign equipment
          </button>
        </div>
      </div>
    </template>

    <!-- Equipment Modal -->
    <div v-if="showEquipmentModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white rounded-xl shadow-xl max-w-md w-full mx-4 p-6">
        <h3 class="text-lg font-semibold text-gray-900 mb-4">Change Equipment</h3>

        <div class="mb-6">
          <label class="label">Equipment</label>
          <select v-model="selectedGearId" class="input">
            <option value="">No equipment</option>
            <optgroup label="Bikes">
              <option v-for="eq in equipmentStore.activeBikes" :key="eq.id" :value="eq.id">
                {{ eq.name }}
              </option>
            </optgroup>
            <optgroup label="Shoes">
              <option v-for="eq in equipmentStore.activeShoes" :key="eq.id" :value="eq.id">
                {{ eq.name }}
              </option>
            </optgroup>
          </select>
        </div>

        <div class="flex gap-3">
          <button @click="showEquipmentModal = false" class="btn btn-secondary flex-1">
            Cancel
          </button>
          <button
            @click="updateEquipment"
            :disabled="isUpdating"
            class="btn btn-primary flex-1 disabled:opacity-50"
          >
            {{ isUpdating ? 'Updating...' : 'Save Changes' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
