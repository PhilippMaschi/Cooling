import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Checkbox } from './ui/checkbox';
import { Badge } from './ui/badge';
import { CheckCircle2 } from 'lucide-react';

const ScenarioSelector = ({ scenarios, selectedScenarios, onToggle, viewMode, loading }) => {
  return (
    <Card className="mb-6 border-slate-200 shadow-sm">
      <CardHeader>
        <CardTitle className="text-lg">Scenario Selection</CardTitle>
        <CardDescription>
          {viewMode === 'detailed' 
            ? 'Choose up to 3 scenarios for detailed hourly comparison'
            : 'Select scenarios to include in statistical analysis'}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {scenarios.map(scenario => {
            const scenarioId = scenario.id ?? scenario.scenario_id;
            const isSelected = selectedScenarios.includes(scenarioId);
            const isDisabled = viewMode === 'detailed' && !isSelected && selectedScenarios.length >= 3;

            return (
              <div
                key={scenarioId}
                onClick={() => !isDisabled && onToggle(scenarioId)}
                className={`
                  p-4 border-2 rounded-lg cursor-pointer transition-all duration-200
                  ${
                    isSelected
                      ? 'border-blue-500 bg-blue-50/50 shadow-sm'
                      : isDisabled
                      ? 'border-slate-200 bg-slate-50 opacity-50 cursor-not-allowed'
                      : 'border-slate-200 hover:border-blue-300 hover:bg-slate-50'
                  }
                `}
              >
                <div className="flex items-start gap-3">
                  <div className="mt-0.5">
                    <Checkbox
                      checked={isSelected}
                      disabled={isDisabled}
                      onCheckedChange={() => !isDisabled && onToggle(scenarioId)}
                    />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="font-semibold text-sm text-slate-900 truncate">
                        {scenario.name || `Scenario ${scenarioId}`}
                      </h4>
                      {isSelected && (
                        <CheckCircle2 className="w-4 h-4 text-blue-600 flex-shrink-0" />
                      )}
                    </div>
                    <div className="text-xs text-slate-600 space-y-1">
                      <p>Total cooling: {(scenario.total_cooling_load ?? 0).toLocaleString(undefined, { maximumFractionDigits: 0 })} kWh</p>
                      <p>Peak electric: {(scenario.peak_electric_load ?? 0).toFixed(2)} kW</p>
                    </div>
                    <Badge variant="secondary" className="mt-2 text-xs">
                      ID: {scenarioId}
                    </Badge>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {loading && (
          <div className="mt-4 text-center text-sm text-slate-500">
            Loading scenarios...
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default ScenarioSelector;
