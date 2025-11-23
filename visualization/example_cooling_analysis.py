
"""
Example script demonstrating the new cooling analysis visualizations.

This script shows how to:
1. Create load duration curves for cooling/heating demand
2. Analyze cooling energy breakdown (shading vs ventilation savings)
3. Visualize the results

Prerequisites:
- Model results must be available for the scenarios you want to analyze
- Run main_server.py first to generate the necessary data
"""

from pathlib import Path
from utils.config import Config
from utils.db import fetch_input_tables, init_project_db
from model.main import run_operation_model
from visualization.cooling_analysis import (
    create_load_duration_curve,
    analyze_cooling_breakdown,
    visualize_cooling_breakdown
)


def example_load_duration_curve():
    """Example: Create load duration curves for cooling demand."""
    print("\n" + "="*60)
    print("EXAMPLE 1: Load Duration Curve")
    print("="*60)
    
    # Setup
    cfg = Config(
        project_name="AUT_2020_cooling",
        project_path=Path(__file__).parent / "projects" / "AUT_2020_cooling"
    )
    
    # Make sure we have results (uncomment if needed)
    # init_project_db(cfg)
    # run_operation_model(
    #     config=cfg,
    #     scenario_ids=[1, 2, 3],
    #     run_ref=True,
    #     run_opt=False,
    #     save_hour=True
    # )
    
    input_tables = fetch_input_tables(config=cfg)
    
    # Create load duration curve for cooling
    print("\nCreating cooling load duration curve...")
    fig_cooling = create_load_duration_curve(
        scenarios=[1, 2, 3],  # Adjust scenario IDs as needed
        config=cfg,
        input_tables=input_tables,
        var_name='Q_RoomCooling',
        show_quartiles=True,
        title='Cooling Load Duration Curve'
    )
    fig_cooling.show()
    
    # Create load duration curve for heating
    print("\nCreating heating load duration curve...")
    fig_heating = create_load_duration_curve(
        scenarios=[1, 2, 3],
        config=cfg,
        input_tables=input_tables,
        var_name='Q_RoomHeating',
        show_quartiles=True,
        title='Heating Load Duration Curve'
    )
    fig_heating.show()


def example_cooling_breakdown():
    """Example: Analyze cooling energy breakdown."""
    print("\n" + "="*60)
    print("EXAMPLE 2: Cooling Energy Breakdown")
    print("="*60)
    
    # Setup
    cfg = Config(
        project_name="AUT_2020_cooling",
        project_path=Path(__file__).parent / "projects" / "AUT_2020_cooling"
    )
    
    input_tables = fetch_input_tables(config=cfg)
    
    # Analyze cooling breakdown for a scenario
    print("\nAnalyzing cooling breakdown...")
    breakdown = analyze_cooling_breakdown(
        scenario_id=1,  # Adjust scenario ID as needed
        config=cfg,
        input_tables=input_tables
    )
    
    # Visualize the breakdown
    print("\nCreating breakdown visualization...")
    fig = visualize_cooling_breakdown(breakdown, scenario_id=1)
    fig.show()
    
    # Print detailed results
    print("\n" + "-"*60)
    print("DETAILED RESULTS:")
    print("-"*60)
    print(f"Baseline cooling demand: {breakdown['results']['baseline']/1000:.2f} kWh")
    print(f"With shading only: {breakdown['results']['with_shading']/1000:.2f} kWh")
    print(f"With both features: {breakdown['results']['full']/1000:.2f} kWh")
    print()
    print(f"Savings from shading: {breakdown['savings']['shading_savings_Wh']/1000:.2f} kWh "
          f"({breakdown['savings']['shading_savings_percent']:.1f}%)")
    print(f"Savings from ventilation: {breakdown['savings']['ventilation_savings_Wh']/1000:.2f} kWh "
          f"({breakdown['savings']['ventilation_savings_percent']:.1f}%)")
    print(f"Total savings: {breakdown['savings']['total_savings_Wh']/1000:.2f} kWh "
          f"({breakdown['savings']['total_savings_percent']:.1f}%)")


def example_combined_analysis():
    """Example: Combined analysis for multiple scenarios."""
    print("\n" + "="*60)
    print("EXAMPLE 3: Combined Analysis")
    print("="*60)
    
    cfg = Config(
        project_name="AUT_2020_cooling",
        project_path=Path(__file__).parent / "projects" / "AUT_2020_cooling"
    )
    
    input_tables = fetch_input_tables(config=cfg)
    scenarios = [1, 2, 3]  # Adjust as needed
    
    # Analyze breakdown for multiple scenarios
    print("\nAnalyzing multiple scenarios...")
    all_breakdowns = {}
    for scenario_id in scenarios:
        print(f"\nScenario {scenario_id}:")
        breakdown = analyze_cooling_breakdown(
            scenario_id=scenario_id,
            config=cfg,
            input_tables=input_tables
        )
        all_breakdowns[scenario_id] = breakdown
    
    # Create comparison visualization
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Load Duration Curves', 'Cooling Savings Comparison'),
        specs=[[{'type': 'scatter'}, {'type': 'bar'}]]
    )
    
    # Add load duration curves
    for scenario_id in scenarios:
        hourly = all_breakdowns[scenario_id]['hourly_results']['full']
        sorted_data = np.sort(hourly)[::-1]
        fig.add_trace(
            go.Scatter(
                x=list(range(len(sorted_data))),
                y=sorted_data,
                name=f'Scenario {scenario_id}'
            ),
            row=1, col=1
        )
    
    # Add savings comparison
    import numpy as np
    shading_savings = [all_breakdowns[s]['savings']['shading_savings_Wh']/1000 for s in scenarios]
    vent_savings = [all_breakdowns[s]['savings']['ventilation_savings_Wh']/1000 for s in scenarios]
    
    fig.add_trace(
        go.Bar(name='Shading Savings', x=[f'S{s}' for s in scenarios], y=shading_savings),
        row=1, col=2
    )
    fig.add_trace(
        go.Bar(name='Ventilation Savings', x=[f'S{s}' for s in scenarios], y=vent_savings),
        row=1, col=2
    )
    
    fig.update_xaxes(title_text="Hours", row=1, col=1)
    fig.update_xaxes(title_text="Scenario", row=1, col=2)
    fig.update_yaxes(title_text="Cooling Demand (W)", row=1, col=1)
    fig.update_yaxes(title_text="Energy Saved (kWh)", row=1, col=2)
    
    fig.update_layout(height=500, showlegend=True, title_text="Cooling Analysis Comparison")
    fig.show()


if __name__ == "__main__":
    print("\n" + "="*60)
    print("COOLING ANALYSIS EXAMPLES")
    print("="*60)
    print("\nThis script demonstrates the new cooling analysis features.")
    print("Uncomment the examples you want to run.\n")
    
    # Uncomment to run examples:
    
    # Example 1: Load duration curves
    example_load_duration_curve()
    
    # Example 2: Cooling breakdown for single scenario
    # example_cooling_breakdown()
    
    # Example 3: Combined analysis for multiple scenarios
    # example_combined_analysis()
    
    print("\nTo run examples, uncomment the function calls in the __main__ block.")
