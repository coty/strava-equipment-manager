import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '../api/client'

// Check if we're in development mode with mock data
const USE_MOCK_DATA = import.meta.env.VITE_USE_MOCK_DATA === 'true'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const isLoading = ref(false)
  const error = ref(null)

  // Mock user for development
  const mockUser = {
    id: 12345,
    strava_athlete_id: 12345,
    firstname: 'John',
    lastname: 'Cyclist',
    profile: 'https://dgalywyr863hv.cloudfront.net/pictures/athletes/12345/12345/1/large.jpg',
    city: 'San Francisco',
    state: 'CA',
    country: 'United States'
  }

  // Start with mock user if in mock mode
  if (USE_MOCK_DATA) {
    user.value = mockUser
  }

  const isAuthenticated = computed(() => !!user.value)

  function login() {
    if (USE_MOCK_DATA) {
      user.value = mockUser
      return
    }
    // Redirect to Strava OAuth
    window.location.href = authApi.getLoginUrl()
  }

  async function logout() {
    if (USE_MOCK_DATA) {
      user.value = null
      return
    }

    try {
      await authApi.logout()
      user.value = null
    } catch (e) {
      console.error('Logout failed:', e)
      // Clear user anyway
      user.value = null
    }
  }

  async function checkAuthStatus() {
    if (USE_MOCK_DATA) {
      return
    }

    isLoading.value = true
    error.value = null

    try {
      const status = await authApi.getStatus()
      if (status.is_authenticated && status.user) {
        user.value = status.user
      } else {
        user.value = null
      }
    } catch (e) {
      console.error('Auth check failed:', e)
      error.value = e.message
      user.value = null
    } finally {
      isLoading.value = false
    }
  }

  return {
    user,
    isLoading,
    error,
    isAuthenticated,
    login,
    logout,
    checkAuthStatus
  }
})
