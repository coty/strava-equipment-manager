<script setup>
import { RouterLink, RouterView } from 'vue-router'
import { useAuthStore } from './stores/auth'
import JobsIndicator from './components/JobsIndicator.vue'

const authStore = useAuthStore()
</script>

<template>
  <div class="min-h-screen flex">
    <!-- Sidebar -->
    <aside class="w-64 bg-white border-r border-gray-200 flex flex-col">
      <!-- Logo -->
      <div class="p-6 border-b border-gray-200">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 bg-strava-orange rounded-lg flex items-center justify-center">
            <svg class="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 24 24">
              <path d="M15.387 17.944l-2.089-4.116h-3.065L15.387 24l5.15-10.172h-3.066m-7.008-5.599l2.836 5.598h4.172L10.463 0l-7 13.828h4.169" />
            </svg>
          </div>
          <div>
            <h1 class="font-bold text-gray-900">Equipment Manager</h1>
            <p class="text-xs text-gray-500">for Strava</p>
          </div>
        </div>
      </div>

      <!-- Navigation -->
      <nav class="flex-1 p-4">
        <ul class="space-y-1">
          <li>
            <RouterLink
              to="/"
              class="flex items-center gap-3 px-3 py-2 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors"
              active-class="bg-strava-orange/10 text-strava-orange font-medium"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
              </svg>
              Dashboard
            </RouterLink>
          </li>
          <li>
            <RouterLink
              to="/activities"
              class="flex items-center gap-3 px-3 py-2 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors"
              active-class="bg-strava-orange/10 text-strava-orange font-medium"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              Activities
            </RouterLink>
          </li>
          <li>
            <RouterLink
              to="/equipment"
              class="flex items-center gap-3 px-3 py-2 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors"
              active-class="bg-strava-orange/10 text-strava-orange font-medium"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
              </svg>
              Equipment
            </RouterLink>
          </li>
          <li>
            <RouterLink
              to="/rules"
              class="flex items-center gap-3 px-3 py-2 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors"
              active-class="bg-strava-orange/10 text-strava-orange font-medium"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
              </svg>
              Rules
            </RouterLink>
          </li>
        </ul>
      </nav>

      <!-- Jobs indicator -->
      <div class="px-4 pb-2">
        <JobsIndicator />
      </div>

      <!-- User section -->
      <div class="p-4 border-t border-gray-200">
        <div v-if="authStore.isAuthenticated" class="flex items-center gap-3">
          <img
            :src="authStore.user?.profile || 'https://via.placeholder.com/40'"
            :alt="authStore.user?.firstname"
            class="w-10 h-10 rounded-full"
          />
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium text-gray-900 truncate">
              {{ authStore.user?.firstname }} {{ authStore.user?.lastname }}
            </p>
            <button
              @click="authStore.logout"
              class="text-xs text-gray-500 hover:text-strava-orange"
            >
              Disconnect
            </button>
          </div>
        </div>
        <div v-else class="text-center">
          <p class="text-sm text-gray-500 mb-2">Not connected</p>
          <button
            @click="authStore.login"
            class="btn btn-primary w-full text-sm"
          >
            Connect with Strava
          </button>
        </div>
      </div>
    </aside>

    <!-- Main content -->
    <main class="flex-1 overflow-auto">
      <RouterView />
    </main>
  </div>
</template>
