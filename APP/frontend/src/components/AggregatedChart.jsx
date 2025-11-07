import React, { useEffect, useMemo, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Tabs, TabsList, TabsTrigger } from './ui/tabs';
import Plot from 'react-plotly.js';
import { Loader2, AlertCircle } from 'lucide-react';
import { getScenarioTimeseries } from '../lib/api';

const AggregatedChart = ({ projectId, selectedScenarios }) => {
  const [chartType, setChartType] = useState('box');
  const [seriesCache, setSeriesCache] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    setSeriesCache({});
  }, [projectId]);

  useEffect(() => {
    const missing = selectedScenarios.filter((scenarioId) => !seriesCache[scenarioId]);
    if (!projectId || missing.length === 0) return;

    const fetchData = async () => {
      setLoading(true);
      setError('');
      try {
        const responses = await Promise.all(
          missing.map(async (scenarioId) => {
            const data = await getScenarioTimeseries(projectId, scenarioId, {
              metric: 'coolingLoad',
              aggregation: 'hourly',
            });
            return { scenarioId, values: data.values };
          })
        );
        setSeriesCache((prev) => {
          const next = { ...prev };
          responses.forEach(({ scenarioId, values }) => {
            next[scenarioId] = values;
          });
          return next;
        });
      } catch (err) {
        setError('Failed to load aggregated data.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [projectId, selectedScenarios, seriesCache]);

  const coolingValues = (scenarioId) => seriesCache[scenarioId] ?? [];

  const boxPlotData = useMemo(() => {
    const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];
    return selectedScenarios
      .map((scenarioId, index) => {
        const values = coolingValues(scenarioId);
        if (!values.length) return null;
        return {
          y: values,
          type: 'box',
          name: `Scenario ${scenarioId}`,
          marker: { color: colors[index % colors.length] },
          boxmean: 'sd',
        };
      })
      .filter(Boolean);
  }, [selectedScenarios, seriesCache]);

  const barChartData = useMemo(() => {
    const metrics = ['Mean', 'Median', 'Max', 'Min', 'Std Dev'];
    const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];
    return selectedScenarios
      .map((scenarioId, index) => {
        const values = coolingValues(scenarioId);
        if (!values.length) return null;
        const mean = values.reduce((sum, v) => sum + v, 0) / values.length;
        const sorted = [...values].sort((a, b) => a - b);
        const median = sorted[Math.floor(sorted.length / 2)];
        const max = Math.max(...values);
        const min = Math.min(...values);
        const variance =
          values.reduce((sum, v) => sum + Math.pow(v - mean, 2), 0) / values.length;
        const stdDev = Math.sqrt(variance);

        return {
          x: metrics,
          y: [mean, median, max, min, stdDev],
          type: 'bar',
          name: `Scenario ${scenarioId}`,
          marker: { color: colors[index % colors.length] },
        };
      })
      .filter(Boolean);
  }, [selectedScenarios, seriesCache]);

  const violinPlotData = useMemo(() => {
    const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];
    return selectedScenarios
      .map((scenarioId, index) => {
        const values = coolingValues(scenarioId);
        if (!values.length) return null;
        return {
          y: values,
          type: 'violin',
          name: `Scenario ${scenarioId}`,
          marker: { color: colors[index % colors.length] },
          box: { visible: true },
          meanline: { visible: true },
        };
      })
      .filter(Boolean);
  }, [selectedScenarios, seriesCache]);

  const plotData = useMemo(() => {
    switch (chartType) {
      case 'box':
        return boxPlotData;
      case 'bar':
        return barChartData;
      case 'violin':
        return violinPlotData;
      default:
        return [];
    }
  }, [chartType, boxPlotData, barChartData, violinPlotData]);

  const getYAxisTitle = () => (chartType === 'bar' ? 'Value (kW)' : 'Cooling Load (kW)');

  return (
    <Card className="border-slate-200 shadow-sm">
      <CardHeader>
        <CardTitle className="text-lg">Statistical Comparison</CardTitle>
        <CardDescription>Cooling load distribution using live scenario data</CardDescription>
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
            <p>Loading aggregated data...</p>
          </div>
        )}
        {!loading && (
          <>
            <Tabs value={chartType} onValueChange={setChartType} className="mb-6">
              <TabsList className="grid w-full max-w-md grid-cols-3">
                <TabsTrigger value="box">Box Plot</TabsTrigger>
                <TabsTrigger value="bar">Bar Chart</TabsTrigger>
                <TabsTrigger value="violin">Violin Plot</TabsTrigger>
              </TabsList>
            </Tabs>
            {plotData.length === 0 ? (
              <div className="text-sm text-slate-500 text-center py-10">
                No cooling load data available for the selected scenarios.
              </div>
            ) : (
              <Plot
                data={plotData}
                layout={{
                  autosize: true,
                  height: 500,
                  margin: { l: 60, r: 40, t: 40, b: 100 },
                  xaxis: {
                    title: chartType === 'bar' ? 'Statistics' : 'Scenarios',
                    showgrid: chartType === 'bar',
                  },
                  yaxis: {
                    title: getYAxisTitle(),
                    showgrid: true,
                    gridcolor: '#e2e8f0',
                  },
                  plot_bgcolor: '#fafafa',
                  paper_bgcolor: 'white',
                  font: {
                    family: 'Inter, system-ui, sans-serif',
                    size: 12,
                  },
                  showlegend: chartType === 'bar',
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
          </>
        )}
      </CardContent>
    </Card>
  );
};

export default AggregatedChart;
