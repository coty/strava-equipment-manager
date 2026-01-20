<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useActivitiesStore } from '../stores/activities'
import { useEquipmentStore } from '../stores/equipment'

const activitiesStore = useActivitiesStore()
const equipmentStore = useEquipmentStore()

const filters = ref({
  search: '',
  activityType: '',
  equipment: '',
  trainer: '',
  dateFrom: '',
  dateTo: ''
})

const selectedActivities = ref(new Set())
const showEquipmentModal = ref(false)
const newEquipmentId = ref('')
let backfillPollInterval = null

const activityTypes = ['Ride', 'VirtualRide', 'Run', 'GravelRide']

// Fetch data on mount
onMounted(async () => {
  await Promise.all([
    activitiesStore.fetchActivities(),
    activitiesStore.fetchStats(),
    equipmentStore.fetchEquipment(),
    activitiesStore.checkBackfillStatus()
  ])

  // Start polling if backfill is running
  if (activitiesStore.isBackfilling) {
    startBackfillPolling()
  }
})

onUnmounted(() => {
  stopBackfillPolling()
})

// Watch filters and refetch (debounced for real API)
let filterTimeout = null
watch(filters, () => {
  if (filterTimeout) clearTimeout(filterTimeout)
  filterTimeout = setTimeout(() => {
    activitiesStore.fetchActivities({
      search: filters.value.search,
      activityType: filters.value.activityType,
      equipmentId: filters.value.equipment,
      trainer: filters.value.trainer,
      dateFrom: filters.value.dateFrom,
      dateTo: filters.value.dateTo
    })
  }, 300)
}, { deep: true })

const filteredActivities = computed(() => activitiesStore.activities)
const allEquipment = computed(() => equipmentStore.activeEquipment)

function toggleSelectAll() {
  if (selectedActivities.value.size === filteredActivities.value.length) {
    selectedActivities.value.clear()
  } else {
    selectedActivities.value = new Set(filteredActivities.value.map(a => a.id))
  }
}

function toggleActivity(id) {
  if (selectedActivities.value.has(id)) {
    selectedActivities.value.delete(id)
  } else {
    selectedActivities.value.add(id)
  }
}

function clearFilters() {
  filters.value = {
    search: '',
    activityType: '',
    equipment: '',
    trainer: '',
    dateFrom: '',
    dateTo: ''
  }
}

function openEquipmentModal() {
  showEquipmentModal.value = true
}

async function updateEquipment() {
  try {
    await activitiesStore.bulkUpdateEquipment(
      Array.from(selectedActivities.value),
      newEquipmentId.value
    )
    showEquipmentModal.value = false
    selectedActivities.value.clear()
    newEquipmentId.value = ''
  } catch (e) {
    console.error('Failed to update equipment:', e)
  }
}

async function syncActivities() {
  try {
    await activitiesStore.syncFromStrava(30)
  } catch (e) {
    console.error('Failed to sync:', e)
  }
}

function startBackfillPolling() {
  backfillPollInterval = setInterval(async () => {
    const status = await activitiesStore.checkBackfillStatus()
    if (status && (status.status === 'completed' || status.status === 'error')) {
      stopBackfillPolling()
      // Refresh activities after backfill completes
      await activitiesStore.fetchActivities()
    }
  }, 2000)
}

function stopBackfillPolling() {
  if (backfillPollInterval) {
    clearInterval(backfillPollInterval)
    backfillPollInterval = null
  }
}

async function startBackfill() {
  try {
    await activitiesStore.startBackfill()
    startBackfillPolling()
  } catch (e) {
    console.error('Failed to start backfill:', e)
  }
}
</script>

