import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { rulesApi } from '../api/client'

const POLL_INTERVAL = 2000
const STORAGE_KEY = 'equipment_manager_jobs'

export const useJobsStore = defineStore('jobs', () => {
  const jobs = ref([])
  const pollIntervals = {}

  // Load persisted jobs on init
  function loadPersistedJobs() {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        const parsed = JSON.parse(stored)
        // Filter out old completed jobs (older than 1 hour)
        const oneHourAgo = Date.now() - 60 * 60 * 1000
        jobs.value = parsed.filter(job => {
          if (['completed', 'failed', 'error'].includes(job.status)) {
            return new Date(job.completedAt || job.startedAt).getTime() > oneHourAgo
          }
          return true
        })
        // Resume polling for any running jobs
        jobs.value.forEach(job => {
          if (['running', 'rate_limited', 'starting'].includes(job.status)) {
            startPolling(job.id)
          }
        })
      }
    } catch (e) {
      console.error('Failed to load persisted jobs:', e)
    }
  }

  // Persist jobs to localStorage
  function persistJobs() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(jobs.value))
    } catch (e) {
      console.error('Failed to persist jobs:', e)
    }
  }

  // Computed
  const activeJobs = computed(() =>
    jobs.value.filter(job => ['running', 'rate_limited', 'starting'].includes(job.status))
  )

  const hasActiveJobs = computed(() => activeJobs.value.length > 0)

  const recentJobs = computed(() => {
    // Return jobs from the last hour, sorted by most recent
    const oneHourAgo = Date.now() - 60 * 60 * 1000
    return jobs.value
      .filter(job => new Date(job.startedAt).getTime() > oneHourAgo)
      .sort((a, b) => new Date(b.startedAt) - new Date(a.startedAt))
  })

  // Add a new job
  function addJob(jobData) {
    const job = {
      id: jobData.jobId,
      type: jobData.type,
      name: jobData.name,
      description: jobData.description,
      resourceId: jobData.resourceId,
      status: 'starting',
      total: jobData.total || 0,
      processed: 0,
      updated: 0,
      errors: [],
      startedAt: new Date().toISOString(),
      completedAt: null,
    }
    jobs.value.push(job)
    persistJobs()
    startPolling(job.id)
    return job
  }

  // Update job status
  function updateJob(jobId, updates) {
    const job = jobs.value.find(j => j.id === jobId)
    if (job) {
      Object.assign(job, updates)
      if (['completed', 'failed', 'error'].includes(updates.status)) {
        job.completedAt = new Date().toISOString()
        stopPolling(jobId)
      }
      persistJobs()
    }
  }

  // Remove a job from the list
  function removeJob(jobId) {
    stopPolling(jobId)
    jobs.value = jobs.value.filter(j => j.id !== jobId)
    persistJobs()
  }

  // Clear completed jobs
  function clearCompletedJobs() {
    jobs.value = jobs.value.filter(job =>
      !['completed', 'failed', 'error'].includes(job.status)
    )
    persistJobs()
  }

  // Start polling for a job
  function startPolling(jobId) {
    if (pollIntervals[jobId]) return

    const job = jobs.value.find(j => j.id === jobId)
    if (!job) return

    pollIntervals[jobId] = setInterval(async () => {
      try {
        let status
        if (job.type === 'rule_apply') {
          status = await rulesApi.getApplyStatus(job.resourceId)
        }
        // Add other job types here as needed

        if (status) {
          updateJob(jobId, {
            status: status.status,
            total: status.total || job.total,
            processed: status.processed || 0,
            updated: status.updated || 0,
            errors: status.errors || [],
          })
        }
      } catch (e) {
        console.error('Failed to poll job status:', e)
      }
    }, POLL_INTERVAL)
  }

  // Stop polling for a job
  function stopPolling(jobId) {
    if (pollIntervals[jobId]) {
      clearInterval(pollIntervals[jobId])
      delete pollIntervals[jobId]
    }
  }

  // Get job by ID
  function getJob(jobId) {
    return jobs.value.find(j => j.id === jobId)
  }

  // Initialize - load persisted jobs
  loadPersistedJobs()

  return {
    jobs,
    activeJobs,
    hasActiveJobs,
    recentJobs,
    addJob,
    updateJob,
    removeJob,
    clearCompletedJobs,
    getJob,
  }
})
