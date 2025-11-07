import React from 'react';
import { Card, CardContent } from './ui/card';
import { Activity, Zap, DollarSign, TrendingUp, Gauge } from 'lucide-react';

const formatNumber = (value, decimals = 0) => {
  if (value === null || value === undefined || Number.isNaN(value)) return '—';
  return Number(value).toLocaleString(undefined, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
};

const StatsOverview = ({ selectedScenarios, scenarioStats }) => {
  const stats = scenarioStats.filter((scenario) =>
    selectedScenarios.includes(scenario.id ?? scenario.scenario_id)
  );

  if (stats.length === 0) {
    return null;
  }

  const avgCooling =
    stats.reduce((sum, scenario) => sum + (scenario.avg_cooling_load ?? 0), 0) /
    stats.length;
  const totalCooling = stats.reduce(
    (sum, scenario) => sum + (scenario.total_cooling_load ?? 0),
    0
  );
  const totalElectric = stats.reduce(
    (sum, scenario) => sum + (scenario.total_electricity_demand ?? 0),
    0
  );
  const totalCost = stats.reduce(
    (sum, scenario) => sum + (scenario.total_energy_cost ?? 0),
    0
  );
  const peakElectric = Math.max(
    ...stats.map((scenario) => scenario.peak_electric_load ?? 0)
  );
  const peakCooling = Math.max(
    ...stats.map((scenario) => scenario.peak_cooling_load ?? 0)
  );

  const statCards = [
    {
      title: 'Avg Cooling Load',
      value: formatNumber(avgCooling, 2),
      unit: 'kW',
      icon: Activity,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
    },
    {
      title: 'Total Cooling Energy',
      value: formatNumber(totalCooling),
      unit: 'kWh',
      icon: Zap,
      color: 'text-cyan-600',
      bgColor: 'bg-cyan-50',
    },
    {
      title: 'Total Electricity',
      value: formatNumber(totalElectric),
      unit: 'kWh',
      icon: TrendingUp,
      color: 'text-indigo-600',
      bgColor: 'bg-indigo-50',
    },
    {
      title: 'Total Cost',
      value: formatNumber(totalCost, 0),
      unit: '€',
      icon: DollarSign,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
    },
    {
      title: 'Peak Cooling',
      value: formatNumber(peakCooling, 2),
      unit: 'kW',
      icon: Gauge,
      color: 'text-orange-600',
      bgColor: 'bg-orange-50',
    },
    {
      title: 'Peak Electric',
      value: formatNumber(peakElectric, 2),
      unit: 'kW',
      icon: Zap,
      color: 'text-amber-600',
      bgColor: 'bg-amber-50',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
      {statCards.map((stat, index) => {
        const Icon = stat.icon;
        return (
          <Card key={index} className="border-slate-200 shadow-sm">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-slate-600 mb-1">{stat.title}</p>
                  <div className="flex items-baseline gap-1">
                    <span className="text-2xl font-bold text-slate-900">{stat.value}</span>
                    <span className="text-sm text-slate-500">{stat.unit}</span>
                  </div>
                </div>
                <div className={`p-3 rounded-lg ${stat.bgColor}`}>
                  <Icon className={`w-6 h-6 ${stat.color}`} />
                </div>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
};

export default StatsOverview;
