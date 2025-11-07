// Mock data for model visualization

// Generate hourly data (8760 points) for a year
const generateHourlyData = (baseValue, variance, trend = 0) => {
  const data = [];
  for (let i = 0; i < 8760; i++) {
    // Add seasonal variation (higher cooling in summer)
    const seasonalFactor = Math.sin((i / 8760) * 2 * Math.PI) * 0.5 + 0.5;
    const trendFactor = 1 + (trend * i / 8760);
    const randomVariance = (Math.random() - 0.5) * variance;
    const value = (baseValue + randomVariance) * seasonalFactor * trendFactor;
    data.push(Math.max(0, value));
  }
  return data;
};

// Mock projects
export const mockProjects = [
  { id: 'cooling_analysis_2024', name: 'Cooling Analysis 2024' },
  { id: 'energy_efficiency', name: 'Energy Efficiency Study' },
  { id: 'thermal_comfort', name: 'Thermal Comfort Analysis' }
];

// Mock scenarios for a project
export const mockScenarios = [
  { id: 1, name: 'Scenario 1 - Baseline', description: 'Standard cooling system' },
  { id: 2, name: 'Scenario 2 - Optimized', description: 'Improved insulation' },
  { id: 3, name: 'Scenario 3 - Advanced', description: 'Heat pump with storage' },
  { id: 4, name: 'Scenario 4 - Hybrid', description: 'Hybrid cooling system' },
  { id: 5, name: 'Scenario 5 - Green', description: 'Renewable energy focus' }
];

// Generate mock hourly data for different profiles
export const generateMockScenarioData = (scenarioId) => {
  const multiplier = 1 + (scenarioId - 1) * 0.15;
  return {
    scenarioId,
    coolingLoad: generateHourlyData(2.5 * multiplier, 1.2, -0.1),
    heatingLoad: generateHourlyData(1.8 * multiplier, 0.8, 0.05),
    electricityConsumption: generateHourlyData(3.2 * multiplier, 1.5, 0),
    temperature: generateHourlyData(22, 4, 0)
  };
};

// Mock aggregated statistics from SQLite
export const mockAggregatedStats = [
  {
    scenarioId: 1,
    name: 'Scenario 1 - Baseline',
    totalCoolingLoad: 15420,
    avgCoolingLoad: 1.76,
    peakCoolingLoad: 8.2,
    totalEnergyCost: 4250,
    co2Emissions: 1850
  },
  {
    scenarioId: 2,
    name: 'Scenario 2 - Optimized',
    totalCoolingLoad: 13180,
    avgCoolingLoad: 1.50,
    peakCoolingLoad: 7.1,
    totalEnergyCost: 3620,
    co2Emissions: 1580
  },
  {
    scenarioId: 3,
    name: 'Scenario 3 - Advanced',
    totalCoolingLoad: 11250,
    avgCoolingLoad: 1.28,
    peakCoolingLoad: 6.5,
    totalEnergyCost: 3180,
    co2Emissions: 1320
  },
  {
    scenarioId: 4,
    name: 'Scenario 4 - Hybrid',
    totalCoolingLoad: 12800,
    avgCoolingLoad: 1.46,
    peakCoolingLoad: 6.9,
    totalEnergyCost: 3450,
    co2Emissions: 1420
  },
  {
    scenarioId: 5,
    name: 'Scenario 5 - Green',
    totalCoolingLoad: 10980,
    avgCoolingLoad: 1.25,
    peakCoolingLoad: 6.2,
    totalEnergyCost: 2890,
    co2Emissions: 980
  }
];

// Mock API delay simulation
export const mockDelay = (ms = 500) => new Promise(resolve => setTimeout(resolve, ms));