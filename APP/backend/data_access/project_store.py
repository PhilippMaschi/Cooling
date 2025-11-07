"""Utilities to discover project folders and load scenario artifacts."""

from __future__ import annotations

import logging
import os
import re
import sqlite3
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable, List, Literal, Optional, Tuple

import numpy as np
import pandas as pd

from .models import ProjectInfo, ScenarioFileInfo, ScenarioStats, TimeSeriesData

logger = logging.getLogger(__name__)

DATA_LAYER_DIR = Path(__file__).resolve().parent
BACKEND_DIR = DATA_LAYER_DIR.parent
APP_DIR = BACKEND_DIR.parent
REPO_ROOT = APP_DIR.parent


class ScenarioMetric(str, Enum):
    """Supported metric identifiers to keep parity with the frontend mock data."""

    COOLING_LOAD = "coolingLoad"
    HEATING_LOAD = "heatingLoad"
    ELECTRICITY_CONSUMPTION = "electricityConsumption"
    TEMPERATURE = "temperature"


METRIC_COLUMN_MAP: Dict[ScenarioMetric, Tuple[str, str]] = {
    ScenarioMetric.COOLING_LOAD: ("Q_RoomCooling", "kWh"),
    ScenarioMetric.HEATING_LOAD: ("Q_RoomHeating", "kWh"),
    ScenarioMetric.ELECTRICITY_CONSUMPTION: ("Load", "kWh"),
    ScenarioMetric.TEMPERATURE: ("T_outside", "°C"),
}

SCENARIO_STAT_COLUMNS: Dict[str, str] = {
    "total_cooling_load": "Q_RoomCooling",
    "total_energy_cost": "TotalCost",
    "total_electricity_demand": "Load",
    "peak_cooling_load": "PeakCoolingLoad",
    "peak_electric_load": "PeakElectricLoad",
}


