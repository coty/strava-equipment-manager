<script setup>
import { onMounted, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const status = ref('processing')
const error = ref(null)

onMounted(async () => {
  const success = route.query.success
  const errorParam = route.query.error

  if (errorParam) {
    status.value = 'error'
    error.value = errorParam === 'access_denied'
      ? 'You denied access to your Strava account.'
      : errorParam === 'no_code'
      ? 'No authorization code received from Strava.'
      : `Authentication failed: ${errorParam}`
    return
  }

  if (success === 'true') {
    // Backend already exchanged the code, check auth status
    try {
      await authStore.checkAuthStatus()

      if (authStore.isAuthenticated) {
        status.value = 'success'
        // Redirect to home after a brief delay
        setTimeout(() => {
          router.push('/')
        }, 1000)
      } else {
        status.value = 'error'
        error.value = 'Authentication completed but session not established. Please try again.'
      }
    } catch (e) {
      status.value = 'error'
      error.value = 'Failed to verify authentication. Please try again.'
    }
    return
  }

  // No success or error param - something went wrong
  status.value = 'error'
  error.value = 'Invalid callback. Please try connecting again.'
})
</script>

<template>
  <div class="min-h-screen flex items-center justify-center p-8">
    <div class="card max-w-md w-full text-center">
      <!-- Processing -->
      <div v-if="status === 'processing'">
        <div class="w-16 h-16 bg-strava-orange/10 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg class="w-8 h-8 text-strava-orange animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        </div>
        <h2 class="text-xl font-semibold text-gray-900 mb-2">Connecting to Strava</h2>
        <p class="text-gray-600">Please wait while we complete the authentication...</p>
      </div>

      <!-- Success -->
      <div v-else-if="status === 'success'">
        <div class="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg class="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h2 class="text-xl font-semibold text-gray-900 mb-2">Connected!</h2>
        <p class="text-gray-600">Redirecting you to the dashboard...</p>
      </div>

      <!-- Error -->
      <div v-else>
        <div class="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg class="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </div>
        <h2 class="text-xl font-semibold text-gray-900 mb-2">Connection Failed</h2>
        <p class="text-gray-600 mb-4">{{ error }}</p>
        <router-link to="/" class="btn btn-primary">
          Back to Home
        </router-link>
      </div>
    </div>
  </div>
</template>
