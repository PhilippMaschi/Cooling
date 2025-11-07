import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Tabs, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Badge } from '../components/ui/badge';
import { BarChart3, LineChart, Cloud, AlertCircle } from 'lucide-react';
import ScenarioSelector from '../components/ScenarioSelector';
import DetailedChart from '../components/DetailedChart';
import AggregatedChart from '../components/AggregatedChart';
import StatsOverview from '../components/StatsOverview';
import { getProjects, getProjectScenarios } from '../lib/api';

const Dashboard = () => {
  const [selectedProject, setSelectedProject] = useState('');
  const [projects, setProjects] = useState([]);
  const [scenarios, setScenarios] = useState([]);
  const [scenarioStats, setScenarioStats] = useState([]);
  const [selectedScenarios, setSelectedScenarios] = useState([]);
  const [viewMode, setViewMode] = useState('detailed'); // 'detailed' or 'aggregated'
  const [projectLoading, setProjectLoading] = useState(false);
  const [scenarioLoading, setScenarioLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    loadProjects();
  }, []);

  useEffect(() => {
    if (selectedProject) {
      loadScenarios(selectedProject);
    }
  }, [selectedProject]);

  const loadProjects = async () => {
    setProjectLoading(true);
    setError('');
    try {
      const data = await getProjects();
      setProjects(data);
      if (data.length > 0) {
        setSelectedProject(data[0].id);
      }
    } catch (err) {
      setError('Unable to load projects. Please try again.');
    } finally {
      setProjectLoading(false);
    }
  };

  const loadScenarios = async (projectId) => {
    setScenarioLoading(true);
    setError('');
    try {
      const data = await getProjectScenarios(projectId);
      const normalized = data.scenarios.map((scenario) => ({
        ...scenario,
        id: scenario.scenario_id,
        name: `Scenario ${scenario.scenario_id}`,
        description: 'Yearly operation stats',
      }));
      setScenarios(normalized);
      setScenarioStats(normalized);
      if (viewMode === 'aggregated') {
        setSelectedScenarios(normalized.map((s) => s.id));
      } else {
        setSelectedScenarios(normalized.slice(0, 3).map((s) => s.id));
      }
    } catch (err) {
      setError('Unable to load scenarios for this project.');
      setScenarios([]);
      setScenarioStats([]);
      setSelectedScenarios([]);
    } finally {
      setScenarioLoading(false);
    }
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
            <Select value={selectedProject} onValueChange={setSelectedProject} disabled={projectLoading}>
              <SelectTrigger className="w-full max-w-md">
                <SelectValue placeholder={projectLoading ? 'Loading projects...' : 'Choose a project...'} />
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

        {error && (
          <Card className="mb-6 border-red-200 bg-red-50/60 shadow-sm">
            <CardContent className="py-4 flex items-center gap-3 text-red-700">
              <AlertCircle className="w-5 h-5" />
              <span>{error}</span>
            </CardContent>
          </Card>
        )}

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
              loading={scenarioLoading}
            />

            {/* Statistics Overview */}
            {selectedScenarios.length > 0 && (
              <StatsOverview
               selectedScenarios={selectedScenarios}
                scenarioStats={scenarioStats}
              />
            )}

            {/* Charts */}
            {selectedScenarios.length > 0 && (
              <div className="space-y-6">
                {viewMode === 'detailed' ? (
                  <DetailedChart
                    projectId={selectedProject}
                    selectedScenarios={selectedScenarios}
                  />
                ) : (
                  <AggregatedChart
                    projectId={selectedProject}
                    selectedScenarios={selectedScenarios}
                  />
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
