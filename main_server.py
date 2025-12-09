from utils.config import Config
from utils.db import init_project_db
from model.main import run_operation_model, run_operation_model_parallel
import shutil
from pathlib import Path


def delete_result_files(conf):
    # Iterate through each item in the directory
    for item in Path(conf.output).iterdir():
        # Check if the item is a file
        if item.is_file():
            # Check the file extension and delete if it's not .csv or .parquet
            if item.suffix in ['.gzip']:
                # print(f"Deleting: {item.name}")
                item.unlink()  # Delete the file


def delete_result_task_folders(conf):
    for item in Path(conf.output).iterdir():
        if item.is_dir():
            print(f"Deleting directory and all contents: {item}")
            for sub_item in item.iterdir():
                # Check if the sub_item is a file
                if sub_item.is_file():
                    sub_item.unlink()  # Delete the file
            shutil.rmtree(item)



if __name__ == "__main__":
    country_list = [
            "AUT",  
            # "BEL", 
            # "POL",
            # # "CYP", 
            # "PRT",
            # "DNK", 
            # "FRA", 
            # "CZE",  
            # "DEU", 
            # "HRV",
            # "HUN", 
            # "ITA",  
            # "LUX",
            # "NLD",
            # "SVK",
            # "SVN",
            # 'IRL', 
            # 'ESP',  
            # 'SWE',
            # 'GRC',
            # 'LVA',  
            # 'LTU',
            # 'MLT',
            # 'ROU',
            # 'BGR',  
            # 'FIN',
            # 'EST',
        ]

    years = [2020]#2030, 2040]
    for country in country_list:
        for year in years:
            cfg = Config(
                project_name=f"{country}_{year}_cooling", 
                project_path=Path(__file__).parent / "projects" / f"{country}_{year}_cooling"
            )
            init_project_db(cfg)
            run_operation_model(
                config=cfg,
                scenario_ids=[1,2,3,4,5,6,7,8,9,10],
                run_ref=True,
                run_opt=False,
                save_year=True,
                save_month=False,
                save_hour=True,
                hour_vars=None
            )
            pass
        


          
