import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import pathlib
import os
import sys


# Add project root to sys.path to enable imports from utils
project_root = pathlib.Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.config import Config
from utils.db import create_db_conn

class CoolingVisualization:
    def __init__(self, config: Config):
        self.config = config
        self.yearly_data = self.load_yearly_data()  

    def load_yearly_data(self):
        # Load data from the database
        db = create_db_conn(self.config)
        return db.read_dataframe(table_name="OperationResult_RefYear")

    def load_hourly_results(self, scenario_id: int):
        # Load data from the database
        df = pd.read_parquet(self.config.output / f"OperationResult_RefHour_S{scenario_id}.parquet.gzip")
        return df

    def plot_results(self):
        # Plot results
        
        pass



if __name__ == "__main__":
    config = Config(project_name="AUT_2020_cooling", project_path=pathlib.Path("/home/users/pmascherbauer/projects4/workspace_philippm/Cooling/projects/AUT_2020_cooling/"))
    visualization = CoolingVisualization(config)
    visualization.plot_results()