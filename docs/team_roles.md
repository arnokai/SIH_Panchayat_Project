# Team Roles & Workspace Ownership — TerraMind (SIH26074)

This document establishes the dedicated folder ownership for the 4 team members to prevent merge conflicts and ensure parallel development.

---

## 1. Team Allocation

| Role | Member | Assigned Folder(s) | Dedicated Roadmap & Guide | Key Responsibilities |
| :--- | :--- | :--- | :--- | :--- |
| **Frontend Engineer** | Member 1 | `frontend/` | [frontend/README.md](../frontend/README.md) / [FRONTEND_TODO.md](../FRONTEND_TODO.md) | React UI, 5-day forecast cards, Leaflet comparison map, Bengali TTS audio, WhatsApp share button, offline PWA, 3,339 GP autocomplete |
| **Backend Engineer** | Member 2 | `backend/` & `rules/` | [backend/README.md](../backend/README.md) / [BACKEND_TODO.md](../BACKEND_TODO.md) | FastAPI REST endpoints (`/v1/forecast`, `/v1/statewide/*`), forecast engine, agricultural rules engine, `rules.yaml` advisory definitions, streak contexts |
| **AI / ML & Data Lake Engineer** | Member 3 | `ml/` & `data_pipeline/` | [ml/README.md](../ml/README.md) / [ML_TODO.md](../ML_TODO.md) | Two-Stage Hurdle downscaling model (`statewide_hurdle_v2.pkl`), pure Parquet data lake (22 districts, 2.44M rows), Copernicus DEM & SoilGrids enrichment, data contracts |
| **Project Manager & DevOps** | Member 4 | Root, `.github/`, `docs/`, `tests/` | [docs/DEVOPS_README.md](DEVOPS_README.md) / [DEVOPS_TODO.md](../DEVOPS_TODO.md) | Render cloud deployment, Vercel frontend, Docker container, CI branch guards, 157-test automated verification runner, SIH compliance |

---

## 2. Git Branching Workflow

1. Always branch from `main`:
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/<your-role>-<feature-name>
   ```
   * Frontend: `feature/frontend-statewide-search`
   * Backend: `feature/backend-statewide-endpoints`
   * AI/ML & Data Lake: `feature/ml-hurdle-v2-parquet`
   * DevOps: `feature/devops-157-tests-ci`

2. Do **not** edit files outside your assigned folder without coordinating with the assigned owner.
3. Open a Pull Request for Manager/DevOps review before merging into `main`.
