from __future__ import annotations

import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import List, Literal

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware

from .data_access import ProjectRepository, ScenarioMetric

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

app = FastAPI()
api_router = APIRouter(prefix="/api")


# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------
@lru_cache
def get_project_repository() -> ProjectRepository:
    return ProjectRepository()


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------
class ProjectSummaryResponse(BaseModel):
    id: str
    name: str
    country: str
    year: int
    focus: str
    scenario_count: int
    scenario_ids: List[int]


class ScenarioStatsResponse(BaseModel):
    scenario_id: int
    total_cooling_load: float | None = None
    avg_cooling_load: float | None = None
    total_energy_cost: float | None = None
    total_electricity_demand: float | None = None
    peak_cooling_load: float | None = None
    peak_electric_load: float | None = None


class ProjectScenariosResponse(BaseModel):
    project_id: str
    scenarios: List[ScenarioStatsResponse]


class TimeSeriesResponse(BaseModel):
    scenario_id: int
    metric: str
    aggregation: Literal["hourly", "daily", "monthly"]
    unit: str | None = None
    timestamps: List[str]
    values: List[float]


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@api_router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
async def root_redirect() -> RedirectResponse:
    """Send root traffic to the projects endpoint for convenience."""
    return RedirectResponse(url="/api/projects")


@api_router.get("/projects", response_model=List[ProjectSummaryResponse])
async def list_projects(repo: ProjectRepository = Depends(get_project_repository)):
    projects = repo.list_projects()
    summaries = [
        ProjectSummaryResponse(
            id=project.id,
            name=project.name,
            country=project.country,
            year=project.year,
            focus=project.focus,
            scenario_count=len(project.scenarios),
            scenario_ids=[scenario.scenario_id for scenario in project.scenarios],
        )
        for project in projects
    ]
    return summaries


@api_router.get(
    "/projects/{project_id}/scenarios",
    response_model=ProjectScenariosResponse,
)
async def list_project_scenarios(
    project_id: str,
    repo: ProjectRepository = Depends(get_project_repository),
):
    try:
        project = repo.get_project(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    scenarios: List[ScenarioStatsResponse] = []
    for scenario in project.scenarios:
        stats = repo.get_scenario_stats(project.id, scenario.scenario_id)
        scenarios.append(
            ScenarioStatsResponse(
                scenario_id=scenario.scenario_id,
                total_cooling_load=stats.total_cooling_load,
                avg_cooling_load=stats.avg_cooling_load,
                total_energy_cost=stats.total_energy_cost,
                total_electricity_demand=stats.total_electricity_demand,
                peak_cooling_load=stats.peak_cooling_load,
                peak_electric_load=stats.peak_electric_load,
            )
        )

    return ProjectScenariosResponse(project_id=project.id, scenarios=scenarios)


@api_router.get(
    "/projects/{project_id}/scenarios/{scenario_id}/timeseries",
    response_model=TimeSeriesResponse,
)
async def get_scenario_timeseries(
    project_id: str,
    scenario_id: int,
    metric: ScenarioMetric = Query(default=ScenarioMetric.COOLING_LOAD),
    aggregation: Literal["hourly", "daily", "monthly"] = Query(default="hourly"),
    repo: ProjectRepository = Depends(get_project_repository),
):
    try:
        payload = repo.get_timeseries(project_id, scenario_id, metric, aggregation)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return TimeSeriesResponse(
        scenario_id=scenario_id,
        metric=payload.metric,
        aggregation=payload.aggregation,
        unit=payload.unit,
        timestamps=payload.timestamps,
        values=payload.values,
    )


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