class ProjectRepository:
    """High-level entry point to inspect project folders and load scenario data."""

    def __init__(self, projects_root: Optional[Path | str] = None) -> None:
        root = projects_root or os.environ.get("PROJECTS_ROOT") or (REPO_ROOT / "projects")
        self.projects_root = Path(root).expanduser().resolve()
        if not self.projects_root.exists():
            raise FileNotFoundError(f"Projects root does not exist: {self.projects_root}")
        self._project_cache: Dict[str, ProjectInfo] = {}

    # ------------------------------------------------------------------
    # Project discovery helpers
    # ------------------------------------------------------------------
    def list_projects(self) -> List[ProjectInfo]:
        """Return metadata for every project folder under the root."""
        projects = []
        for folder in sorted(self.projects_root.iterdir()):
            if not folder.is_dir():
                continue
            try:
                projects.append(self._get_or_build_project(folder))
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.warning("Skipping project %s: %s", folder.name, exc)
        return projects

    def get_project(self, project_id: str) -> ProjectInfo:
        """Return metadata for a single project by its folder name."""
        project_path = self.projects_root / project_id
        if not project_path.exists():
            raise FileNotFoundError(f"Project folder not found: {project_path}")
        return self._get_or_build_project(project_path)

    def _get_or_build_project(self, path: Path) -> ProjectInfo:
        project_id = path.name
        if project_id in self._project_cache:
            return self._project_cache[project_id]
        info = self._build_project_info(path)
        self._project_cache[project_id] = info
        return info

    def _build_project_info(self, path: Path) -> ProjectInfo:
        output_dir = path / "output"
        if not output_dir.exists():
            raise FileNotFoundError(f"Project output directory missing: {output_dir}")

        sqlite_path = self._find_sqlite_file(output_dir)
        scenarios = self._discover_scenario_files(output_dir)

        country, year, focus = self._parse_project_name(path.name)
        project_name = f"{country} {year} {focus.capitalize()}"

        return ProjectInfo(
            id=path.name,
            name=project_name,
            country=country,
            year=year,
            focus=focus,
            path=path,
            output_dir=output_dir,
            sqlite_path=sqlite_path,
            scenarios=scenarios,
        )

    @staticmethod
    def _parse_project_name(name: str) -> Tuple[str, int, str]:
        parts = name.split("_")
        if len(parts) < 3:
            raise ValueError(f"Unexpected project naming convention: {name}")
        country = parts[0]
        year = int(parts[1])
        focus = "_".join(parts[2:])
        return country, year, focus

    @staticmethod
    def _find_sqlite_file(output_dir: Path) -> Optional[Path]:
        for candidate in output_dir.glob("*.sqlite"):
            return candidate
        return None

    @staticmethod
    def _discover_scenario_files(output_dir: Path) -> List[ScenarioFileInfo]:
        pattern = re.compile(r"OperationResult_RefHour_S(\d+)\.parquet\.gzip$", re.IGNORECASE)
        scenarios = []
        for parquet_file in output_dir.glob("OperationResult_RefHour_S*.parquet.gzip"):
            match = pattern.search(parquet_file.name)
            if not match:
                continue
            scenarios.append(
                ScenarioFileInfo(
                    scenario_id=int(match.group(1)),
                    hourly_parquet=parquet_file.resolve(),
                )
            )
        return sorted(scenarios, key=lambda item: item.scenario_id)

    # ------------------------------------------------------------------
    # Aggregated statistics
    # ------------------------------------------------------------------
    def get_scenario_stats(self, project_id: str, scenario_id: int) -> ScenarioStats:
        """Load yearly KPIs for a scenario from the SQLite database."""
        project = self.get_project(project_id)
        if not project.sqlite_path:
            raise FileNotFoundError(f"No SQLite file found for project {project_id}")

        query = "SELECT * FROM OperationResult_RefYear WHERE ID_Scenario = ?"
        with sqlite3.connect(project.sqlite_path) as conn:
            df = pd.read_sql_query(query, conn, params=(scenario_id,))

        if df.empty:
            raise ValueError(f"Scenario {scenario_id} not found in {project.sqlite_path.name}")

        row = df.iloc[0]
        total_cooling = self._to_float(row.get(SCENARIO_STAT_COLUMNS["total_cooling_load"]))
        avg_cooling = (total_cooling / 8760) if total_cooling is not None else None
        total_cost = self._to_float(row.get(SCENARIO_STAT_COLUMNS["total_energy_cost"]))
        total_electric = self._to_float(row.get(SCENARIO_STAT_COLUMNS["total_electricity_demand"]))
        peak_cooling = self._to_float(row.get(SCENARIO_STAT_COLUMNS["peak_cooling_load"]))
        peak_electric = self._to_float(row.get(SCENARIO_STAT_COLUMNS["peak_electric_load"]))

        raw = {key: self._to_float(value) for key, value in row.items()}

        return ScenarioStats(
            scenario_id=scenario_id,
            total_cooling_load=total_cooling,
            avg_cooling_load=avg_cooling,
            total_energy_cost=total_cost,
            total_electricity_demand=total_electric,
            peak_cooling_load=peak_cooling,
            peak_electric_load=peak_electric,
            raw=raw,
        )

    # ------------------------------------------------------------------
    # Timeseries loading
    # ------------------------------------------------------------------
    def get_timeseries(
        self,
        project_id: str,
        scenario_id: int,
        metric: ScenarioMetric,
        aggregation: Literal["hourly", "daily", "monthly"] = "hourly",
    ) -> TimeSeriesData:
        """Return a metric's timeseries for a given scenario."""
        project = self.get_project(project_id)
        scenario_info = self._find_scenario_info(project.scenarios, scenario_id)
        if not scenario_info:
            raise FileNotFoundError(
                f"No parquet file for scenario {scenario_id} in {project.output_dir}"
            )

        column, unit = METRIC_COLUMN_MAP[metric]
        hourly_series = self._read_hourly_series(scenario_info.hourly_parquet, column)

        agg_series = self._aggregate_series(hourly_series, aggregation)
        timestamps = [ts.isoformat() for ts in agg_series.index.to_pydatetime()]
        values = [self._to_float(val, allow_none=False) for val in agg_series.values]

        return TimeSeriesData(
            scenario_id=scenario_id,
            metric=metric.value,
            aggregation=aggregation,
            unit=unit,
            timestamps=timestamps,
            values=values,
        )

    @staticmethod
    def _find_scenario_info(
        scenarios: Iterable[ScenarioFileInfo], scenario_id: int
    ) -> Optional[ScenarioFileInfo]:
        for scenario in scenarios:
            if scenario.scenario_id == scenario_id:
                return scenario
        return None

    @staticmethod
    def _aggregate_series(
        series: pd.Series, aggregation: Literal["hourly", "daily", "monthly"]
    ) -> pd.Series:
        if aggregation == "hourly":
            return series
        if aggregation == "daily":
            return series.resample("D").mean()
        if aggregation == "monthly":
            return series.resample("M").mean()
        raise ValueError(f"Unsupported aggregation: {aggregation}")

    @staticmethod
    @lru_cache(maxsize=16)
    def _read_hourly_series(parquet_path: Path, column: str) -> pd.Series:
        df = pd.read_parquet(parquet_path, columns=[column], engine="pyarrow")
        index = pd.date_range("2000-01-01", periods=len(df), freq="h")
        return pd.Series(df[column].astype(float).to_numpy(), index=index, dtype=np.float64)

    @staticmethod
    def _to_float(value, allow_none: bool = True) -> Optional[float]:
        if value is None:
            return None if allow_none else 0.0
        if isinstance(value, (np.generic,)):
            return float(value.item())
        if isinstance(value, (int, float)):
            return float(value)
        try:
            return float(value)
        except (TypeError, ValueError):
            if allow_none:
                return None
            raise
