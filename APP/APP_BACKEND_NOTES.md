# Cooling App – Backend Analysis & Working Notes

_Last updated: 2025-11-07T10:43:09+01:00_

## Purpose of this document
- Capture the current state of the Cooling visualization app (front-end + back-end).
- Record where critical model output data lives and what formats we must support (SQLite + Parquet).
- Outline blockers/missing backend pieces so future work can focus on shipping a real API that the React UI can consume.

## Latest progress (2025-11-07)
- Created `APP/backend/data_access/` package with `ProjectRepository` + `ScenarioMetric` enum to explore project folders and expose reusable readers.
- Repository auto-discovers projects under `PROJECTS_ROOT` (defaults to `<repo>/projects`), parses scenario parquet assets, and provides helper methods:
  - `list_projects()` → `ProjectInfo` objects describing root paths, sqlite file, and available scenario files.
  - `get_scenario_stats(project_id, scenario_id)` → wraps `OperationResult_RefYear` rows into `ScenarioStats` (includes aggregate/avg cooling load, total energy cost, raw data snapshot).
  - `get_timeseries(..., metric, aggregation)` → reads `OperationResult_RefHour_S*.parquet.gzip`, maps metrics (`coolingLoad`, `heatingLoad`, `electricityConsumption`, `temperature`) to columns, and returns structured timestamps/values with hourly/daily/monthly aggregation via pandas resampling.
- Added lightweight domain models in `data_access/models.py` (Pydantic) to keep type parity with eventual FastAPI responses.
- Installed `pydantic>=2.6.4` inside `.venv` to support the new data layer (matches backend requirements file).
- FastAPI app now exposes `/api/health`, `/api/projects`, `/api/projects/{id}/scenarios`, and `/api/projects/{id}/scenarios/{scenario_id}/timeseries`, all powered by the shared `ProjectRepository`. Responses currently surface totals from SQLite; peak fields default to `null` until the DB includes them.
- SQLite export now contains `PeakCoolingLoad` + `PeakElectricLoad`. `ScenarioStats` (and therefore `/scenarios` responses) read those values directly without recomputing from parquet.
- Added repository-focused pytest coverage in `APP/tests/test_project_repository.py` (listing projects, validating stats vs. SQLite, and checking timeseries payloads). Run locally with `export TMPDIR=$PWD/tmp` and `PYTEST_ADDOPTS='--maxfail=1 -s -p no:cacheprovider' pytest APP/tests/test_project_repository.py` to avoid sandbox temp/cache issues.
- Added FastAPI integration checks in `APP/tests/test_api.py`. They mount the real app via `TestClient`, hit `/api/projects`, `/projects/{id}/scenarios`, and `/projects/{id}/scenarios/{sid}/timeseries`, and assert the responses contain totals + peaks. Always pass `timeout=10` (enforced in the tests) and run via `export TMPDIR=$PWD/tmp; PYTEST_ADDOPTS='--maxfail=1 -s -p no:cacheprovider' pytest APP/tests/test_api.py`.
- Frontend dashboard now calls the real backend: `src/lib/api.js` centralizes axios calls (defaulting to `REACT_APP_API_BASE_URL` or `http://localhost:8000/api`), `Dashboard.jsx` loads projects/scenario stats, and `DetailedChart`/`AggregatedChart` fetch live timeseries per metric. `StatsOverview` + `ScenarioSelector` display the actual totals/peaks returned by `/api/projects/{id}/scenarios`. The old `mock.js` file remains for reference but is no longer imported.
- `src/lib/api.js` now falls back to `http://<current-host>:8001/api` when no env var is provided, ensuring the CRA app talks to the default backend port even if `.env` is missing/mis-typed.
- Created `APP/frontend/.env.example` documenting `REACT_APP_API_BASE_URL`. The CRA dev server must consume this value (or default to `http://localhost:8000/api`) when pointing the UI at remote deployments.
- Installed a local Node.js toolchain under `tools/node` (v20.11.1) plus a project-scoped Yarn (`.npm-global/bin/yarn`). Always prefix commands with `export PATH="/path/to/tools/node/bin:/path/to/.npm-global/bin:$PATH"` to pick them up.
- Added React Testing Library + jest-dom/user-event dependencies and a representative integration test (`src/pages/__tests__/Dashboard.integration.test.jsx`) exercising the mocked API flow. `src/setupTests.js` now wires jest-dom + fetch polyfill.
- Frontend automated-test run is currently blocked: `yarn test`/Jest attempts to create temp folders under the repo (or `/tmp`) but the workspace denies non-elevated writes, yielding `EACCES: permission denied, mkdir ...`. Once a writable temp directory is available (or the sandbox relaxes permissions), rerun `TMPDIR=<writable-path> CI=1 yarn test --watchAll=false`.
- Known issue: the CRA dev server launched from `start_app.py` currently ignores the injected `REACT_APP_API_BASE_URL`, so if you need a different backend port you still must set `.env` or prefix the command manually. The default fallback now targets `http://<host>:8001/api`, so the UI works with the bundled backend even when env vars are missing, but custom deployments still require manual configuration.
- Added `start_app.py` at the repo root to launch both servers. After activating `.venv`, run `python start_app.py` and it will:
  - start the FastAPI backend (`uvicorn APP.backend.server:app`) with `--reload` on port 8001 by default
  - start the CRA dev server via Yarn on port 3000 (unless `--no-frontend` is passed) with `REACT_APP_API_BASE_URL` pointing to the backend (`http://localhost:<backend-port>/api` even when the backend binds to `0.0.0.0`)
  - set `PYTHONPATH` for both processes so `APP.backend` imports work even when uvicorn spawns reload subprocesses
  - cleanly terminate both processes on Ctrl+C
  Make sure your shell exports the local Node/Yarn paths (see above) before invoking the script.

