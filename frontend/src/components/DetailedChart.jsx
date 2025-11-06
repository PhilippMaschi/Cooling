import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import Plot from 'react-plotly.js';
import { generateMockScenarioData, mockDelay } from '../mock';
import { Loader2 } from 'lucide-react';

const DetailedChart = ({ selectedScenarios }) => {
  const [loading, setLoading] = useState(false);
  const [scenarioData, setScenarioData] = useState({});
  const [aggregation, setAggregation] = useState('hourly');
  const [activeProfile, setActiveProfile] = useState('coolingLoad');

  useEffect(() => {
    loadScenarioData();
  }, [selectedScenarios]);

  const loadScenarioData = async () => {
    setLoading(true);
    await mockDelay(800);
    
    const data = {};
    selectedScenarios.forEach(id => {
      data[id] = generateMockScenarioData(id);
    });
    
    setScenarioData(data);
    setLoading(false);
  };

  const aggregateData = (data, type) => {
    if (type === 'hourly') return data;
    
    const aggregated = [];
    const groupSize = type === 'daily' ? 24 : 24 * 30; // 30 days per month
    
    for (let i = 0; i < data.length; i += groupSize) {
      const chunk = data.slice(i, i + groupSize);
      const avg = chunk.reduce((sum, val) => sum + val, 0) / chunk.length;
      aggregated.push(avg);
    }
    
    return aggregated;
  };

  const getXAxis = (dataLength, type) => {
    if (type === 'hourly') {
      return Array.from({ length: dataLength }, (_, i) => i);
    } else if (type === 'daily') {
      return Array.from({ length: dataLength }, (_, i) => i + 1);
    } else {
      return Array.from({ length: dataLength }, (_, i) => i + 1);
    }
  };

  const getXAxisLabel = (type) => {
    if (type === 'hourly') return 'Hours of Year';
    if (type === 'daily') return 'Days of Year';
    return 'Months of Year';
  };

  const profiles = [
    { value: 'coolingLoad', label: 'Cooling Load', unit: 'kW' },
    { value: 'heatingLoad', label: 'Heating Load', unit: 'kW' },
    { value: 'electricityConsumption', label: 'Electricity Consumption', unit: 'kW' },
    { value: 'temperature', label: 'Temperature', unit: '°C' }
  ];

  const createPlotData = () => {
    const traces = [];
    const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

    selectedScenarios.forEach((scenarioId, index) => {
      if (scenarioData[scenarioId]) {
        const rawData = scenarioData[scenarioId][activeProfile];
        const aggregatedData = aggregateData(rawData, aggregation);
        const xAxis = getXAxis(aggregatedData.length, aggregation);

        traces.push({
          x: xAxis,
          y: aggregatedData,
          type: 'scatter',
          mode: 'lines',
          name: `Scenario ${scenarioId}`,
          line: {
            color: colors[index % colors.length],
            width: 2
          },
          hovertemplate: `<b>Scenario ${scenarioId}</b><br>` +
            `${getXAxisLabel(aggregation)}: %{x}<br>` +
            `Value: %{y:.2f}<extra></extra>`
        });
      }
    });

    return traces;
  };

  const currentProfile = profiles.find(p => p.value === activeProfile);

  if (loading) {
    return (
      <Card className="border-slate-200 shadow-sm">
        <CardContent className="py-12">
          <div className="flex flex-col items-center justify-center text-slate-500">
            <Loader2 className="w-8 h-8 animate-spin mb-4" />
            <p>Loading scenario data...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-slate-200 shadow-sm">
      <CardHeader>
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <CardTitle className="text-lg">Detailed Time-Series Analysis</CardTitle>
            <CardDescription>Interactive hourly profile comparison</CardDescription>
          </div>
          <div className="flex flex-col sm:flex-row gap-3">
            <Select value={activeProfile} onValueChange={setActiveProfile}>
              <SelectTrigger className="w-full sm:w-[200px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {profiles.map(profile => (
                  <SelectItem key={profile.value} value={profile.value}>
                    {profile.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            
            <Select value={aggregation} onValueChange={setAggregation}>
              <SelectTrigger className="w-full sm:w-[150px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="hourly">Hourly</SelectItem>
                <SelectItem value="daily">Daily</SelectItem>
                <SelectItem value="monthly">Monthly</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="w-full">
          <Plot
            data={createPlotData()}
            layout={{
              autosize: true,
              height: 500,
              margin: { l: 60, r: 40, t: 40, b: 60 },
              xaxis: {
                title: getXAxisLabel(aggregation),
                showgrid: true,
                gridcolor: '#e2e8f0'
              },
              yaxis: {
                title: `${currentProfile.label} (${currentProfile.unit})`,
                showgrid: true,
                gridcolor: '#e2e8f0'
              },
              hovermode: 'closest',
              plot_bgcolor: '#fafafa',
              paper_bgcolor: 'white',
              font: {
                family: 'Inter, system-ui, sans-serif',
                size: 12
              },
              legend: {
                x: 1,
                xanchor: 'right',
                y: 1,
                bgcolor: 'rgba(255, 255, 255, 0.8)',
                bordercolor: '#cbd5e1',
                borderwidth: 1
              }
            }}
            config={{
              responsive: true,
              displayModeBar: true,
              displaylogo: false,
              modeBarButtonsToRemove: ['lasso2d', 'select2d']
            }}
            style={{ width: '100%', height: '100%' }}
          />
        </div>
      </CardContent>
    </Card>
  );
};

export default DetailedChart;