import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Dashboard from '../Dashboard';
import {
  getProjects,
  getProjectScenarios,
  getScenarioTimeseries,
} from '../../lib/api';

jest.mock('../../lib/api', () => ({
  getProjects: jest.fn(),
  getProjectScenarios: jest.fn(),
  getScenarioTimeseries: jest.fn(),
}));

const mockProjects = [
  {
    id: 'AUT_2020_cooling',
    name: 'AUT 2020 Cooling',
    country: 'AUT',
    year: 2020,
    focus: 'cooling',
    scenario_count: 3,
    scenario_ids: [1, 2, 3],
  },
];

const mockScenarioResponse = {
  project_id: 'AUT_2020_cooling',
  scenarios: [
    {
      scenario_id: 1,
      total_cooling_load: 12500,
      avg_cooling_load: 1.42,
      total_electricity_demand: 22000,
      total_energy_cost: 4800,
      peak_cooling_load: 6.2,
      peak_electric_load: 8.4,
    },
  ],
};

const mockTimeseries = {
  scenario_id: 1,
  metric: 'coolingLoad',
  aggregation: 'hourly',
  unit: 'kW',
  timestamps: ['2020-01-01T00:00:00Z', '2020-01-01T01:00:00Z'],
  values: [1.2, 1.3],
};

describe('Dashboard integration', () => {
  beforeEach(() => {
    getProjects.mockResolvedValue(mockProjects);
    getProjectScenarios.mockResolvedValue(mockScenarioResponse);
    getScenarioTimeseries.mockResolvedValue(mockTimeseries);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('loads projects and displays scenario stats from the backend', async () => {
    render(<Dashboard />);

    await waitFor(() => expect(getProjects).toHaveBeenCalled());
    await waitFor(() =>
      expect(getProjectScenarios).toHaveBeenCalledWith('AUT_2020_cooling')
    );

    expect(await screen.findByText(/Scenario Selection/i)).toBeInTheDocument();
    expect(screen.getByText(/Scenario 1/i)).toBeInTheDocument();
    expect(screen.getByText(/Total Cooling Energy/i)).toBeInTheDocument();
    expect(screen.getByText('12,500')).toBeInTheDocument();
    expect(screen.getByText('4,800')).toBeInTheDocument();
  });

  it('allows switching view modes and keeps selections in sync', async () => {
    render(<Dashboard />);

    await screen.findByText(/Scenario Selection/i);
    const aggregatedTab = screen.getByRole('tab', { name: /Aggregated View/i });
    await userEvent.click(aggregatedTab);

    expect(getProjectScenarios).toHaveBeenCalledTimes(1);
    expect(screen.getByText(/Peak Electric/i)).toBeInTheDocument();
  });
});
