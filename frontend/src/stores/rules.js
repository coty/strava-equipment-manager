import { defineStore } from 'pinia'
import { ref } from 'vue'
import { rulesApi } from '../api/client'
import { mockRules, ruleFields, ruleOperators } from '../data/mockRules'
import { useJobsStore } from './jobs'

const USE_MOCK_DATA = import.meta.env.VITE_USE_MOCK_DATA === 'true'

export const useRulesStore = defineStore('rules', () => {
  const rules = ref([])
  const isLoading = ref(false)
  const error = ref(null)
  const previewResults = ref([])
  const isPreviewLoading = ref(false)

  // Initialize with mock data if in mock mode
  if (USE_MOCK_DATA) {
    rules.value = [...mockRules]
  }

  async function fetchRules() {
    if (USE_MOCK_DATA) {
      rules.value = [...mockRules]
      return
    }

    isLoading.value = true
    error.value = null

    try {
      const data = await rulesApi.getAll()
      rules.value = data
    } catch (e) {
      console.error('Failed to fetch rules:', e)
      error.value = e.response?.data?.detail || e.message
    } finally {
      isLoading.value = false
    }
  }

  async function createRule(rule) {
    if (USE_MOCK_DATA) {
      const newRule = {
        ...rule,
        id: Date.now(),
        matching_count: 0
      }
      rules.value.push(newRule)
      return newRule
    }

    try {
      const newRule = await rulesApi.create(rule)
      // Re-fetch all rules to ensure fresh data including matching counts
      await fetchRules()
      return newRule
    } catch (e) {
      console.error('Failed to create rule:', e)
      error.value = e.response?.data?.detail || e.message
      throw e
    }
  }

  async function updateRule(id, rule) {
    if (USE_MOCK_DATA) {
      const index = rules.value.findIndex(r => r.id === id)
      if (index !== -1) {
        rules.value[index] = { ...rule, id, matching_count: rules.value[index].matching_count || 0 }
      }
      return rules.value[index]
    }

    try {
      const updatedRule = await rulesApi.update(id, rule)
      // Re-fetch all rules to ensure fresh data including matching counts
      await fetchRules()
      return updatedRule
    } catch (e) {
      console.error('Failed to update rule:', e)
      error.value = e.response?.data?.detail || e.message
      throw e
    }
  }

  async function deleteRule(id) {
    if (USE_MOCK_DATA) {
      rules.value = rules.value.filter(r => r.id !== id)
      return
    }

    try {
      await rulesApi.delete(id)
      rules.value = rules.value.filter(r => r.id !== id)
    } catch (e) {
      console.error('Failed to delete rule:', e)
      error.value = e.response?.data?.detail || e.message
      throw e
    }
  }

  function toggleRuleActive(id) {
    const rule = rules.value.find(r => r.id === id)
    if (rule) {
      rule.is_active = !rule.is_active
      if (!USE_MOCK_DATA) {
        // Fire and forget update to backend
        rulesApi.update(id, rule).catch(e => {
          console.error('Failed to toggle rule:', e)
          // Revert on error
          rule.is_active = !rule.is_active
        })
      }
    }
  }

  async function previewRule(id) {
    if (USE_MOCK_DATA) {
      // Import mock activities for preview
      const { mockActivities } = await import('../data/mockActivities')
      const rule = rules.value.find(r => r.id === id)
      if (!rule) return []

      // Evaluate rule against mock activities
      const matching = mockActivities.filter(activity => {
        return rule.conditions.every(condition => {
          const value = activity[condition.field]
          switch (condition.operator) {
            case 'equals':
              if (typeof value === 'boolean') {
                return value === (condition.value === 'true' || condition.value === true)
              }
              return String(value).toLowerCase() === String(condition.value).toLowerCase()
            case 'not_equals':
              return String(value).toLowerCase() !== String(condition.value).toLowerCase()
            case 'contains':
              return String(value).toLowerCase().includes(String(condition.value).toLowerCase())
            case 'not_contains':
              return !String(value).toLowerCase().includes(String(condition.value).toLowerCase())
            case 'starts_with':
              return String(value).toLowerCase().startsWith(String(condition.value).toLowerCase())
            case 'ends_with':
              return String(value).toLowerCase().endsWith(String(condition.value).toLowerCase())
            case 'greater_than':
              return Number(value) > Number(condition.value)
            case 'less_than':
              return Number(value) < Number(condition.value)
            default:
              return true
          }
        })
      })

      previewResults.value = matching
      return matching
    }

    isPreviewLoading.value = true
    error.value = null

    try {
      const response = await rulesApi.preview(id)
      // Extract matching_activities from the response
      previewResults.value = response.matching_activities || []
      return previewResults.value
    } catch (e) {
      console.error('Failed to preview rule:', e)
      error.value = e.response?.data?.detail || e.message
      throw e
    } finally {
      isPreviewLoading.value = false
    }
  }

  async function applyRule(id, activityIds = null) {
    if (USE_MOCK_DATA) {
      await new Promise(resolve => setTimeout(resolve, 1000))

      // Update mock activities with new gear
      const rule = rules.value.find(r => r.id === id)
      const { mockActivities } = await import('../data/mockActivities')

      const idsToUpdate = activityIds || previewResults.value.map(a => a.id)
      idsToUpdate.forEach(actId => {
        const activity = mockActivities.find(a => a.id === actId)
        if (activity && rule) {
          activity.gear_id = rule.target_gear_id
        }
      })

      return { updated: idsToUpdate.length }
    }

    error.value = null

    try {
      const rule = rules.value.find(r => r.id === id)

      // Start the async job
      const result = await rulesApi.apply(id, activityIds)

      // Register with global jobs store
      const jobsStore = useJobsStore()
      jobsStore.addJob({
        jobId: result.job_id,
        type: 'rule_apply',
        name: `Apply Rule: ${rule?.name || 'Unknown'}`,
        description: `Updating equipment on ${activityIds?.length || 'matching'} activities`,
        resourceId: id,
        total: activityIds?.length || 0,
      })

      return result
    } catch (e) {
      console.error('Failed to start rule application:', e)
      error.value = e.response?.data?.detail || e.message
      throw e
    }
  }

  // Helper functions for rule editor
  function getFieldType(fieldValue) {
    const field = ruleFields.find(f => f.value === fieldValue)
    return field?.type || 'text'
  }

  function getOperatorsForField(fieldValue) {
    const type = getFieldType(fieldValue)
    return ruleOperators[type] || ruleOperators.text
  }

  function getFieldOptions(fieldValue) {
    const field = ruleFields.find(f => f.value === fieldValue)
    return field?.options || []
  }

  return {
    rules,
    isLoading,
    error,
    previewResults,
    isPreviewLoading,
    fetchRules,
    createRule,
    updateRule,
    deleteRule,
    toggleRuleActive,
    previewRule,
    applyRule,
    ruleFields,
    ruleOperators,
    getFieldType,
    getOperatorsForField,
    getFieldOptions
  }
})
