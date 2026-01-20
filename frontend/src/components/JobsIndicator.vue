<script setup>
import { ref } from 'vue'
import { useJobsStore } from '../stores/jobs'

const jobsStore = useJobsStore()
const showPanel = ref(false)

function getStatusColor(status) {
  switch (status) {
    case 'running':
    case 'starting':
      return 'text-strava-orange'
    case 'rate_limited':
      return 'text-yellow-500'
    case 'completed':
      return 'text-green-500'
    case 'failed':
    case 'error':
      return 'text-red-500'
    default:
      return 'text-gray-500'
  }
}

function getStatusText(status) {
  switch (status) {
    case 'running':
      return 'Running'
    case 'starting':
      return 'Starting'
    case 'rate_limited':
      return 'Rate Limited'
    case 'completed':
      return 'Completed'
    case 'failed':
    case 'error':
      return 'Failed'
    default:
      return status
  }
}

function formatTime(isoString) {
  const date = new Date(isoString)
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}
</script>

<template>
  <div class="relative">
    <!-- Indicator Button -->
    <button
      @click="showPanel = !showPanel"
      class="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-gray-100 transition-colors"
      :class="{ 'bg-gray-100': showPanel }"
    >
      <!-- Activity indicator -->
      <div class="relative">
        <svg class="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        <!-- Active job badge -->
        <span
          v-if="jobsStore.hasActiveJobs"
          class="absolute -top-1 -right-1 w-3 h-3 bg-strava-orange rounded-full animate-pulse"
        ></span>
      </div>
      <span class="text-sm text-gray-700">Jobs</span>
      <span
        v-if="jobsStore.activeJobs.length > 0"
        class="text-xs font-medium text-strava-orange"
      >
        {{ jobsStore.activeJobs.length }}
      </span>
    </button>

    <!-- Jobs Panel -->
    <div
      v-if="showPanel"
      class="absolute bottom-full left-0 mb-2 w-80 bg-white rounded-xl shadow-xl border border-gray-200 overflow-hidden z-50"
    >
      <div class="p-4 border-b border-gray-200 flex items-center justify-between">
        <h3 class="font-semibold text-gray-900">Background Jobs</h3>
        <button
          v-if="jobsStore.recentJobs.some(j => ['completed', 'failed', 'error'].includes(j.status))"
          @click="jobsStore.clearCompletedJobs()"
          class="text-xs text-gray-500 hover:text-gray-700"
        >
          Clear completed
        </button>
      </div>

      <div class="max-h-80 overflow-y-auto">
        <!-- Empty state -->
        <div v-if="jobsStore.recentJobs.length === 0" class="p-8 text-center">
          <svg class="w-10 h-10 text-gray-300 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          <p class="text-sm text-gray-500">No recent jobs</p>
        </div>

        <!-- Jobs list -->
        <div v-else class="divide-y divide-gray-100">
          <div
            v-for="job in jobsStore.recentJobs"
            :key="job.id"
            class="p-4"
          >
            <div class="flex items-start justify-between mb-2">
              <div class="flex-1 min-w-0">
                <p class="font-medium text-gray-900 truncate">{{ job.name }}</p>
                <p class="text-xs text-gray-500">Started {{ formatTime(job.startedAt) }}</p>
              </div>
              <span
                class="text-xs font-medium px-2 py-0.5 rounded"
                :class="getStatusColor(job.status)"
              >
                {{ getStatusText(job.status) }}
              </span>
            </div>

            <!-- Progress bar for active jobs -->
            <div v-if="['running', 'starting', 'rate_limited'].includes(job.status)" class="mt-2">
              <div class="flex items-center justify-between text-xs text-gray-500 mb-1">
                <span>{{ job.processed }} / {{ job.total }}</span>
                <span v-if="job.updated > 0">{{ job.updated }} updated</span>
              </div>
              <div class="w-full bg-gray-200 rounded-full h-1.5">
                <div
                  class="h-1.5 rounded-full transition-all duration-300"
                  :class="{
                    'bg-strava-orange': job.status === 'running' || job.status === 'starting',
                    'bg-yellow-500': job.status === 'rate_limited'
                  }"
                  :style="{ width: `${job.total ? (job.processed / job.total) * 100 : 0}%` }"
                ></div>
              </div>
            </div>

            <!-- Completed summary -->
            <div v-else-if="job.status === 'completed'" class="mt-2 text-xs text-gray-600">
              Updated {{ job.updated }} activities
            </div>

            <!-- Error info -->
            <div v-if="job.errors?.length > 0" class="mt-2 text-xs text-red-600">
              {{ job.errors.length }} error(s)
            </div>

            <!-- Dismiss button for completed/failed -->
            <button
              v-if="['completed', 'failed', 'error'].includes(job.status)"
              @click="jobsStore.removeJob(job.id)"
              class="mt-2 text-xs text-gray-400 hover:text-gray-600"
            >
              Dismiss
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Backdrop to close panel -->
    <div
      v-if="showPanel"
      class="fixed inset-0 z-40"
      @click="showPanel = false"
    ></div>
  </div>
</template>
