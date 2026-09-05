# Team Roles & Workspace Ownership — TerraMind (SIH26074)

This document establishes the dedicated folder ownership for the 4 team members to prevent merge conflicts and ensure parallel development.

---

## 1. Team Allocation

| Role | Member | Assigned Folder(s) | Dedicated Roadmap & Guide | Key Responsibilities |
| :--- | :--- | :--- | :--- | :--- |
| **Frontend Engineer** | Member 1 | `frontend/` | [frontend/README.md](file:///home/arnokai/Projects/SIH_Panchayat_Project/frontend/README.md) / [FRONTEND_TODO.md](file:///home/arnokai/Projects/SIH_Panchayat_Project/FRONTEND_TODO.md) | React 18 UI, 5-day forecast cards, Leaflet comparison map, Bengali TTS audio, WhatsApp share button, offline PWA |
| **Backend Engineer** | Member 2 | `backend/` & `rules/` | [backend/README.md](file:///home/arnokai/Projects/SIH_Panchayat_Project/backend/README.md) / [BACKEND_TODO.md](file:///home/arnokai/Projects/SIH_Panchayat_Project/BACKEND_TODO.md) | FastAPI REST endpoints, forecast engine, agricultural rules engine, `rules.yaml` advisory definitions, streak contexts |
| **AI / ML & Data Engineer** | Member 3 | `ml/` & `data_pipeline/` | [ml/README.md](file:///home/arnokai/Projects/SIH_Panchayat_Project/ml/README.md) / [ML_TODO.md](file:///home/arnokai/Projects/SIH_Panchayat_Project/ML_TODO.md) | XGBoost/LightGBM downscaling pipelines, feature engineering (terrain/GIS), gridded datasets (IMERG/CHIRPS/ERA5), models |
| **Project Manager & DevOps** | Member 4 | Root, `.github/`, `docs/`, `tests/` | [docs/DEVOPS_README.md](file:///home/arnokai/Projects/SIH_Panchayat_Project/docs/DEVOPS_README.md) / [DEVOPS_TODO.md](file:///home/arnokai/Projects/SIH_Panchayat_Project/DEVOPS_TODO.md) | Render cloud deployment, Vercel frontend, Docker container, CI guards, Git branch policies, integration tests |

---

## 2. Git Branching Workflow

1. Always branch from `main`:
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/<your-role>-<feature-name>
   ```
   * Frontend: `feature/frontend-tts`
   * Backend: `feature/backend-new-rules`
   * AI/ML: `feature/ml-tweedie-loss`
   * DevOps: `feature/devops-ci`

2. Do **not** edit files outside your assigned folder without coordinating with the assigned owner.
3. Open a Pull Request for Manager/DevOps review before merging into `main`.
