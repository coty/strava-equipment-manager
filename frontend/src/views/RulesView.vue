<script setup>
import { ref, computed, reactive, onMounted } from 'vue'
import { useRulesStore } from '../stores/rules'
import { useEquipmentStore } from '../stores/equipment'
import { useActivitiesStore } from '../stores/activities'

const rulesStore = useRulesStore()
const equipmentStore = useEquipmentStore()
const activitiesStore = useActivitiesStore()

const showEditor = ref(false)
const showPreview = ref(false)
const editingRule = ref(null)
const previewRule = ref(null)
const selectedPreviewActivities = ref(new Set())

const emptyRule = {
  id: null,
  name: '',
  priority: 1,
  target_gear_id: '',
  is_active: true,
  conditions: []
}

const currentRule = reactive({ ...emptyRule })

// Fetch data on mount
onMounted(async () => {
  await Promise.all([
    rulesStore.fetchRules(),
    equipmentStore.fetchEquipment()
  ])
})

const matchingActivities = computed(() => rulesStore.previewResults)

function openEditor(rule = null) {
  if (rule) {
    editingRule.value = rule.id
    Object.assign(currentRule, JSON.parse(JSON.stringify(rule)))
  } else {
    editingRule.value = null
    Object.assign(currentRule, { ...emptyRule, id: Date.now(), conditions: [] })
  }
  showEditor.value = true
}

function closeEditor() {
  showEditor.value = false
  editingRule.value = null
  Object.assign(currentRule, { ...emptyRule })
}

function addCondition() {
  currentRule.conditions.push({
    id: Date.now(),
    field: 'name',
    operator: 'contains',
    value: '',
    logic: 'AND'
  })
}

function removeCondition(index) {
  currentRule.conditions.splice(index, 1)
}

async function saveRule() {
  try {
    if (editingRule.value) {
      await rulesStore.updateRule(editingRule.value, currentRule)
    } else {
      await rulesStore.createRule(currentRule)
    }
    closeEditor()
  } catch (e) {
    console.error('Failed to save rule:', e)
  }
}

async function deleteRule(id) {
  try {
    await rulesStore.deleteRule(id)
  } catch (e) {
    console.error('Failed to delete rule:', e)
  }
}

function toggleRule(id) {
  rulesStore.toggleRuleActive(id)
}

async function openPreview(rule) {
  previewRule.value = rule
  showPreview.value = true
  try {
    await rulesStore.previewRule(rule.id)
    selectedPreviewActivities.value = new Set(matchingActivities.value.map(a => a.id))
  } catch (e) {
    console.error('Failed to preview rule:', e)
  }
}

function closePreview() {
  showPreview.value = false
  previewRule.value = null
  selectedPreviewActivities.value.clear()
}

async function applyRule() {
  try {
    await rulesStore.applyRule(previewRule.value.id, Array.from(selectedPreviewActivities.value))
    // Close modal - job runs in background and can be tracked via Jobs indicator
    closePreview()
  } catch (e) {
    console.error('Failed to apply rule:', e)
  }
}

function togglePreviewActivity(id) {
  if (selectedPreviewActivities.value.has(id)) {
    selectedPreviewActivities.value.delete(id)
  } else {
    selectedPreviewActivities.value.add(id)
  }
}
</script>

