<script setup>
import { ref, computed, onMounted, watch, onUnmounted } from 'vue'
import { Chart, registerables } from 'chart.js'
import { useEquipmentStore } from '../stores/equipment'
import { equipmentApi } from '../api/client'

Chart.register(...registerables)

const equipmentStore = useEquipmentStore()

const showRetired = ref(false)
const chartRef = ref(null)
const usageHistory = ref(null)
let chartInstance = null

// Fetch data on mount
onMounted(async () => {
  await equipmentStore.fetchEquipment(showRetired.value)
  await fetchUsageHistory()
  initChart()
})

async function fetchUsageHistory() {
  try {
    usageHistory.value = await equipmentApi.getUsageHistory(6)
  } catch (e) {
    console.error('Failed to fetch usage history:', e)
  }
}

// Watch showRetired and refetch
watch(showRetired, async (newValue) => {
  await equipmentStore.fetchEquipment(newValue)
  updateChart()
})

// Cleanup chart on unmount
onUnmounted(() => {
  if (chartInstance) {
    chartInstance.destroy()
  }
})

const filteredEquipment = computed(() => {
  if (showRetired.value) {
    return equipmentStore.equipment
  }
  return equipmentStore.equipment.filter(e => !e.is_retired)
})

const bikes = computed(() => filteredEquipment.value.filter(e => e.equipment_type === 'bike'))
const shoes = computed(() => filteredEquipment.value.filter(e => e.equipment_type === 'shoes'))

function initChart() {
  if (!chartRef.value) return

  const ctx = chartRef.value.getContext('2d')
  const colors = ['#FC4C02', '#3B82F6', '#10B981', '#8B5CF6', '#F59E0B', '#EF4444']

  // Use real data from API or fallback to empty chart
  let labels = []
  let datasets = []

  if (usageHistory.value && usageHistory.value.labels) {
    // Format month labels for display (e.g., "2024-09" -> "Sep 24")
    labels = usageHistory.value.labels.map(label => {
      const [year, month] = label.split('-')
      const date = new Date(year, parseInt(month) - 1)
      return date.toLocaleDateString('en-US', { month: 'short', year: '2-digit' })
    })

    datasets = usageHistory.value.datasets.map((dataset, index) => ({
      label: dataset.equipment_name,
      data: dataset.data,
      borderColor: colors[index % colors.length],
      backgroundColor: colors[index % colors.length] + '20',
      fill: true,
      tension: 0.3
    }))
  }

  chartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom'
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: 'Distance (km)'
          }
        }
      }
    }
  })
}

function updateChart() {
  if (chartInstance) {
    chartInstance.destroy()
  }
  initChart()
}

async function syncEquipment() {
  try {
    await equipmentStore.syncFromStrava()
  } catch (e) {
    console.error('Failed to sync:', e)
  }
}
</script>

