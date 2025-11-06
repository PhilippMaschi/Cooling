import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { TrendingDown, Zap, DollarSign, Cloud, Activity } from 'lucide-react';
import { mockAggregatedStats } from '../mock';

const StatsOverview = ({ selectedScenarios, viewMode }) => {
  const stats = mockAggregatedStats.filter(s => selectedScenarios.includes(s.scenarioId));

  const calculateAverage = (key) => {
    const sum = stats.reduce((acc, s) => acc + s[key], 0);
    return (sum / stats.length).toFixed(2);
  };

  const calculateTotal = (key) => {
    return stats.reduce((acc, s) => acc + s[key], 0).toFixed(0);
  };

  const statCards = [
    {
      title: 'Avg Cooling Load',
      value: calculateAverage('avgCoolingLoad'),
      unit: 'kW',
      icon: Activity,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50'
    },
    {
      title: 'Total Energy',
      value: calculateTotal('totalCoolingLoad'),
      unit: 'kWh',
      icon: Zap,
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-50'
    },
    {
      title: 'Total Cost',
      value: calculateTotal('totalEnergyCost'),
      unit: '$',
      icon: DollarSign,
      color: 'text-green-600',
      bgColor: 'bg-green-50'
    },
    {
      title: 'Total CO2',
      value: calculateTotal('co2Emissions'),
      unit: 'kg',
      icon: Cloud,
      color: 'text-slate-600',
      bgColor: 'bg-slate-50'
    }
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
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