### Clarifications (2025-11-07 11:12 CET)
- Each project may ship thousands of scenario parquet files (one file per scenario, each 8760 rows with the same columns). Sample project now includes three scenarios, and the SQLite yearly table has three rows.
- Backend remains read-only; no write/trigger endpoints are required.
- MongoDB is out of scope for this app and can be removed from the backend stack.
- Parquet size is fixed per file, but statistical preprocessing might be required to aggregate peak-demand statistics efficiently across many scenarios.
- User base is tiny (≈2) and has unrestricted access to all projects; no per-project ACL is needed.
- Visualization focus: highlight cooling load and electricity demand totals plus their peaks. CO₂ is not available; the previous placeholder based on `Fuel` can be dropped. KPI values should come straight from SQLite rather than being recomputed in the API layer; upstream ETL will populate yearly totals and peaks.
- Only one project is visualized at a time; restarting or reconfiguring the backend between projects is acceptable, so caching can stay simple for now.

## Snapshot of available assets
### Model output data (source of truth)
- Directory structure: `projects/<COUNTRY_YEAR>_{cooling}/output/`. Sample project (`projects/AUT_2020_cooling/output`) currently exposes three scenarios (`OperationResult_RefHour_S{1,2,3}.parquet.gzip`) plus the combined SQLite database.
- Files present:
  - `AUT_2020_cooling.sqlite` — relational store with scenario + configuration metadata and yearly aggregates.
    - Tables discovered via `sqlite_master`: `OperationScenario`, multiple `OperationScenario_Component_*` tables, `OperationScenario_BehaviorProfile`, `OperationScenario_EnergyPrice`, `OperationScenario_RegionWeather`, and `OperationResult_RefYear`.
    - `OperationResult_RefYear` columns include fields such as `ID_Scenario`, `TotalCost`, `Q_RoomCooling`, `E_RoomCooling`, `Grid`, etc.; latest run has three rows (one per scenario).
  - `OperationResult_RefHour_S*.parquet.gzip` — one file per scenario, each containing the full 8760-row hourly time series with a consistent schema. `pandas`/`pyarrow` inside `.venv` now handles these loads.
  - `figure/` — contains generated images (not yet inspected).
- Implication: the backend must be able to read SQLite for metadata/aggregates and Parquet (compressed) for time-series per scenario.