<template>
  <div class="p-8">
    <!-- Header -->
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Activities</h1>
        <p class="text-gray-600">Showing {{ filteredActivities.length }} of {{ activitiesStore.totalStats.total_activities }} activities</p>
      </div>
      <div class="flex gap-2">
        <button
          @click="startBackfill"
          :disabled="activitiesStore.isBackfilling || activitiesStore.isSyncing"
          class="btn btn-secondary disabled:opacity-50"
          title="Fetch all historical activities from Strava"
        >
          <svg
            class="w-4 h-4 mr-2 inline"
            :class="{ 'animate-spin': activitiesStore.isBackfilling }"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
          </svg>
          {{ activitiesStore.isBackfilling ? 'Backfilling...' : 'Backfill All History' }}
        </button>
        <button
          @click="syncActivities"
          :disabled="activitiesStore.isSyncing || activitiesStore.isBackfilling"
          class="btn btn-outline disabled:opacity-50"
        >
          <svg
            class="w-4 h-4 mr-2 inline"
            :class="{ 'animate-spin': activitiesStore.isSyncing }"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          {{ activitiesStore.isSyncing ? 'Syncing...' : 'Sync Recent (30 days)' }}
        </button>
      </div>
    </div>

    <!-- Backfill Status Panel -->
    <div v-if="activitiesStore.backfillStatus && activitiesStore.backfillStatus.status !== 'not_started'" class="mb-6 p-4 rounded-xl border"
         :class="{
           'bg-blue-50 border-blue-200': activitiesStore.backfillStatus.status === 'running',
           'bg-yellow-50 border-yellow-200': activitiesStore.backfillStatus.status === 'rate_limited',
           'bg-green-50 border-green-200': activitiesStore.backfillStatus.status === 'completed',
           'bg-red-50 border-red-200': activitiesStore.backfillStatus.status === 'error'
         }">
      <div class="flex items-center justify-between">
        <div>
          <h3 class="font-medium"
              :class="{
                'text-blue-800': activitiesStore.backfillStatus.status === 'running',
                'text-yellow-800': activitiesStore.backfillStatus.status === 'rate_limited',
                'text-green-800': activitiesStore.backfillStatus.status === 'completed',
                'text-red-800': activitiesStore.backfillStatus.status === 'error'
              }">
            <span v-if="activitiesStore.backfillStatus.status === 'running'">Backfill in Progress</span>
            <span v-else-if="activitiesStore.backfillStatus.status === 'rate_limited'">Rate Limited - Waiting</span>
            <span v-else-if="activitiesStore.backfillStatus.status === 'completed'">Backfill Completed</span>
            <span v-else-if="activitiesStore.backfillStatus.status === 'error'">Backfill Error</span>
          </h3>
          <p class="text-sm text-gray-600 mt-1">
            Pages: {{ activitiesStore.backfillStatus.pages_processed || 0 }} |
            Activities found: {{ activitiesStore.backfillStatus.activities_found || 0 }} |
            Created: {{ activitiesStore.backfillStatus.created || 0 }} |
            Updated: {{ activitiesStore.backfillStatus.updated || 0 }}
          </p>
          <p v-if="activitiesStore.backfillStatus.errors?.length" class="text-sm text-red-600 mt-1">
            Errors: {{ activitiesStore.backfillStatus.errors.join(', ') }}
          </p>
        </div>
        <div v-if="activitiesStore.backfillStatus.status === 'running' || activitiesStore.backfillStatus.status === 'rate_limited'"
             class="animate-spin w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full"></div>
      </div>
    </div>

    <!-- Error Alert -->
    <div v-if="activitiesStore.error" class="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700">
      {{ activitiesStore.error }}
    </div>

    <!-- Filters -->
    <div class="card mb-6">
      <div class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <!-- Search -->
        <div class="lg:col-span-2">
          <label class="label">Search</label>
          <input
            v-model="filters.search"
            type="text"
            placeholder="Activity name..."
            class="input"
          />
        </div>

        <!-- Activity Type -->
        <div>
          <label class="label">Activity Type</label>
          <select v-model="filters.activityType" class="input">
            <option value="">All types</option>
            <option v-for="type in activityTypes" :key="type" :value="type">
              {{ type }}
            </option>
          </select>
        </div>

        <!-- Equipment -->
        <div>
          <label class="label">Equipment</label>
          <select v-model="filters.equipment" class="input">
            <option value="">All equipment</option>
            <option v-for="eq in allEquipment" :key="eq.id" :value="eq.id">
              {{ eq.name }}
            </option>
          </select>
        </div>

        <!-- Trainer -->
        <div>
          <label class="label">Indoor/Outdoor</label>
          <select v-model="filters.trainer" class="input">
            <option value="">All</option>
            <option value="true">Indoor only</option>
            <option value="false">Outdoor only</option>
          </select>
        </div>

        <!-- Date Range -->
        <div>
          <label class="label">Date From</label>
          <input
            v-model="filters.dateFrom"
            type="date"
            class="input"
          />
        </div>
      </div>

      <div class="mt-4 flex items-center gap-4">
        <button @click="clearFilters" class="text-sm text-gray-600 hover:text-gray-900">
          Clear filters
        </button>
      </div>
    </div>

    <!-- Bulk Actions -->
    <div v-if="selectedActivities.size > 0" class="bg-strava-orange/10 border border-strava-orange/20 rounded-xl p-4 mb-6 flex items-center justify-between">
      <p class="text-strava-orange font-medium">
        {{ selectedActivities.size }} activities selected
      </p>
      <div class="flex gap-2">
        <button @click="selectedActivities.clear()" class="btn btn-outline text-sm">
          Clear selection
        </button>
        <button @click="openEquipmentModal" class="btn btn-primary text-sm">
          Change Equipment
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="activitiesStore.isLoading" class="card p-12 text-center">
      <svg class="w-8 h-8 text-strava-orange mx-auto mb-4 animate-spin" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      <p class="text-gray-500">Loading activities...</p>
    </div>

    <!-- Activities Table -->
    <div v-else class="card overflow-hidden">
      <table class="w-full">
        <thead>
          <tr class="border-b border-gray-200">
            <th class="text-left p-4 w-10">
              <input
                type="checkbox"
                :checked="selectedActivities.size === filteredActivities.length && filteredActivities.length > 0"
                @change="toggleSelectAll"
                class="rounded border-gray-300 text-strava-orange focus:ring-strava-orange"
              />
            </th>
            <th class="text-left p-4 text-sm font-medium text-gray-600">Activity</th>
            <th class="text-left p-4 text-sm font-medium text-gray-600">Type</th>
            <th class="text-left p-4 text-sm font-medium text-gray-600">Date</th>
            <th class="text-right p-4 text-sm font-medium text-gray-600">Distance</th>
            <th class="text-right p-4 text-sm font-medium text-gray-600">Duration</th>
            <th class="text-left p-4 text-sm font-medium text-gray-600">Equipment</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="activity in filteredActivities"
            :key="activity.id"
            class="border-b border-gray-100 hover:bg-gray-50 transition-colors"
            :class="{ 'bg-strava-orange/5': selectedActivities.has(activity.id) }"
          >
            <td class="p-4">
              <input
                type="checkbox"
                :checked="selectedActivities.has(activity.id)"
                @change="toggleActivity(activity.id)"
                class="rounded border-gray-300 text-strava-orange focus:ring-strava-orange"
              />
            </td>
            <td class="p-4">
              <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-lg flex items-center justify-center"
                     :class="activity.activity_type.includes('Ride') ? 'bg-strava-orange/10' : 'bg-blue-100'">
                  <svg v-if="activity.activity_type.includes('Ride')" class="w-4 h-4 text-strava-orange" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <circle cx="5.5" cy="17.5" r="3.5" stroke-width="2"/>
                    <circle cx="18.5" cy="17.5" r="3.5" stroke-width="2"/>
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 17.5l-2-6 4-3 3 1" />
                  </svg>
                  <svg v-else class="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <div>
                  <router-link
                    :to="`/activities/${activity.id}`"
                    class="font-medium text-gray-900 hover:text-strava-orange transition-colors"
                  >
                    {{ activity.name }}
                  </router-link>
                  <p class="text-xs text-gray-500">{{ activity.device_name }}</p>
                </div>
              </div>
            </td>
            <td class="p-4">
              <div class="flex items-center gap-2">
                <span class="text-sm text-gray-600">{{ activity.sport_type }}</span>
                <span v-if="activity.trainer" class="px-2 py-0.5 text-xs font-medium bg-blue-100 text-blue-700 rounded">
                  Indoor
                </span>
              </div>
            </td>
            <td class="p-4 text-sm text-gray-600">
              <p>{{ activitiesStore.formatDate(activity.start_date) }}</p>
              <p class="text-xs text-gray-400">{{ activitiesStore.formatTime(activity.start_date) }}</p>
            </td>
            <td class="p-4 text-right text-sm font-medium text-gray-900">
              {{ activitiesStore.formatDistance(activity.distance) }}
            </td>
            <td class="p-4 text-right text-sm text-gray-600">
              {{ activitiesStore.formatDuration(activity.moving_time) }}
            </td>
            <td class="p-4">
              <span class="text-sm text-gray-600">{{ equipmentStore.getEquipmentName(activity.gear_id) }}</span>
            </td>
          </tr>
        </tbody>
      </table>

      <div v-if="filteredActivities.length === 0" class="p-12 text-center">
        <svg class="w-12 h-12 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <p class="text-gray-500">No activities match your filters</p>
        <button @click="clearFilters" class="mt-2 text-strava-orange hover:underline">
          Clear filters
        </button>
      </div>
    </div>

    <!-- Equipment Modal -->
    <div v-if="showEquipmentModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white rounded-xl shadow-xl max-w-md w-full mx-4 p-6">
        <h3 class="text-lg font-semibold text-gray-900 mb-4">Change Equipment</h3>
        <p class="text-gray-600 mb-4">
          Select new equipment for {{ selectedActivities.size }} selected activities:
        </p>

        <div class="mb-6">
          <label class="label">Equipment</label>
          <select v-model="newEquipmentId" class="input">
            <option value="">Select equipment...</option>
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
            :disabled="!newEquipmentId"
            class="btn btn-primary flex-1 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Update Equipment
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
