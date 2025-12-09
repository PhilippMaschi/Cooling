import os
import sys
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path

# Get the absolute path of the directory two levels up
two_levels_up = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# Add this directory to sys.path
sys.path.insert(0, two_levels_up)

from model.scenario import OperationScenario
from visualization.Visualization_class import MotherVisualization
from utils.config import Config
from utils.db import fetch_input_tables


class CoolingLoadVisualizer:
    """
    Visualizer for cooling load scenarios in reference mode only.
    Creates three main plots:
    1. All cooling loads as thin line plots (can handle thousands of scenarios)
    2. Summed cooling load over the whole year (single line)
    3. Total cooling demand as boxplot
    """
    
    def __init__(self, cfg: Config, input_tables):
        """
        Initialize the visualizer with configuration and input tables.
        
        Args:
            cfg: Config object containing project configuration
            input_tables: Input tables from database
        """
        self.cfg = cfg
        self.input_tables = input_tables
        self.scenarios_data = {}  # Will store {scenario_id: {'hourly': df, 'yearly': df}}
        
    def load_scenarios(self, scenario_ids: list):
        """
        Load reference mode results for multiple scenarios.
        
        Args:
            scenario_ids: List of scenario IDs to load
        """
        print(f"Loading {len(scenario_ids)} scenarios...")
        for scen_id in scenario_ids:
            try:
                scenario = OperationScenario(
                    scenario_id=scen_id, 
                    config=self.cfg, 
                    input_tables=self.input_tables
                )
                
                # Use MotherVisualization to fetch results
                vis = MotherVisualization(scenario=scenario)
                hourly_ref = vis.hourly_results_reference_df
                yearly_ref = vis.yearly_results_reference_df
                
                # Store the data
                self.scenarios_data[scen_id] = {
                    'hourly': hourly_ref,
                    'yearly': yearly_ref
                }
                print(f"  ✓ Loaded scenario {scen_id}")
                
            except Exception as e:
                print(f"  ✗ Failed to load scenario {scen_id}: {e}")
        
        print(f"Successfully loaded {len(self.scenarios_data)} scenarios")
    
    def plot_all_cooling_loads(self, cooling_var: str = "Q_RoomCooling"):
        """
        Plot 1: Show all cooling loads of all scenarios as very thin line plots.
        Optimized for handling thousands of lines efficiently.
        
        Args:
            cooling_var: Name of the cooling variable in hourly results
        """
        fig = go.Figure()
        x_axis = np.arange(8760)
        
        # Use very thin lines and low opacity for efficiency with many scenarios
        for scen_id, data in self.scenarios_data.items():
            hourly_df = data['hourly']
            
            if cooling_var in hourly_df.columns:
                fig.add_trace(
                    go.Scattergl(  # Use Scattergl for better performance with many lines
                        x=x_axis,
                        y=hourly_df[cooling_var],
                        mode='lines',
                        name=f'Scenario {scen_id}',
                        line=dict(width=0.5),  # Very thin lines
                        opacity=0.6,
                        hovertemplate=f'Scenario {scen_id}<br>Hour: %{{x}}<br>Cooling: %{{y:.2f}}<extra></extra>'
                    )
                )
        
        fig.update_layout(
            title=f"All Cooling Loads - {len(self.scenarios_data)} Scenarios (Reference Mode)",
            xaxis_title="Hour of Year",
            yaxis_title=f"{cooling_var} (W)",
            hovermode='closest',
            height=600,
            width=1400,
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.01
            )
        )
        
        fig.show()
        return fig
    
    def plot_summed_yearly_cooling(self, cooling_var: str = "Q_RoomCooling"):
        """
        Plot 2: Show the summed up cooling load over the whole year (one line plot).
        This creates a cumulative sum over the 8760 hours.
        
        Args:
            cooling_var: Name of the cooling variable in hourly results
        """
        fig = go.Figure()
        x_axis = np.arange(8760)
        
        for scen_id, data in self.scenarios_data.items():
            hourly_df = data['hourly']
            
            if cooling_var in hourly_df.columns:
                # Calculate cumulative sum
                cumulative_cooling = hourly_df[cooling_var].cumsum()
                
                fig.add_trace(
                    go.Scatter(
                        x=x_axis,
                        y=cumulative_cooling,
                        mode='lines',
                        name=f'Scenario {scen_id}',
                        line=dict(width=1.5),
                        hovertemplate=f'Scenario {scen_id}<br>Hour: %{{x}}<br>Cumulative: %{{y:.2f}} Wh<extra></extra>'
                    )
                )
        
        fig.update_layout(
            title=f"Cumulative Cooling Load Over Year - {len(self.scenarios_data)} Scenarios (Reference Mode)",
            xaxis_title="Hour of Year",
            yaxis_title=f"Cumulative {cooling_var} (Wh)",
            hovermode='closest',
            height=600,
            width=1400,
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.01
            )
        )
        
        fig.show()
        return fig
    
    def plot_total_cooling_boxplot(self, cooling_var: str = "Q_Cooling"):
        """
        Plot 3: Show the total cooling demand as boxplot.
        Single box with points being the summed Q_Cooling from yearly results.
        
        Args:
            cooling_var: Name of the cooling variable in yearly results
        """
        # Collect total cooling demands from yearly results
        total_cooling_demands = []
        scenario_ids = []
        
        for scen_id, data in self.scenarios_data.items():
            yearly_df = data['yearly']
            
            if not yearly_df.empty and cooling_var in yearly_df.columns:
                # Get the total cooling demand for this scenario
                total_demand = yearly_df[cooling_var].iloc[0]
                total_cooling_demands.append(total_demand)
                scenario_ids.append(scen_id)
        
        # Create boxplot
        fig = go.Figure()
        
        fig.add_trace(
            go.Box(
                y=total_cooling_demands,
                name='Total Cooling Demand',
                boxmean='sd',  # Show mean and standard deviation
                marker=dict(
                    color='lightblue',
                    size=8
                ),
                boxpoints='all',  # Show all points
                jitter=0.3,  # Add jitter to see overlapping points
                pointpos=-1.8,  # Position points to the left of box
                text=[f'Scenario {sid}' for sid in scenario_ids],
                hovertemplate='%{text}<br>Total Cooling: %{y:.2f} Wh<extra></extra>'
            )
        )
        
        fig.update_layout(
            title=f"Total Annual Cooling Demand Distribution - {len(total_cooling_demands)} Scenarios (Reference Mode)",
            yaxis_title=f"Total {cooling_var} (Wh)",
            height=700,
            width=800,
            showlegend=False
        )
        
        # Add statistics annotation
        if total_cooling_demands:
            mean_val = np.mean(total_cooling_demands)
            median_val = np.median(total_cooling_demands)
            std_val = np.std(total_cooling_demands)
            
            fig.add_annotation(
                text=f"Mean: {mean_val:.2f} Wh<br>Median: {median_val:.2f} Wh<br>Std Dev: {std_val:.2f} Wh<br>N: {len(total_cooling_demands)}",
                xref="paper", yref="paper",
                x=0.98, y=0.98,
                showarrow=False,
                bgcolor="white",
                bordercolor="black",
                borderwidth=1,
                xanchor="right",
                yanchor="top"
            )
        
        fig.show()
        return fig
    
    def create_all_plots(self, cooling_var_hourly: str = "Q_RoomCooling", 
                        cooling_var_yearly: str = "Q_Cooling"):
        """
        Create all three plots in sequence.
        
        Args:
            cooling_var_hourly: Name of cooling variable in hourly results
            cooling_var_yearly: Name of cooling variable in yearly results
        """
        print("\n" + "="*80)
        print("Creating Cooling Load Visualizations")
        print("="*80)
        
        print("\n[1/3] Plotting all cooling loads...")
        self.plot_all_cooling_loads(cooling_var=cooling_var_hourly)
        
        print("\n[2/3] Plotting cumulative yearly cooling...")
        self.plot_summed_yearly_cooling(cooling_var=cooling_var_hourly)
        
        print("\n[3/3] Plotting total cooling demand boxplot...")
        self.plot_total_cooling_boxplot(cooling_var=cooling_var_yearly)
        
        print("\n" + "="*80)
        print("All visualizations complete!")
        print("="*80 + "\n")


if __name__ == "__main__":
    # Configuration
    cfg = Config(
        project_name="AUT_2020_cooling", 
        project_path=Path(__file__).parent.parent / "projects" / "AUT_2020_cooling"
    )
    input_tables = fetch_input_tables(config=cfg)
    
    # Define scenarios to visualize
    scenarios_to_visualize = [1, 2, 3]  # Modify this list as needed
    
    # Create visualizer
    visualizer = CoolingLoadVisualizer(cfg=cfg, input_tables=input_tables)
    
    # Load scenarios
    visualizer.load_scenarios(scenario_ids=scenarios_to_visualize)
    
    # Create all plots
    visualizer.create_all_plots(
        cooling_var_hourly="Q_RoomCooling",  # Variable name in hourly results
        cooling_var_yearly="Q_Cooling"       # Variable name in yearly results
    )
