import React, { useEffect, useMemo, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import Plot from 'react-plotly.js';
import { Loader2, AlertCircle } from 'lucide-react';
import { getScenarioTimeseries } from '../lib/api';

const METRIC_MAP = {
  coolingLoad: 'coolingLoad',
  heatingLoad: 'heatingLoad',
  electricityConsumption: 'electricityConsumption',
  temperature: 'temperature',
};

const profiles = [
  { value: 'coolingLoad', label: 'Cooling Load', unit: 'kW' },
  { value: 'heatingLoad', label: 'Heating Load', unit: 'kW' },
  { value: 'electricityConsumption', label: 'Electricity Consumption', unit: 'kW' },
  { value: 'temperature', label: 'Temperature', unit: '°C' },
];

const DetailedChart = ({ projectId, selectedScenarios }) => {
  const [aggregation, setAggregation] = useState('hourly');
  const [activeProfile, setActiveProfile] = useState('coolingLoad');
  const [seriesCache, setSeriesCache] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const missingSeries = selectedScenarios.filter((scenarioId) => {
      const key = cacheKey(projectId, scenarioId, activeProfile, aggregation);
      return !seriesCache[key];
    });

    if (!projectId || missingSeries.length === 0) return;

    const fetchData = async () => {
      setLoading(true);
      setError('');
      try {
        const responses = await Promise.all(
          missingSeries.map(async (scenarioId) => {
            const data = await getScenarioTimeseries(projectId, scenarioId, {
              metric: METRIC_MAP[activeProfile],
              aggregation,
            });
            return { scenarioId, data };
          })
        );
        setSeriesCache((prev) => {
          const next = { ...prev };
          responses.forEach(({ scenarioId, data }) => {
            next[cacheKey(projectId, scenarioId, activeProfile, aggregation)] = data;
          });
          return next;
        });
      } catch (err) {
        setError('Failed to load timeseries data.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [projectId, selectedScenarios, activeProfile, aggregation, seriesCache]);

  useEffect(() => {
    // Clear cache when project changes to avoid stale data
    setSeriesCache({});
  }, [projectId]);

  const plotData = useMemo(() => {
    const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];
    return selectedScenarios
      .map((scenarioId, index) => {
        const entry =
          seriesCache[cacheKey(projectId, scenarioId, activeProfile, aggregation)];
        if (!entry) return null;
        return {
          x: entry.timestamps,
          y: entry.values,
          type: 'scatter',
          mode: 'lines',
          name: `Scenario ${scenarioId}`,
          line: {
            color: colors[index % colors.length],
            width: 2,
          },
          hovertemplate: `<b>Scenario ${scenarioId}</b><br>` +
            `Timestamp: %{x}<br>` +
            `Value: %{y:.2f}<extra></extra>`
        };
      })
      .filter(Boolean);
  }, [selectedScenarios, seriesCache, projectId, activeProfile, aggregation]);

  const currentProfile = profiles.find((profile) => profile.value === activeProfile);

  return (
    <Card className="border-slate-200 shadow-sm">
      <CardHeader>
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <CardTitle className="text-lg">Detailed Time-Series Analysis</CardTitle>
            <CardDescription>Interactive comparison pulled from the backend API</CardDescription>
          </div>
          <div className="flex flex-col sm:flex-row gap-3">
            <Select value={activeProfile} onValueChange={setActiveProfile}>
              <SelectTrigger className="w-full sm:w-[200px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {profiles.map((profile) => (
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
        {error && (
          <div className="mb-4 flex items-center gap-2 text-sm text-red-600">
            <AlertCircle className="w-4 h-4" />
            {error}
          </div>
        )}
        {loading && (
          <div className="flex flex-col items-center justify-center text-slate-500 py-10">
            <Loader2 className="w-6 h-6 animate-spin mb-2" />
            <p>Loading scenario data...</p>
          </div>
        )}
        {!loading && plotData.length === 0 && (
          <div className="text-sm text-slate-500 py-10 text-center">
            No data available for the selected configuration.
          </div>
        )}
        {!loading && plotData.length > 0 && (
          <Plot
            data={plotData}
            layout={{
              autosize: true,
              height: 500,
              margin: { l: 60, r: 40, t: 40, b: 60 },
              xaxis: {
                title: 'Timestamp',
                showgrid: true,
                gridcolor: '#e2e8f0',
              },
              yaxis: {
                title: `${currentProfile?.label ?? ''} (${currentProfile?.unit ?? ''})`,
                showgrid: true,
                gridcolor: '#e2e8f0',
              },
              hovermode: 'closest',
              plot_bgcolor: '#fafafa',
              paper_bgcolor: 'white',
              font: {
                family: 'Inter, system-ui, sans-serif',
                size: 12,
              },
              legend: {
                x: 1,
                xanchor: 'right',
                y: 1,
                bgcolor: 'rgba(255, 255, 255, 0.8)',
                bordercolor: '#cbd5e1',
                borderwidth: 1,
              },
            }}
            config={{
              responsive: true,
              displayModeBar: true,
              displaylogo: false,
              modeBarButtonsToRemove: ['lasso2d', 'select2d'],
            }}
            style={{ width: '100%', height: '100%' }}
          />
        )}
      </CardContent>
    </Card>
  );
};

const cacheKey = (projectId, scenarioId, metric, aggregation) =>
  `${projectId}-${scenarioId}-${metric}-${aggregation}`;

export default DetailedChart;
