
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List
from model.scenario import OperationScenario
from model.model_ref import RefOperationModel
from utils.config import Config
from utils.parquet import read_parquet
from utils.db import create_db_conn


def create_load_duration_curve(
    scenarios: List[int],
    config: Config,
    input_tables: dict,
    var_name: str = 'Q_RoomCooling',
    show_quartiles: bool = True,
    title: str = None
):
    """
    Create a load duration curve for heating or cooling demand.
    
    Args:
        scenarios: List of scenario IDs to analyze
        config: Configuration object
        input_tables: Dictionary of input tables
        var_name: Variable name to plot ('Q_RoomCooling' or 'Q_RoomHeating')
        show_quartiles: If True and multiple scenarios, show quartile ranges
        title: Optional title for the plot
    
    Returns:
        Plotly figure object
    """
    # Collect data from all scenarios
    all_data = []
    scenario_labels = []
    
    for scenario_id in scenarios:
        # Load hourly results
        try:
            hourly_df = read_parquet(
                file_name=f"OperationResult_RefHour_S{scenario_id}",
                folder=config.output
            )
            if var_name in hourly_df.columns:
                data = hourly_df[var_name].to_numpy()
                all_data.append(data)
                scenario_labels.append(f"Scenario {scenario_id}")
        except Exception as e:
            print(f"Could not load data for scenario {scenario_id}: {e}")
            continue
    
    if len(all_data) == 0:
        raise ValueError("No data loaded for any scenario")
    
    # Sort each scenario's data in descending order (load duration curve)
    sorted_data = [np.sort(d)[::-1] for d in all_data]
    hours = np.arange(len(sorted_data[0]))
    
    # Create figure
    fig = go.Figure()
    
    if len(scenarios) > 1 and show_quartiles:
        # Calculate quartiles across scenarios
        data_array = np.array(sorted_data)
        median = np.median(data_array, axis=0)
        q25 = np.percentile(data_array, 25, axis=0)
        q75 = np.percentile(data_array, 75, axis=0)
        
        # Add quartile range as shaded area
        fig.add_trace(go.Scatter(
            x=hours,
            y=q75,
            fill=None,
            mode='lines',
            line_color='rgba(0,0,0,0)',
            showlegend=False,
            name='75th percentile'
        ))
        
        fig.add_trace(go.Scatter(
            x=hours,
            y=q25,
            fill='tonexty',
            fillcolor='rgba(68, 138, 255, 0.2)',
            line_color='rgba(0,0,0,0)',
            name='25-75% Range',
            mode='lines'
        ))
        
        # Add median line
        fig.add_trace(go.Scatter(
            x=hours,
            y=median,
            name='Median',
            line=dict(color='rgb(68, 138, 255)', width=2)
        ))
    else:
        # Single scenario or no quartiles - plot individual curves
        colors = ['rgb(68, 138, 255)', 'rgb(255, 138, 68)', 'rgb(138, 255, 68)', 
                  'rgb(255, 68, 138)', 'rgb(138, 68, 255)']
        for i, (data, label) in enumerate(zip(sorted_data, scenario_labels)):
            fig.add_trace(go.Scatter(
                x=hours,
                y=data,
                name=label,
                line=dict(color=colors[i % len(colors)], width=2)
            ))
    
    # Update layout
    if title is None:
        title = f"Load Duration Curve - {var_name}"
    
    fig.update_layout(
        title=title,
        xaxis_title="Hours (sorted by demand)",
        yaxis_title=f"{var_name} (W)",
        hovermode='x unified',
        template='plotly_white',
        font=dict(size=12)
    )
    
    return fig