<template>
  <div class="p-8">
    <!-- Header -->
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Rules</h1>
        <p class="text-gray-600">Automatically assign equipment to activities</p>
      </div>
      <button @click="openEditor()" class="btn btn-primary">
        <svg class="w-4 h-4 mr-2 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
        </svg>
        New Rule
      </button>
    </div>

    <!-- Error Alert -->
    <div v-if="rulesStore.error" class="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700">
      {{ rulesStore.error }}
    </div>

    <!-- Loading State -->
    <div v-if="rulesStore.isLoading" class="card p-12 text-center">
      <svg class="w-8 h-8 text-strava-orange mx-auto mb-4 animate-spin" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      <p class="text-gray-500">Loading rules...</p>
    </div>

    <!-- Rules List -->
    <div v-else class="space-y-4">
      <div
        v-for="(rule, index) in rulesStore.rules"
        :key="rule.id"
        class="card"
        :class="{ 'opacity-60': !rule.is_active }"
      >
        <div class="flex items-start gap-4">
          <!-- Priority Handle -->
          <div class="flex flex-col items-center gap-1 text-gray-400">
            <svg class="w-5 h-5 cursor-move" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8h16M4 16h16" />
            </svg>
            <span class="text-xs font-medium">{{ index + 1 }}</span>
          </div>

          <!-- Rule Content -->
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-3 mb-2">
              <h3 class="font-semibold text-gray-900">{{ rule.name }}</h3>
              <span v-if="rule.is_active" class="px-2 py-0.5 text-xs font-medium bg-green-100 text-green-700 rounded">
                Active
              </span>
              <span v-else class="px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-600 rounded">
                Inactive
              </span>
            </div>

            <!-- Conditions Summary -->
            <div class="flex flex-wrap gap-2 mb-3">
              <div
                v-for="condition in rule.conditions"
                :key="condition.id"
                class="flex items-center gap-1 px-2 py-1 bg-gray-100 rounded text-sm"
              >
                <span class="font-medium text-gray-700">{{ condition.field }}</span>
                <span class="text-gray-500">{{ condition.operator }}</span>
                <span class="text-gray-900">"{{ condition.value }}"</span>
              </div>
            </div>

            <!-- Target Equipment -->
            <div class="flex items-center gap-2 text-sm text-gray-600">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
              <span>Assign to:</span>
              <span class="font-medium text-gray-900">{{ equipmentStore.getEquipmentName(rule.target_gear_id) }}</span>
            </div>
          </div>

          <!-- Matching Count -->
          <div class="text-center px-4">
            <p class="text-2xl font-bold text-strava-orange">{{ rule.matching_count || 0 }}</p>
            <p class="text-xs text-gray-500">matches</p>
          </div>

          <!-- Actions -->
          <div class="flex items-center gap-2">
            <button
              @click="openPreview(rule)"
              class="p-2 text-gray-400 hover:text-strava-orange hover:bg-strava-orange/10 rounded-lg transition-colors"
              title="Preview matches"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
            </button>
            <button
              @click="openEditor(rule)"
              class="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
              title="Edit rule"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
            </button>
            <button
              @click="toggleRule(rule.id)"
              class="p-2 text-gray-400 hover:text-yellow-600 hover:bg-yellow-50 rounded-lg transition-colors"
              :title="rule.is_active ? 'Disable rule' : 'Enable rule'"
            >
              <svg v-if="rule.is_active" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </button>
            <button
              @click="deleteRule(rule.id)"
              class="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
              title="Delete rule"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-if="!rulesStore.isLoading && rulesStore.rules.length === 0" class="card text-center py-12">
      <svg class="w-12 h-12 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
      </svg>
      <p class="text-gray-500 mb-4">No rules created yet</p>
      <button @click="openEditor()" class="btn btn-primary">
        Create your first rule
      </button>
    </div>

    <!-- Rule Editor Modal -->
    <div v-if="showEditor" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div class="p-6 border-b border-gray-200">
          <h3 class="text-lg font-semibold text-gray-900">
            {{ editingRule ? 'Edit Rule' : 'Create New Rule' }}
          </h3>
        </div>

        <div class="p-6 space-y-6">
          <!-- Rule Name -->
          <div>
            <label class="label">Rule Name</label>
            <input
              v-model="currentRule.name"
              type="text"
              placeholder="e.g., Zwift Rides"
              class="input"
            />
          </div>

          <!-- Target Equipment -->
          <div>
            <label class="label">Assign to Equipment</label>
            <select v-model="currentRule.target_gear_id" class="input">
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

          <!-- Conditions -->
          <div>
            <div class="flex items-center justify-between mb-3">
              <label class="label mb-0">Conditions</label>
              <button @click="addCondition" class="text-sm text-strava-orange hover:underline">
                + Add condition
              </button>
            </div>

            <div v-if="currentRule.conditions.length === 0" class="text-center py-8 bg-gray-50 rounded-lg border-2 border-dashed border-gray-200">
              <p class="text-gray-500 mb-2">No conditions defined</p>
              <button @click="addCondition" class="text-strava-orange hover:underline">
                Add your first condition
              </button>
            </div>

            <div v-else class="space-y-3">
              <div
                v-for="(condition, index) in currentRule.conditions"
                :key="condition.id"
                class="flex items-center gap-3 p-4 bg-gray-50 rounded-lg"
              >
                <!-- Logic operator (for 2nd+ conditions) -->
                <div v-if="index > 0" class="w-16">
                  <select v-model="condition.logic" class="input text-sm py-1">
                    <option value="AND">AND</option>
                    <option value="OR">OR</option>
                  </select>
                </div>
                <div v-else class="w-16">
                  <span class="text-sm text-gray-500">Where</span>
                </div>

                <!-- Field -->
                <div class="flex-1">
                  <select v-model="condition.field" class="input">
                    <option v-for="field in rulesStore.ruleFields" :key="field.value" :value="field.value">
                      {{ field.label }}
                    </option>
                  </select>
                </div>

                <!-- Operator -->
                <div class="w-40">
                  <select v-model="condition.operator" class="input">
                    <option
                      v-for="op in rulesStore.getOperatorsForField(condition.field)"
                      :key="op.value"
                      :value="op.value"
                    >
                      {{ op.label }}
                    </option>
                  </select>
                </div>

                <!-- Value -->
                <div class="flex-1">
                  <select
                    v-if="rulesStore.getFieldType(condition.field) === 'select'"
                    v-model="condition.value"
                    class="input"
                  >
                    <option v-for="opt in rulesStore.getFieldOptions(condition.field)" :key="opt" :value="opt">
                      {{ opt }}
                    </option>
                  </select>
                  <select
                    v-else-if="rulesStore.getFieldType(condition.field) === 'boolean'"
                    v-model="condition.value"
                    class="input"
                  >
                    <option value="true">Yes</option>
                    <option value="false">No</option>
                  </select>
                  <input
                    v-else
                    v-model="condition.value"
                    :type="rulesStore.getFieldType(condition.field) === 'number' ? 'number' : 'text'"
                    placeholder="Value..."
                    class="input"
                  />
                </div>

                <!-- Remove -->
                <button
                  @click="removeCondition(index)"
                  class="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
          </div>

          <!-- Active Toggle -->
          <div class="flex items-center gap-3">
            <input
              v-model="currentRule.is_active"
              type="checkbox"
              id="is_active"
              class="rounded border-gray-300 text-strava-orange focus:ring-strava-orange"
            />
            <label for="is_active" class="text-sm text-gray-700">Rule is active</label>
          </div>
        </div>

        <div class="p-6 border-t border-gray-200 flex gap-3">
          <button @click="closeEditor" class="btn btn-secondary flex-1">
            Cancel
          </button>
          <button
            @click="saveRule"
            :disabled="!currentRule.name || !currentRule.target_gear_id"
            class="btn btn-primary flex-1 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {{ editingRule ? 'Save Changes' : 'Create Rule' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Preview Modal -->
    <div v-if="showPreview" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-xl shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        <div class="p-6 border-b border-gray-200">
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-lg font-semibold text-gray-900">Preview: {{ previewRule?.name }}</h3>
              <p class="text-sm text-gray-500">
                {{ matchingActivities.length }} activities match this rule
              </p>
            </div>
            <div class="text-right">
              <p class="text-sm text-gray-500">Will be assigned to:</p>
              <p class="font-medium text-gray-900">{{ equipmentStore.getEquipmentName(previewRule?.target_gear_id) }}</p>
            </div>
          </div>
        </div>

        <!-- Preview Loading -->
        <div v-if="rulesStore.isPreviewLoading" class="flex-1 flex items-center justify-center p-12">
          <svg class="w-8 h-8 text-strava-orange animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        </div>

        <div v-else class="flex-1 overflow-y-auto p-6">
          <table class="w-full">
            <thead>
              <tr class="border-b border-gray-200">
                <th class="text-left p-3 w-10">
                  <input
                    type="checkbox"
                    :checked="selectedPreviewActivities.size === matchingActivities.length"
                    @change="selectedPreviewActivities.size === matchingActivities.length ? selectedPreviewActivities.clear() : (selectedPreviewActivities = new Set(matchingActivities.map(a => a.id)))"
                    class="rounded border-gray-300 text-strava-orange focus:ring-strava-orange"
                  />
                </th>
                <th class="text-left p-3 text-sm font-medium text-gray-600">Activity</th>
                <th class="text-left p-3 text-sm font-medium text-gray-600">Date</th>
                <th class="text-left p-3 text-sm font-medium text-gray-600">Current Equipment</th>
                <th class="text-left p-3 text-sm font-medium text-gray-600">New Equipment</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="activity in matchingActivities"
                :key="activity.id"
                class="border-b border-gray-100 hover:bg-gray-50"
              >
                <td class="p-3">
                  <input
                    type="checkbox"
                    :checked="selectedPreviewActivities.has(activity.id)"
                    @change="togglePreviewActivity(activity.id)"
                    class="rounded border-gray-300 text-strava-orange focus:ring-strava-orange"
                  />
                </td>
                <td class="p-3">
                  <p class="font-medium text-gray-900">{{ activity.name }}</p>
                  <p class="text-xs text-gray-500">{{ activitiesStore.formatDistance(activity.distance) }} - {{ activitiesStore.formatDuration(activity.moving_time) }}</p>
                </td>
                <td class="p-3 text-sm text-gray-600">{{ activitiesStore.formatDate(activity.start_date) }}</td>
                <td class="p-3">
                  <span class="text-sm text-gray-600">{{ activity.current_gear_name || 'None' }}</span>
                </td>
                <td class="p-3">
                  <span class="text-sm font-medium text-strava-orange">
                    {{ activity.new_gear_name }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>

          <div v-if="matchingActivities.length === 0" class="text-center py-12">
            <svg class="w-12 h-12 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p class="text-gray-500">No activities match this rule</p>
          </div>
        </div>

        <div class="p-6 border-t border-gray-200 flex gap-3">
          <button @click="closePreview" class="btn btn-secondary flex-1">
            Cancel
          </button>
          <button
            @click="applyRule"
            :disabled="selectedPreviewActivities.size === 0"
            class="btn btn-primary flex-1 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Apply to {{ selectedPreviewActivities.size }} Activities
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
