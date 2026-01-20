export const mockEquipment = [
  {
    id: 'b1234567',
    strava_gear_id: 'b1234567',
    name: 'Canyon Aeroad CF SLX',
    equipment_type: 'bike',
    brand_name: 'Canyon',
    model_name: 'Aeroad CF SLX',
    distance: 4523000, // meters
    is_primary: true,
    is_retired: false,
    description: 'Road bike for outdoor rides'
  },
  {
    id: 'b2345678',
    strava_gear_id: 'b2345678',
    name: 'Zwift Hub + Allez',
    equipment_type: 'bike',
    brand_name: 'Specialized',
    model_name: 'Allez',
    distance: 2156000,
    is_primary: false,
    is_retired: false,
    description: 'Indoor trainer setup'
  },
  {
    id: 'b3456789',
    strava_gear_id: 'b3456789',
    name: 'Trek Checkpoint SL5',
    equipment_type: 'bike',
    brand_name: 'Trek',
    model_name: 'Checkpoint SL5',
    distance: 1834000,
    is_primary: false,
    is_retired: false,
    description: 'Gravel adventures'
  },
  {
    id: 'b4567890',
    strava_gear_id: 'b4567890',
    name: 'Old Roadie',
    equipment_type: 'bike',
    brand_name: 'Giant',
    model_name: 'TCR',
    distance: 12500000,
    is_primary: false,
    is_retired: true,
    description: 'Retired road bike'
  },
  {
    id: 'g1234567',
    strava_gear_id: 'g1234567',
    name: 'Nike Vaporfly 3',
    equipment_type: 'shoes',
    brand_name: 'Nike',
    model_name: 'Vaporfly 3',
    distance: 456000,
    is_primary: true,
    is_retired: false,
    description: 'Race day shoes'
  },
  {
    id: 'g2345678',
    strava_gear_id: 'g2345678',
    name: 'Brooks Ghost 15',
    equipment_type: 'shoes',
    brand_name: 'Brooks',
    model_name: 'Ghost 15',
    distance: 823000,
    is_primary: false,
    is_retired: false,
    description: 'Daily trainers'
  }
]

export function getEquipmentById(id) {
  return mockEquipment.find(e => e.id === id)
}

export function getBikes() {
  return mockEquipment.filter(e => e.equipment_type === 'bike' && !e.is_retired)
}

export function getShoes() {
  return mockEquipment.filter(e => e.equipment_type === 'shoes' && !e.is_retired)
}

export function formatDistance(meters) {
  const km = meters / 1000
  if (km >= 1000) {
    return `${(km / 1000).toFixed(1)}k km`
  }
  return `${km.toFixed(0)} km`
}
