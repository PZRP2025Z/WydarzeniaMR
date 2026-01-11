# Project Setup

## Quick Start

```bash
docker compose up -d --build
```

Access at http://localhost:5173

```bash
# Stop services
docker compose down
```

---

## Development

### First Time Setup
```bash
cp .env.example .env.docker
# Edit .env.docker with your config

# Only needed for running tests locally
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -e ".[test,dev]"
```

### Daily Workflow
```bash
# Run tests and build
python build.py

# Or manually:
source venv/bin/activate
python -m pytest
docker compose up -d --build

# View logs
docker compose logs -f

# Stop services
docker compose down
```

### URLs
- Frontend: http://localhost:5173
- Backend: http://localhost:8000