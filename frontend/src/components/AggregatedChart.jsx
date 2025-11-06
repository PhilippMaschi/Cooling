import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import Plot from 'react-plotly.js';
import { generateMockScenarioData, mockScenarios, mockDelay } from '../mock';
import { Loader2 } from 'lucide-react';

const AggregatedChart = ({ selectedScenarios }) => {
  const [loading, setLoading] = useState(false);
  const [scenarioData, setScenarioData] = useState({});
  const [chartType, setChartType] = useState('box');

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

  const createBoxPlot = () => {
    const traces = [];
    const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

    selectedScenarios.forEach((scenarioId, index) => {
      if (scenarioData[scenarioId]) {
        const scenario = mockScenarios.find(s => s.id === scenarioId);
        traces.push({
          y: scenarioData[scenarioId].coolingLoad,
          type: 'box',
          name: scenario ? scenario.name : `Scenario ${scenarioId}`,
          marker: {
            color: colors[index % colors.length]
          },
          boxmean: 'sd'
        });
      }
    });

    return traces;
  };

  const createBarChart = () => {
    const metrics = ['Mean', 'Median', 'Max', 'Min', 'Std Dev'];
    const traces = [];
    const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

    selectedScenarios.forEach((scenarioId, index) => {
      if (scenarioData[scenarioId]) {
        const data = scenarioData[scenarioId].coolingLoad;
        const scenario = mockScenarios.find(s => s.id === scenarioId);
        
        const mean = data.reduce((sum, val) => sum + val, 0) / data.length;
        const sorted = [...data].sort((a, b) => a - b);
        const median = sorted[Math.floor(sorted.length / 2)];
        const max = Math.max(...data);
        const min = Math.min(...data);
        const variance = data.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / data.length;
        const stdDev = Math.sqrt(variance);

        traces.push({
          x: metrics,
          y: [mean, median, max, min, stdDev],
          type: 'bar',
          name: scenario ? scenario.name : `Scenario ${scenarioId}`,
          marker: {
            color: colors[index % colors.length]
          }
        });
      }
    });

    return traces;
  };

  const createViolinPlot = () => {
    const traces = [];
    const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

    selectedScenarios.forEach((scenarioId, index) => {
      if (scenarioData[scenarioId]) {
        const scenario = mockScenarios.find(s => s.id === scenarioId);
        traces.push({
          y: scenarioData[scenarioId].coolingLoad,
          type: 'violin',
          name: scenario ? scenario.name : `Scenario ${scenarioId}`,
          marker: {
            color: colors[index % colors.length]
          },
          box: {
            visible: true
          },
          meanline: {
            visible: true
          }
        });
      }
    });

    return traces;
  };

  const getPlotData = () => {
    switch (chartType) {
      case 'box':
        return createBoxPlot();
      case 'bar':
        return createBarChart();
      case 'violin':
        return createViolinPlot();
      default:
        return [];
    }
  };

  const getYAxisTitle = () => {
    if (chartType === 'bar') {
      return 'Value (kW)';
    }
    return 'Cooling Load (kW)';
  };

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
        <CardTitle className="text-lg">Statistical Comparison</CardTitle>
        <CardDescription>Compare cooling load distributions across all scenarios</CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs value={chartType} onValueChange={setChartType} className="mb-6">
          <TabsList className="grid w-full max-w-md grid-cols-3">
            <TabsTrigger value="box">Box Plot</TabsTrigger>
            <TabsTrigger value="bar">Bar Chart</TabsTrigger>
            <TabsTrigger value="violin">Violin Plot</TabsTrigger>
          </TabsList>
        </Tabs>

        <div className="w-full">
          <Plot
            data={getPlotData()}
            layout={{
              autosize: true,
              height: 500,
              margin: { l: 60, r: 40, t: 40, b: 100 },
              xaxis: {
                title: chartType === 'bar' ? 'Statistics' : 'Scenarios',
                showgrid: false
              },
              yaxis: {
                title: getYAxisTitle(),
                showgrid: true,
                gridcolor: '#e2e8f0'
              },
              plot_bgcolor: '#fafafa',
              paper_bgcolor: 'white',
              font: {
                family: 'Inter, system-ui, sans-serif',
                size: 12
              },
              showlegend: chartType === 'bar',
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

export default AggregatedChart;