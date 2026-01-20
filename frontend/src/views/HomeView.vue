<script setup>
import { ref, computed, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useActivitiesStore } from '../stores/activities'
import { useEquipmentStore } from '../stores/equipment'
import { useRulesStore } from '../stores/rules'
import { activitiesApi } from '../api/client'

const authStore = useAuthStore()
const activitiesStore = useActivitiesStore()
const equipmentStore = useEquipmentStore()
const rulesStore = useRulesStore()

const activityStats = ref({ total_activities: 0, total_distance: 0, total_time: 0 })

onMounted(async () => {
  if (authStore.isAuthenticated) {
    await Promise.all([
      activitiesStore.fetchActivities(),
      equipmentStore.fetchEquipment(),
      rulesStore.fetchRules(),
      fetchActivityStats()
    ])
  }
})

async function fetchActivityStats() {
  try {
    activityStats.value = await activitiesApi.getStats()
  } catch (e) {
    console.error('Failed to fetch activity stats:', e)
  }
}

const recentActivities = computed(() => activitiesStore.activities.slice(0, 5))

const stats = computed(() => {
  const activeEquipment = equipmentStore.activeEquipment.length
  const activeRules = rulesStore.rules.filter(r => r.is_active).length

  return {
    totalActivities: activityStats.value.total_activities,
    totalDistance: activityStats.value.total_distance,
    totalTime: activityStats.value.total_time,
    activeEquipment,
    activeRules,
  }
})

const isLoading = computed(() =>
  activitiesStore.isLoading || equipmentStore.isLoading || rulesStore.isLoading
)

async function syncActivities() {
  try {
    await activitiesStore.syncFromStrava(30)
  } catch (e) {
    console.error('Failed to sync:', e)
  }
}
</script>

