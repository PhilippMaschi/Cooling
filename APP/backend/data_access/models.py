"""Domain models shared by the backend data access layer."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class ScenarioFileInfo(BaseModel):
    """Metadata about scenario artifacts stored on disk."""

    scenario_id: int
    hourly_parquet: Path


class ProjectInfo(BaseModel):
    """Represents a project folder produced by the FLEX operation model."""

    id: str
    name: str
    country: str
    year: int
    focus: str = "cooling"
    path: Path
    output_dir: Path
    sqlite_path: Optional[Path] = None
    scenarios: List[ScenarioFileInfo] = Field(default_factory=list)


class ScenarioStats(BaseModel):
    """Aggregated KPIs derived from the yearly SQLite table."""

    scenario_id: int
    total_cooling_load: Optional[float] = None
    avg_cooling_load: Optional[float] = None
    total_energy_cost: Optional[float] = None
    total_electricity_demand: Optional[float] = None
    peak_cooling_load: Optional[float] = None
    peak_electric_load: Optional[float] = None
    raw: Dict[str, Optional[float]] = Field(default_factory=dict)


class TimeSeriesData(BaseModel):
    """Timeseries payload ready for serialization to the frontend."""

    scenario_id: int
    metric: str
    aggregation: Literal["hourly", "daily", "monthly"]
    unit: Optional[str] = None
    timestamps: List[str] = Field(default_factory=list)
    values: List[float] = Field(default_factory=list)