### Back-end code (`APP/backend`)
- `server.py` now wires the `ProjectRepository` into FastAPI and exposes project/scenario/timeseries endpoints plus `/api/health`. Status-check + Mongo plumbing has been removed, but we still need to document the new `.env` expectations (currently only `CORS_ORIGINS` and optional `PROJECTS_ROOT`).
- No authentication/authorization layer is implemented (intentionally, per requirements).
- `requirements.txt` still lists security/auth tooling (bcrypt, python-jose) even though they are unused; we can prune them later.

### Front-end code (`APP/frontend`)
- CRA + CRACO + Tailwind/shadcn UI stack. Routing limited to `/` rendering `pages/Dashboard.jsx`.
- All data flows come from `src/mock.js` (mock projects, scenarios, stats, and random time-series) with artificial delay via `mockDelay`.
- Components expecting backend data:
  - `ScenarioSelector`, `StatsOverview`, `DetailedChart`, `AggregatedChart` all consume mock structures and never call an API.
- Conclusion: once a backend API exists, the Dashboard needs hooks/services (e.g., via `axios`) to replace the mock module.

### Tests
- `APP/tests/__init__.py` only; no API or integration tests yet.

## Missing pieces / blockers
1. **Data access layer**: No service reads SQLite/Parquet outputs or abstracts projects/scenarios/time-series into domain models.
2. **API surface**: No REST (or GraphQL) contract to list projects, fetch scenario metadata, pull aggregates, or stream hourly data. Current Mongo-backed status endpoints are unrelated to requirements.
3. **Configuration**: Need a reliable way to point the backend to a `projects/` root, likely via env var (e.g., `PROJECTS_ROOT`). `.env` template should be committed with documentation.
4. **Serialization/performance**: Need pagination/chunking/compression strategy for 8760-point series per scenario; consider pre-aggregations (hour/daily/monthly) or server-side down-sampling.
5. **Validation & typing**: No Pydantic models for domain entities (Project, Scenario, AggregatedStats, TimeSeriesPoint) yet.
6. **Security/observability**: No auth, logging only basic `logging.basicConfig`, no structured logs, no rate limiting.
7. **Testing/tooling**: pytest dependency present but no tests; need unit tests for data readers and API routes.
8. **Peak demand stats**: Need reusable helpers to compute peak cooling/electric loads (and possibly other percentiles) from parquet data so aggregated charts can visualize distributions.
9. **Scalability prep**: With thousands of parquet files per project, we should consider precomputing summaries (peaks, totals) instead of reading every file on-demand—at least for scenario listing endpoints.

## Recommended backend roadmap
### Phase 0 – Recon / setup
- Install `pandas`, `pyarrow`, `sqlalchemy` (or `sqlite3` stdlib) to read Parquet + SQLite efficiently. ✅ `.venv` now includes pandas + pyarrow.
- Add `.env.example` documenting `PROJECTS_ROOT`, `MONGO_URL` (if still needed), `DB_NAME`, `CORS_ORIGINS`.
- Decide whether MongoDB is required; ✅ confirmed we can drop it.

### Phase 1 – Data services
- Implement a `projects` module that scans `projects/` for folders matching pattern `<country>_<year>_cooling` and inspects `output/` contents.
- Build readers:
  - SQLite reader returning scenario metadata + aggregated KPIs (`OperationResult_RefYear`, component configs) mapped onto Pydantic models.
  - Parquet reader returning hourly time-series arrays keyed by scenario and metric; consider caching to avoid re-reading large files.
- Provide simple repository/cache layer so endpoints can reuse loaded data (e.g., LRU keyed by project/scenario).
- Extend stats helpers with peak cooling/electric loads + other summary figures needed for the UI.

