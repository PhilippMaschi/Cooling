import pandas as pd
import sqlalchemy.exc
import os
import sys

# Get the absolute path of the directory two levels up
two_levels_up = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# Add this directory to sys.path
sys.path.insert(0, two_levels_up)
from model.scenario import OperationScenario
from model.model_opt import OptInstance, OptOperationModel
from model.model_ref import RefOperationModel
from model.data_collector import RefDataCollector, OptDataCollector
from utils.db import create_db_conn
from utils.parquet import read_parquet


class MotherVisualization:
    def __init__(self, scenario: OperationScenario):
        self.scenario = scenario
        (
            self.hourly_results_reference_df,
            self.yearly_results_reference_df,
            self.hourly_results_optimization_df,
            self.yearly_results_optimization_df,
        ) = self.read_hourly_results()

    def create_header(self) -> str:
        return (
            f"Scenario: {self.scenario.scenario_id}; \n "
            f"AC: {int(self.scenario.space_cooling_technology.power)} W; \n "
            f"Battery: {int(self.scenario.battery.capacity)} W; \n "
            f"Building id: {self.scenario.building.type}; \n "
            f"Boiler: {self.scenario.boiler.type}; \n "
            f"DHW Tank: {self.scenario.hot_water_tank.size} l; \n "
            f"PV: {self.scenario.pv.size} kWp; \n "
            f"Heating Tank: {self.scenario.space_heating_tank.size} l"
        )

    
    def read_hourly_results(
        self,
    ) -> (pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame):
        db = create_db_conn(self.scenario.config)
        # check if scenario id is in results, if yes, load them instead of calculating them:
        try:
            hourly_results_reference_df = read_parquet(
                file_name=f"OperationResult_RefHour_S{self.scenario.scenario_id}",
                folder=self.scenario.config.output,
            )
        except:
            print(f"No hourly reference results for scenario {self.scenario.scenario_id}")
            hourly_results_reference_df = pd.DataFrame()
        try:
            yearly_results_reference_df = db.read_dataframe(
                table_name="OperationResult_RefYear",
                filter={"ID_Scenario": self.scenario.scenario_id}
            )
        except:
            print(f"No yearly reference results for scenario {self.scenario.scenario_id}")
            yearly_results_reference_df = pd.DataFrame()
        try:
            hourly_results_optimization_df = read_parquet(
                file_name=f"OperationResult_OptHour_S{self.scenario.scenario_id}",
                folder=self.scenario.config.output,
            )
        except:
            print(f"No hourly optimization results for scenario {self.scenario.scenario_id}")
            hourly_results_optimization_df = pd.DataFrame()
        try:
            yearly_results_optimization_df = db.read_dataframe(
                table_name="OperationResult_OptYear",
                filter={"ID_Scenario": self.scenario.scenario_id},
            )
        except:
            print(f"No yearly optimization results for scenario {self.scenario.scenario_id}")
            yearly_results_optimization_df = pd.DataFrame()

        return (
            hourly_results_reference_df,
            yearly_results_reference_df,
            hourly_results_optimization_df,
            yearly_results_optimization_df,
        )