<template>
  <div class="p-8">
    <!-- Header -->
    <div class="mb-8">
      <h1 class="text-2xl font-bold text-gray-900">Dashboard</h1>
      <p class="text-gray-600">Manage your Strava equipment assignments</p>
    </div>

    <!-- Not Authenticated State -->
    <div v-if="!authStore.isAuthenticated" class="card text-center py-12">
      <svg class="w-16 h-16 text-strava-orange mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
      <h2 class="text-xl font-semibold text-gray-900 mb-2">Connect to Strava</h2>
      <p class="text-gray-600 mb-6 max-w-md mx-auto">
        Connect your Strava account to start managing your equipment assignments automatically.
      </p>
      <button @click="authStore.login" class="btn btn-primary">
        Connect with Strava
      </button>
    </div>

    <!-- Loading State -->
    <div v-else-if="isLoading" class="card p-12 text-center">
      <svg class="w-8 h-8 text-strava-orange mx-auto mb-4 animate-spin" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      <p class="text-gray-500">Loading your data...</p>
    </div>

    <!-- Authenticated Dashboard -->
    <template v-else>
      <!-- Stats Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        <!-- Activities Card -->
        <div class="card">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-gray-500">Total Activities</p>
              <p class="text-2xl font-bold text-gray-900">{{ stats.totalActivities }}</p>
            </div>
            <div class="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <svg class="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
          </div>
          <div class="mt-4 flex gap-4 text-sm text-gray-500">
            <span>{{ activitiesStore.formatDistance(stats.totalDistance) }}</span>
            <span>{{ activitiesStore.formatDuration(stats.totalTime) }}</span>
          </div>
        </div>

        <!-- Equipment Card -->
        <div class="card">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-gray-500">Active Equipment</p>
              <p class="text-2xl font-bold text-gray-900">{{ stats.activeEquipment }}</p>
            </div>
            <div class="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
              <svg class="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
              </svg>
            </div>
          </div>
          <div class="mt-4">
            <RouterLink to="/equipment" class="text-sm text-strava-orange hover:underline">
              View all equipment →
            </RouterLink>
          </div>
        </div>

        <!-- Rules Card -->
        <div class="card">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-gray-500">Active Rules</p>
              <p class="text-2xl font-bold text-gray-900">{{ stats.activeRules }}</p>
            </div>
            <div class="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
              <svg class="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
              </svg>
            </div>
          </div>
          <div class="mt-4">
            <RouterLink to="/rules" class="text-sm text-strava-orange hover:underline">
              Manage rules →
            </RouterLink>
          </div>
        </div>
      </div>

      <!-- Empty State for No Activities -->
      <div v-if="recentActivities.length === 0" class="card text-center py-12 mb-8">
        <svg class="w-12 h-12 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
        <h3 class="text-lg font-semibold text-gray-900 mb-2">No activities yet</h3>
        <p class="text-gray-600 mb-4">Sync your activities from Strava to get started</p>
        <button @click="syncActivities" :disabled="activitiesStore.isSyncing" class="btn btn-primary">
          {{ activitiesStore.isSyncing ? 'Syncing...' : 'Sync from Strava' }}
        </button>
      </div>

      <!-- Recent Activities -->
      <div v-else class="card">
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-lg font-semibold text-gray-900">Recent Activities</h2>
          <RouterLink to="/activities" class="text-sm text-strava-orange hover:underline">
            View all →
          </RouterLink>
        </div>

        <div class="space-y-4">
          <div
            v-for="activity in recentActivities"
            :key="activity.id"
            class="flex items-center gap-4 p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <!-- Activity Type Icon -->
            <div class="w-10 h-10 rounded-lg flex items-center justify-center"
                 :class="activity.activity_type.includes('Ride') ? 'bg-strava-orange/10' : 'bg-blue-100'">
              <svg v-if="activity.activity_type.includes('Ride')" class="w-5 h-5 text-strava-orange" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <circle cx="5.5" cy="17.5" r="3.5" stroke-width="2"/>
                <circle cx="18.5" cy="17.5" r="3.5" stroke-width="2"/>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 17.5l-2-6 4-3 3 1" />
              </svg>
              <svg v-else class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>

            <!-- Activity Details -->
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2">
                <p class="font-medium text-gray-900 truncate">{{ activity.name }}</p>
                <span v-if="activity.trainer" class="px-2 py-0.5 text-xs font-medium bg-blue-100 text-blue-700 rounded">
                  Indoor
                </span>
              </div>
              <p class="text-sm text-gray-500">
                {{ activitiesStore.formatDate(activity.start_date) }} at {{ activitiesStore.formatTime(activity.start_date) }}
              </p>
            </div>

            <!-- Stats -->
            <div class="text-right text-sm">
              <p class="font-medium text-gray-900">{{ activitiesStore.formatDistance(activity.distance) }}</p>
              <p class="text-gray-500">{{ activitiesStore.formatDuration(activity.moving_time) }}</p>
            </div>

            <!-- Equipment -->
            <div class="w-40 text-right">
              <p class="text-sm text-gray-600 truncate">{{ equipmentStore.getEquipmentName(activity.gear_id) }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Quick Actions -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mt-8">
        <div class="card">
          <h3 class="font-semibold text-gray-900 mb-2">Sync Activities</h3>
          <p class="text-sm text-gray-600 mb-4">Import your latest activities from Strava</p>
          <button
            @click="syncActivities"
            :disabled="activitiesStore.isSyncing"
            class="btn btn-outline w-full disabled:opacity-50"
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
            {{ activitiesStore.isSyncing ? 'Syncing...' : 'Sync from Strava' }}
          </button>
        </div>

        <div class="card">
          <h3 class="font-semibold text-gray-900 mb-2">Create Rule</h3>
          <p class="text-sm text-gray-600 mb-4">Set up automatic equipment assignment rules</p>
          <RouterLink to="/rules" class="btn btn-outline w-full inline-block text-center">
            <svg class="w-4 h-4 mr-2 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            New Rule
          </RouterLink>
        </div>
      </div>
    </template>
  </div>
</template>
