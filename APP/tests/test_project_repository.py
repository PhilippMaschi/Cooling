import sqlite3
import sys
from pathlib import Path

import pandas as pd
import pytest

BASE_DIR = Path(__file__).resolve().parents[2]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from APP.backend.data_access import ProjectRepository, ScenarioMetric


@pytest.fixture(scope="module")
def projects_root() -> Path:
    return Path(__file__).resolve().parents[2] / "projects"


@pytest.fixture(scope="module")
def repository(projects_root: Path) -> ProjectRepository:
    return ProjectRepository(projects_root)


def test_list_projects_includes_expected_project(repository: ProjectRepository):
    projects = repository.list_projects()
    project_ids = {project.id for project in projects}
    assert "AUT_2020_cooling" in project_ids

    aut_project = next(project for project in projects if project.id == "AUT_2020_cooling")
    assert len(aut_project.scenarios) == 3
    assert aut_project.sqlite_path.name == "AUT_2020_cooling.sqlite"


def test_get_scenario_stats_matches_sqlite(repository: ProjectRepository, projects_root: Path):
    scenario_id = 1
    stats = repository.get_scenario_stats("AUT_2020_cooling", scenario_id)

    sqlite_path = projects_root / "AUT_2020_cooling" / "output" / "AUT_2020_cooling.sqlite"
    with sqlite3.connect(sqlite_path) as conn:
        df = pd.read_sql_query(
            "SELECT * FROM OperationResult_RefYear WHERE ID_Scenario = ?",
            conn,
            params=(scenario_id,),
        )
    assert not df.empty
    row = df.iloc[0]

    assert stats.total_cooling_load == pytest.approx(float(row["Q_RoomCooling"]))
    assert stats.total_energy_cost == pytest.approx(float(row["TotalCost"]))
    assert stats.total_electricity_demand == pytest.approx(float(row["Load"]))
    assert stats.peak_cooling_load == pytest.approx(float(row["PeakCoolingLoad"]))
    assert stats.peak_electric_load == pytest.approx(float(row["PeakElectricLoad"]))


def test_get_timeseries_returns_expected_length(repository: ProjectRepository):
    payload = repository.get_timeseries(
        "AUT_2020_cooling",
        scenario_id=1,
        metric=ScenarioMetric.COOLING_LOAD,
        aggregation="hourly",
    )
    assert payload.metric == ScenarioMetric.COOLING_LOAD.value
    assert len(payload.values) == 8760
    assert payload.values[0] is not None