### Phase 2 – API contract (FastAPI)
Proposed endpoints (all under `/api`):
- `GET /projects` → list `{id, name, country, year, available_scenarios}` derived from folder names + DB metadata.
- `GET /projects/{project_id}/scenarios` → list scenarios with descriptions/config summary.
- `GET /projects/{project_id}/scenarios/{scenario_id}/stats` → aggregated KPIs (total/avg loads, cost, CO₂) mirroring `mockAggregatedStats` shape for drop-in UI swap.
- `GET /projects/{project_id}/scenarios/{scenario_id}/timeseries?metric=coolingLoad&aggregation=hourly` → deliver 8760 data points (optionally aggregated server-side to daily/monthly when requested).
- `GET /health` → simple heartbeat (useful for deployment without Mongo).

### Phase 3 – Front-end integration
- Replace `mock.js` usage with hooks calling the new endpoints (e.g., `useQuery` via React Query or custom `useEffect` + `axios`).
- Preserve component props so minimal UI rewrites needed; ensure responses match expected shapes (arrays of `{id, name}` etc.).
- Add loading/error states leveraging existing spinners and badges.

### Phase 4 – Testing & hardening
- Unit tests for data readers (using fixtures from `projects/AUT_2020_cooling`).
- API tests via `httpx.AsyncClient` & `pytest` to ensure endpoints serialize correctly.
- Consider snapshot tests for typical responses; add CI job when backend matures.

## Critical references & breadcrumbs
- Project runner: `main_server.py` shows how configs are built (`Config` from `utils.config`, `init_project_db`, `run_operation_model`). This informs how new project folders are named and populated.
- Model codebase: `model/` folder contains domain logic; refer to `model/constants.py`, `model/model_base.py` (already open in IDE) for parameter names if you need to map SQLite columns to friendly labels.
- Front-end components expecting data: `APP/frontend/src/pages/Dashboard.jsx`, `../components/{ScenarioSelector,StatsOverview,DetailedChart,AggregatedChart}`.
- Mock data contract to emulate: `APP/frontend/src/mock.js`.

- [Resolved] Each scenario has its own parquet file and there can be thousands per project (fixed schema, 8760 rows).
- [Resolved] Backend is read-only; no model-run triggers necessary.
- [Resolved] MongoDB is out of scope; dependencies/routes can be removed.
- [Resolved] Only a handful of trusted users exist; no per-project ACL or auth required right now.
- [Resolved] KPI set focuses on total cooling/electric demand, their yearly peaks, and total cost; values will be delivered via SQLite once ETL populates them.
- [Resolved] No extra aggregations (percentiles/monthly) are required for now.
- [Resolved] Ensure the SQLite export eventually contains the peak/totals columns the API expects (`PeakCoolingLoad`, `PeakElectricLoad`, etc.) so the backend can remain a simple pass-through.
- Outstanding: Evaluate whether caching beyond the `_read_hourly_series` LRU is necessary once multi-project support or larger datasets arrive (probably not until the UI can switch projects live).

## Next recommended investigation steps
1. Wire `ProjectRepository` into FastAPI and expose `/api/projects` + `/api/projects/{id}/scenarios` so the frontend can start consuming real data. ✅ (implemented; remember to respect the 10 s timeout guard when testing manually).
2. Keep `ScenarioStats` aligned with the SQLite schema (totals + peak columns) so the API remains a pass-through layer. ✅ — now reading `PeakCoolingLoad`/`PeakElectricLoad` directly.
3. Add automated tests for `ProjectRepository` using `projects/AUT_2020_cooling` as fixture data to guard against regressions in parquet/sqlite parsing. ✅ (`APP/tests/test_project_repository.py`).
4. ✅ FastAPI integration tests now exist (`APP/tests/test_api.py`). Keep using `timeout<=10s` in any future `TestClient` code.
5. Frontend now consumes the API; automated UI tests (React Testing Library) are scaffolded but can’t run until we get a writable temp directory for Jest/Yarn. Follow up with the workspace owner to grant write permissions (or provide an approved tmp path), then re-run `TMPDIR=<tmp> CI=1 yarn test --watchAll=false`.

Keep this file updated as you answer the outstanding questions or add new backend capabilities.
- Created `APP/README.md` documenting full setup: Python venv, local Node/Yarn usage, manual vs. scripted startup, environment variables, and troubleshooting tips.