<template>
  <div class="p-8">
    <!-- Header -->
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Equipment</h1>
        <p class="text-gray-600">{{ filteredEquipment.length }} pieces of equipment</p>
      </div>
      <div class="flex items-center gap-4">
        <label class="flex items-center gap-2 text-sm text-gray-600">
          <input
            v-model="showRetired"
            type="checkbox"
            class="rounded border-gray-300 text-strava-orange focus:ring-strava-orange"
          />
          Show retired
        </label>
        <button
          @click="syncEquipment"
          :disabled="equipmentStore.isSyncing"
          class="btn btn-outline disabled:opacity-50"
        >
          <svg
            class="w-4 h-4 mr-2 inline"
            :class="{ 'animate-spin': equipmentStore.isSyncing }"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          {{ equipmentStore.isSyncing ? 'Syncing...' : 'Sync from Strava' }}
        </button>
      </div>
    </div>

    <!-- Error Alert -->
    <div v-if="equipmentStore.error" class="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700">
      {{ equipmentStore.error }}
    </div>

    <!-- Loading State -->
    <div v-if="equipmentStore.isLoading" class="card p-12 text-center">
      <svg class="w-8 h-8 text-strava-orange mx-auto mb-4 animate-spin" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      <p class="text-gray-500">Loading equipment...</p>
    </div>

    <template v-else>
      <!-- Usage Chart -->
      <div class="card mb-8">
        <h2 class="text-lg font-semibold text-gray-900 mb-4">Usage Over Time</h2>
        <div class="h-64">
          <canvas ref="chartRef"></canvas>
        </div>
      </div>

      <!-- Bikes Section -->
      <div class="mb-8">
        <h2 class="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <svg class="w-5 h-5 text-strava-orange" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <circle cx="5.5" cy="17.5" r="3.5" stroke-width="2"/>
            <circle cx="18.5" cy="17.5" r="3.5" stroke-width="2"/>
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 17.5l-2-6 4-3 3 1" />
          </svg>
          Bikes
        </h2>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div
            v-for="bike in bikes"
            :key="bike.id"
            class="card"
            :class="{ 'opacity-60': bike.is_retired }"
          >
            <div class="flex items-start justify-between mb-4">
              <div>
                <div class="flex items-center gap-2">
                  <h3 class="font-semibold text-gray-900">{{ bike.name }}</h3>
                  <span v-if="bike.is_primary" class="px-2 py-0.5 text-xs font-medium bg-strava-orange text-white rounded">
                    Primary
                  </span>
                  <span v-if="bike.is_retired" class="px-2 py-0.5 text-xs font-medium bg-gray-400 text-white rounded">
                    Retired
                  </span>
                </div>
                <p class="text-sm text-gray-500">{{ bike.brand_name }} {{ bike.model_name }}</p>
              </div>
            </div>

            <!-- Stats -->
            <div class="grid grid-cols-3 gap-4 mb-4">
              <div>
                <p class="text-xs text-gray-500">Distance</p>
                <p class="font-semibold text-gray-900">{{ equipmentStore.formatDistance(bike.distance) }}</p>
              </div>
              <div>
                <p class="text-xs text-gray-500">Activities</p>
                <p class="font-semibold text-gray-900">{{ equipmentStore.getActivityCount(bike.id) }}</p>
              </div>
              <div>
                <p class="text-xs text-gray-500">Time</p>
                <p class="font-semibold text-gray-900">{{ equipmentStore.getTotalTime(bike.id) }}</p>
              </div>
            </div>

            <!-- Usage Bar -->
            <div class="mb-4">
              <div class="flex justify-between text-xs text-gray-500 mb-1">
                <span>Usage</span>
                <span>{{ Math.round(equipmentStore.getUsagePercentage(bike)) }}%</span>
              </div>
              <div class="h-2 bg-gray-100 rounded-full overflow-hidden">
                <div
                  class="h-full bg-strava-orange rounded-full transition-all duration-500"
                  :style="{ width: `${equipmentStore.getUsagePercentage(bike)}%` }"
                ></div>
              </div>
            </div>

            <!-- Description -->
            <p v-if="bike.description" class="text-sm text-gray-500">{{ bike.description }}</p>
          </div>
        </div>
      </div>

      <!-- Shoes Section -->
      <div>
        <h2 class="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
          Shoes
        </h2>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div
            v-for="shoe in shoes"
            :key="shoe.id"
            class="card"
            :class="{ 'opacity-60': shoe.is_retired }"
          >
            <div class="flex items-start justify-between mb-4">
              <div>
                <div class="flex items-center gap-2">
                  <h3 class="font-semibold text-gray-900">{{ shoe.name }}</h3>
                  <span v-if="shoe.is_primary" class="px-2 py-0.5 text-xs font-medium bg-blue-600 text-white rounded">
                    Primary
                  </span>
                  <span v-if="shoe.is_retired" class="px-2 py-0.5 text-xs font-medium bg-gray-400 text-white rounded">
                    Retired
                  </span>
                </div>
                <p class="text-sm text-gray-500">{{ shoe.brand_name }} {{ shoe.model_name }}</p>
              </div>
            </div>

            <!-- Stats -->
            <div class="grid grid-cols-3 gap-4 mb-4">
              <div>
                <p class="text-xs text-gray-500">Distance</p>
                <p class="font-semibold text-gray-900">{{ equipmentStore.formatDistance(shoe.distance) }}</p>
              </div>
              <div>
                <p class="text-xs text-gray-500">Activities</p>
                <p class="font-semibold text-gray-900">{{ equipmentStore.getActivityCount(shoe.id) }}</p>
              </div>
              <div>
                <p class="text-xs text-gray-500">Time</p>
                <p class="font-semibold text-gray-900">{{ equipmentStore.getTotalTime(shoe.id) }}</p>
              </div>
            </div>

            <!-- Shoe wear indicator -->
            <div class="mb-4">
              <div class="flex justify-between text-xs text-gray-500 mb-1">
                <span>Wear (est. 800km lifespan)</span>
                <span>{{ Math.min(Math.round((shoe.distance || 0) / 8000), 100) }}%</span>
              </div>
              <div class="h-2 bg-gray-100 rounded-full overflow-hidden">
                <div
                  class="h-full rounded-full transition-all duration-500"
                  :class="{
                    'bg-green-500': (shoe.distance || 0) < 400000,
                    'bg-yellow-500': (shoe.distance || 0) >= 400000 && (shoe.distance || 0) < 600000,
                    'bg-red-500': (shoe.distance || 0) >= 600000
                  }"
                  :style="{ width: `${Math.min(((shoe.distance || 0) / 800000) * 100, 100)}%` }"
                ></div>
              </div>
            </div>

            <!-- Description -->
            <p v-if="shoe.description" class="text-sm text-gray-500">{{ shoe.description }}</p>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-if="filteredEquipment.length === 0" class="card text-center py-12">
        <svg class="w-12 h-12 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
        </svg>
        <p class="text-gray-500">No equipment found</p>
        <button @click="syncEquipment" class="mt-2 text-strava-orange hover:underline">
          Sync from Strava
        </button>
      </div>
    </template>
  </div>
</template>