def analyze_cooling_breakdown(
    scenario_id: int,
    config: Config,
    input_tables: dict
):
    """
    Analyze cooling energy breakdown by running the model 3 times:
    1. Baseline (no shading, no ventilation)
    2. Shading only
    3. Full (both features enabled)
    
    Args:
        scenario_id: Scenario ID to analyze
        config: Configuration object
        input_tables: Dictionary of input tables
    
    Returns:
        Dictionary with results and savings breakdown
    """
    results = {}
    hourly_results = {}
    
    print(f"Running cooling breakdown analysis for scenario {scenario_id}...")
    
    # 1. Baseline (no shading, no ventilation)
    print("  Running baseline (no shading, no ventilation)...")
    scenario_baseline = OperationScenario(
        scenario_id=scenario_id,
        config=config,
        input_tables=input_tables
    )
    scenario_baseline.enable_shading = False
    scenario_baseline.enable_dynamic_ventilation = False
    model_baseline = RefOperationModel(scenario_baseline).solve()
    results['baseline'] = model_baseline.Q_RoomCooling.sum()
    hourly_results['baseline'] = model_baseline.Q_RoomCooling.copy()
    
    # 2. Shading only
    print("  Running with shading only...")
    scenario_shading = OperationScenario(
        scenario_id=scenario_id,
        config=config,
        input_tables=input_tables
    )
    scenario_shading.enable_shading = True
    scenario_shading.enable_dynamic_ventilation = False
    model_shading = RefOperationModel(scenario_shading).solve()
    results['with_shading'] = model_shading.Q_RoomCooling.sum()
    hourly_results['with_shading'] = model_shading.Q_RoomCooling.copy()
    
    # 3. Full (both features)
    print("  Running with both features...")
    scenario_full = OperationScenario(
        scenario_id=scenario_id,
        config=config,
        input_tables=input_tables
    )
    scenario_full.enable_shading = True
    scenario_full.enable_dynamic_ventilation = True
    model_full = RefOperationModel(scenario_full).solve()
    results['full'] = model_full.Q_RoomCooling.sum()
    hourly_results['full'] = model_full.Q_RoomCooling.copy()
    
    # Calculate savings
    savings = {
        'shading_savings_Wh': results['baseline'] - results['with_shading'],
        'ventilation_savings_Wh': results['with_shading'] - results['full'],
        'total_savings_Wh': results['baseline'] - results['full'],
        'shading_savings_percent': ((results['baseline'] - results['with_shading']) / results['baseline'] * 100) if results['baseline'] > 0 else 0,
        'ventilation_savings_percent': ((results['with_shading'] - results['full']) / results['baseline'] * 100) if results['baseline'] > 0 else 0,
        'total_savings_percent': ((results['baseline'] - results['full']) / results['baseline'] * 100) if results['baseline'] > 0 else 0
    }
    
    print(f"  Analysis complete!")
    print(f"    Baseline cooling: {results['baseline']/1000:.2f} kWh")
    print(f"    Savings from shading: {savings['shading_savings_Wh']/1000:.2f} kWh ({savings['shading_savings_percent']:.1f}%)")
    print(f"    Savings from ventilation: {savings['ventilation_savings_Wh']/1000:.2f} kWh ({savings['ventilation_savings_percent']:.1f}%)")
    print(f"    Total savings: {savings['total_savings_Wh']/1000:.2f} kWh ({savings['total_savings_percent']:.1f}%)")
    
    return {
        'results': results,
        'savings': savings,
        'hourly_results': hourly_results
    }


def visualize_cooling_breakdown(breakdown_data: dict, scenario_id: int):
    """
    Create visualization of cooling energy breakdown.
    
    Args:
        breakdown_data: Output from analyze_cooling_breakdown
        scenario_id: Scenario ID for title
    
    Returns:
        Plotly figure object
    """
    results = breakdown_data['results']
    savings = breakdown_data['savings']
    
    # Create stacked bar chart
    fig = go.Figure()
    
    # Convert to kWh for readability
    baseline_kWh = results['baseline'] / 1000
    shading_savings_kWh = savings['shading_savings_Wh'] / 1000
    ventilation_savings_kWh = savings['ventilation_savings_Wh'] / 1000
    final_cooling_kWh = results['full'] / 1000
    
    # Create breakdown bars
    categories = ['Cooling Energy Breakdown']
    
    fig.add_trace(go.Bar(
        name='Final Cooling Demand',
        x=categories,
        y=[final_cooling_kWh],
        marker_color='rgb(255, 100, 100)',
        text=[f'{final_cooling_kWh:.1f} kWh'],
        textposition='inside'
    ))
    
    fig.add_trace(go.Bar(
        name='Saved by Ventilation',
        x=categories,
        y=[ventilation_savings_kWh],
        marker_color='rgb(100, 200, 255)',
        text=[f'{ventilation_savings_kWh:.1f} kWh ({savings["ventilation_savings_percent"]:.1f}%)'],
        textposition='inside'
    ))
    
    fig.add_trace(go.Bar(
        name='Saved by Shading',
        x=categories,
        y=[shading_savings_kWh],
        marker_color='rgb(255, 200, 100)',
        text=[f'{shading_savings_kWh:.1f} kWh ({savings["shading_savings_percent"]:.1f}%)'],
        textposition='inside'
    ))
    
    fig.update_layout(
        title=f'Cooling Energy Breakdown - Scenario {scenario_id}',
        yaxis_title='Energy (kWh)',
        barmode='stack',
        template='plotly_white',
        font=dict(size=12),
        showlegend=True,
        height=500
    )
    
    # Add annotation showing baseline
    fig.add_annotation(
        x=0,
        y=baseline_kWh,
        text=f'Baseline: {baseline_kWh:.1f} kWh',
        showarrow=True,
        arrowhead=2,
        ax=100,
        ay=-40
    )
    
    return fig


if __name__ == "__main__":
    # Example usage
    from utils.config import Config
    from utils.db import fetch_input_tables
    from pathlib import Path
    
    # Setup config (adjust path as needed)
    cfg = Config(
        project_name="AUT_2020_cooling",
        project_path=Path(__file__).parent.parent / "projects" / "AUT_2020_cooling"
    )
    
    input_tables = fetch_input_tables(config=cfg)
    
    # Example 1: Load duration curve for multiple scenarios
    # scenarios = [1, 2, 3]
    # fig = create_load_duration_curve(
    #     scenarios=scenarios,
    #     config=cfg,
    #     input_tables=input_tables,
    #     var_name='Q_RoomCooling',
    #     show_quartiles=True
    # )
    # fig.show()
    
    # Example 2: Cooling breakdown analysis
    # breakdown = analyze_cooling_breakdown(
    #     scenario_id=1,
    #     config=cfg,
    #     input_tables=input_tables
    # )
    # fig = visualize_cooling_breakdown(breakdown, scenario_id=1)
    # fig.show()
    
    print("Cooling analysis module loaded. Uncomment examples to run.")
