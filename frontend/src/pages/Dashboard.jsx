import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Button } from '../components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Badge } from '../components/ui/badge';
import { BarChart3, LineChart, TrendingDown, Zap, Cloud } from 'lucide-react';
import ScenarioSelector from '../components/ScenarioSelector';
import DetailedChart from '../components/DetailedChart';
import AggregatedChart from '../components/AggregatedChart';
import StatsOverview from '../components/StatsOverview';
import { mockProjects, mockScenarios, mockDelay } from '../mock';

const Dashboard = () => {
  const [selectedProject, setSelectedProject] = useState('');
  const [projects, setProjects] = useState([]);
  const [scenarios, setScenarios] = useState([]);
  const [selectedScenarios, setSelectedScenarios] = useState([]);
  const [viewMode, setViewMode] = useState('detailed'); // 'detailed' or 'aggregated'
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadProjects();
  }, []);

  useEffect(() => {
    if (selectedProject) {
      loadScenarios(selectedProject);
    }
  }, [selectedProject]);

  const loadProjects = async () => {
    setLoading(true);
    await mockDelay(300);
    setProjects(mockProjects);
    setLoading(false);
  };

  const loadScenarios = async (projectId) => {
    setLoading(true);
    await mockDelay(300);
    setScenarios(mockScenarios);
    setSelectedScenarios([]);
    setLoading(false);
  };

  const handleScenarioToggle = (scenarioId) => {
    setSelectedScenarios(prev => {
      if (prev.includes(scenarioId)) {
        return prev.filter(id => id !== scenarioId);
      } else {
        // Limit to 3 scenarios for detailed view
        if (viewMode === 'detailed' && prev.length >= 3) {
          return prev;
        }
        return [...prev, scenarioId];
      }
    });
  };

  const handleViewModeChange = (mode) => {
    setViewMode(mode);
    if (mode === 'aggregated') {
      // Select all scenarios for aggregated view
      setSelectedScenarios(scenarios.map(s => s.id));
    } else {
      // Limit to first 3 for detailed view
      setSelectedScenarios(scenarios.slice(0, 3).map(s => s.id));
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Header */}
      <header className="border-b border-slate-200 bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-lg">
                <BarChart3 className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-slate-900">Model Results Viewer</h1>
                <p className="text-sm text-slate-600">Cooling Load Analysis Platform</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-6 py-8">
        {/* Project Selection */}
        <Card className="mb-6 border-slate-200 shadow-sm">
          <CardHeader>
            <CardTitle className="text-lg">Project Selection</CardTitle>
            <CardDescription>Select a project to view its scenario results</CardDescription>
          </CardHeader>
          <CardContent>
            <Select value={selectedProject} onValueChange={setSelectedProject}>
              <SelectTrigger className="w-full max-w-md">
                <SelectValue placeholder="Choose a project..." />
              </SelectTrigger>
              <SelectContent>
                {projects.map(project => (
                  <SelectItem key={project.id} value={project.id}>
                    {project.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </CardContent>
        </Card>

        {selectedProject && (
          <>
            {/* View Mode Tabs */}
            <Card className="mb-6 border-slate-200 shadow-sm">
              <CardContent className="pt-6">
                <Tabs value={viewMode} onValueChange={handleViewModeChange} className="w-full">
                  <TabsList className="grid w-full max-w-md grid-cols-2">
                    <TabsTrigger value="detailed" className="flex items-center gap-2">
                      <LineChart className="w-4 h-4" />
                      Detailed View
                    </TabsTrigger>
                    <TabsTrigger value="aggregated" className="flex items-center gap-2">
                      <BarChart3 className="w-4 h-4" />
                      Aggregated View
                    </TabsTrigger>
                  </TabsList>
                </Tabs>

                <div className="mt-4">
                  {viewMode === 'detailed' && (
                    <Badge variant="outline" className="text-xs">
                      Select up to 3 scenarios for comparison
                    </Badge>
                  )}
                  {viewMode === 'aggregated' && (
                    <Badge variant="outline" className="text-xs">
                      All scenarios included for statistical analysis
                    </Badge>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Scenario Selection */}
            <ScenarioSelector
              scenarios={scenarios}
              selectedScenarios={selectedScenarios}
              onToggle={handleScenarioToggle}
              viewMode={viewMode}
              loading={loading}
            />

            {/* Statistics Overview */}
            {selectedScenarios.length > 0 && (
              <StatsOverview
                selectedScenarios={selectedScenarios}
                viewMode={viewMode}
              />
            )}

            {/* Charts */}
            {selectedScenarios.length > 0 && (
              <div className="space-y-6">
                {viewMode === 'detailed' ? (
                  <DetailedChart selectedScenarios={selectedScenarios} />
                ) : (
                  <AggregatedChart selectedScenarios={selectedScenarios} />
                )}
              </div>
            )}

            {selectedScenarios.length === 0 && (
              <Card className="border-slate-200 shadow-sm">
                <CardContent className="py-12">
                  <div className="text-center text-slate-500">
                    <Cloud className="w-16 h-16 mx-auto mb-4 opacity-50" />
                    <p className="text-lg font-medium mb-2">No scenarios selected</p>
                    <p className="text-sm">Select one or more scenarios to view the results</p>
                  </div>
                </CardContent>
              </Card>
            )}
          </>
        )}

        {!selectedProject && (
          <Card className="border-slate-200 shadow-sm">
            <CardContent className="py-16">
              <div className="text-center text-slate-500">
                <BarChart3 className="w-20 h-20 mx-auto mb-4 opacity-30" />
                <p className="text-xl font-medium mb-2">Welcome to Model Results Viewer</p>
                <p className="text-sm mb-6">Select a project from above to get started</p>
              </div>
            </CardContent>
          </Card>
        )}
      </main>
    </div>
  );
};

export default Dashboard;