export const mockRules = [
  {
    id: 1,
    name: 'Zwift Rides',
    priority: 1,
    target_gear_id: 'b2345678',
    is_active: true,
    conditions: [
      {
        id: 1,
        field: 'name',
        operator: 'contains',
        value: 'Zwift',
        logic: 'AND'
      }
    ],
    matching_count: 7 // Number of activities that match
  },
  {
    id: 2,
    name: 'TrainerRoad Workouts',
    priority: 2,
    target_gear_id: 'b2345678',
    is_active: true,
    conditions: [
      {
        id: 2,
        field: 'device_name',
        operator: 'equals',
        value: 'TrainerRoad',
        logic: 'AND'
      }
    ],
    matching_count: 1
  },
  {
    id: 3,
    name: 'Gravel Rides',
    priority: 3,
    target_gear_id: 'b3456789',
    is_active: true,
    conditions: [
      {
        id: 3,
        field: 'sport_type',
        operator: 'equals',
        value: 'GravelRide',
        logic: 'AND'
      }
    ],
    matching_count: 1
  },
  {
    id: 4,
    name: 'Race Day Runs',
    priority: 4,
    target_gear_id: 'g1234567',
    is_active: false,
    conditions: [
      {
        id: 4,
        field: 'name',
        operator: 'contains',
        value: 'race',
        logic: 'AND'
      },
      {
        id: 5,
        field: 'activity_type',
        operator: 'equals',
        value: 'Run',
        logic: 'AND'
      }
    ],
    matching_count: 0
  }
]

export const ruleFields = [
  { value: 'name', label: 'Activity Name', type: 'text' },
  { value: 'activity_type', label: 'Activity Type', type: 'select', options: ['Ride', 'VirtualRide', 'Run', 'Walk', 'Hike'] },
  { value: 'sport_type', label: 'Sport Type', type: 'select', options: ['Ride', 'VirtualRide', 'GravelRide', 'MountainBikeRide', 'Run', 'TrailRun'] },
  { value: 'trainer', label: 'Indoor/Trainer', type: 'boolean' },
  { value: 'device_name', label: 'Device Name', type: 'text' },
  { value: 'external_id', label: 'External ID', type: 'text' },
  { value: 'distance', label: 'Distance (km)', type: 'number' },
  { value: 'moving_time', label: 'Moving Time (min)', type: 'number' },
  { value: 'current_gear_name', label: 'Current Equipment', type: 'text' }
]

export const ruleOperators = {
  text: [
    { value: 'contains', label: 'contains' },
    { value: 'not_contains', label: 'does not contain' },
    { value: 'equals', label: 'equals' },
    { value: 'starts_with', label: 'starts with' },
    { value: 'ends_with', label: 'ends with' },
    { value: 'regex', label: 'matches regex' }
  ],
  select: [
    { value: 'equals', label: 'equals' },
    { value: 'not_equals', label: 'does not equal' }
  ],
  boolean: [
    { value: 'equals', label: 'is' }
  ],
  number: [
    { value: 'equals', label: 'equals' },
    { value: 'greater_than', label: 'greater than' },
    { value: 'less_than', label: 'less than' },
    { value: 'between', label: 'between' }
  ]
}
