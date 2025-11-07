# Cooling App – Developer Setup

This app consists of a FastAPI backend (data API) and a React (CRA) frontend for visualization. Follow the steps below to get both parts running locally after cloning the repository.

## Prerequisites

- Python 3.11 (or compatible)
- Node.js 20.x and Yarn 1.x (install globally or use the bundled binaries under `tools/node` / `.npm-global` if present)
- `pip` for Python dependency management

## 1. Clone the repo

```bash
git clone <repo-url>
cd Cooling
```

## 2. Python environment

```bash
python -m venv .venv
source .venv/bin/activate                  # Windows: .\.venv\Scripts\activate
pip install --upgrade pip
pip install -r APP/backend/requirements.txt
```

## 3. Node/Yarn setup

- If you already have Node 20+ and Yarn 1.x installed globally, skip to step 4.
- Otherwise, install or unpack Node/Yarn somewhere on your system and ensure both `node` and `yarn` are on your `PATH`.
- The repo contains a local toolchain (`tools/node`, `.npm-global/bin/yarn`) that you can use by prepending the following to your shell:

  ```bash
  export PATH="$PWD/tools/node/bin:$PWD/.npm-global/bin:$PATH"
  ```

## 4. Install frontend dependencies

```bash
cd APP/frontend
yarn install
cd ../..
```

## 5. Starting the app

### Option A – Single command (if the environment permits)

```bash
source .venv/bin/activate
python start_app.py
```

This attempts to:
1. Launch the FastAPI backend on port 8001 (`http://localhost:8001/api`).
2. Launch the CRA dev server on port 3000 (`http://localhost:3000`).

> **Note:** In restricted/sandboxed environments the script might not be allowed to spawn processes that bind to ports or write temporary files. If you see `PermissionError` (uvicorn) or `EACCES` (yarn), use option B instead.

### Option B – Manual startup

**Backend**
```bash
source .venv/bin/activate
uvicorn APP.backend.server:app --host 0.0.0.0 --port 8001 --reload
```

Verify it works:
```bash
curl http://localhost:8001/api/health
curl http://localhost:8001/api/projects
```

**Frontend**
```bash
export PATH="$PWD/tools/node/bin:$PWD/.npm-global/bin:$PATH"   # if using bundled node/yarn
cd APP/frontend
REACT_APP_API_BASE_URL=http://localhost:8001/api TMPDIR=$PWD/.tmp yarn start
```

Then open http://localhost:3000 in your browser. The dropdown should populate with projects from `/projects/<name>/output`.

## 6. Environment variables

- `REACT_APP_API_BASE_URL` – Frontend uses `http://<host>:8001/api` by default, so you only need to set this if your backend listens elsewhere.
- Backend currently requires no additional env vars (MongoDB was removed).

## 7. Data expectations

Place project folders under `projects/`, e.g.:
```
projects/
└── AUT_2020_cooling/
    ├── input/
    └── output/
        ├── AUT_2020_cooling.sqlite
        ├── OperationResult_RefHour_S1.parquet.gzip
        └── ...
```

Each project’s `output` directory must contain:
- SQLite file with `OperationResult_RefYear` data.
- One `OperationResult_RefHour_SX.parquet.gzip` per scenario (8760 rows).

## 8. Tests (optional)

### Backend
```bash
export TMPDIR=$PWD/tmp
source .venv/bin/activate
pytest APP/tests
```

### Frontend
Jest/RTL tests exist but require a writable temp directory. Run only if your environment allows it:
```bash
cd APP/frontend
TMPDIR=$PWD/.tmp CI=1 yarn test --watchAll=false
```

## Troubleshooting

- **“Loading projects…” forever:** backend not reachable or wrong `REACT_APP_API_BASE_URL`.
- **`EACCES` when running `yarn start`:** ensure `TMPDIR` points to a writable folder (e.g., `APP/frontend/.tmp`) and that folder exists with perms `chmod 777`.
- **`ModuleNotFoundError: APP`:** run commands from the repo root or set `PYTHONPATH` to the repo root.
