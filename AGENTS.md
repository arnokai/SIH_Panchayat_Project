# Instructions for AI Agents & Pair Programmers

Welcome, AI Agent. This project uses the **Unified AI Root Memory System**.
All persistent memory, architectural decisions, task statuses, and session state are centralized in `~/ai-brain/contexts/SIH_Panchayat_Project` and accessible locally via the `.context` directory.

---

## 1. Mandatory Engagement Loop (Non-Negotiable)
Before executing changes or running modifying commands for any new task:
1. **Grill Me Interview First**: Ask one-by-one clarifying questions to resolve ambiguities and design decisions.
2. **Auto-Skill Suggestion & Stacking**: Identify relevant Master Suites in `~/ai-brain/skills/` and announce:  
   `💡 Skill Activated: [Suite Name] ➔ [Module Name]` (or stack multiple suites: `💡 Skills Activated: [Suite 1] + [Suite 2]`).
3. **Give a Report / Plan**: Formulate a complete implementation plan detailing proposed changes.
4. **Approval Gate**: Explicitly ask the user: *"Would you like me to execute this plan or make adjustments?"* and **WAIT** for explicit user approval before executing.
5. **Pre-Execution Transparency**: Always tell the user what command or edit you are about to do before doing it.

---

## 2. Rules Hierarchy ("Global is Main, Local can Override")
- **Baseline Global Standards**: Read [.global-rules.md](file://.global-rules.md) (or `~/ai-brain/global/RULES.md`).
- **Project Overrides**: Read [.context/memory/rules_override.md](file://.context/memory/rules_override.md). Any rule here **overrides** the global rules.

---

## 3. Reading Context at Session Start
Before proposing or making changes, always inspect:
1. [.context/memory/active_context.md](file://.context/memory/active_context.md): Current milestone, recent changes, and immediate next steps.
2. [.context/tasks/in_progress.md](file://.context/tasks/in_progress.md): What tasks are active right now.
3. [.context/memory/decisions.md](file://.context/memory/decisions.md): Architecture decisions and constraints.
4. **System Architecture Specs**: Review [.context/specs/architecture.md](file://.context/specs/architecture.md) for architecture rules, system flows, and data structures.
5. **Token-Saving Knowledge Graph (Graphify)**: If `graphify-out/graph.json` exists, always query the knowledge graph first with `graphify query "<question>"` (or `graphify path "<A>" "<B>"` / `graphify explain "<concept>"`) to inspect callers, callees, and dependencies instead of reading large source files and burning tokens.

---

## 4. Saving Context at Milestone or When User Requests
Whenever the user asks:
> *"Save all work and context"*, *"Save context"*, *"Update memory"*, or when wrapping up a feature:

You MUST update the following files in `.context/`:
- **[.context/memory/active_context.md](file://.context/memory/active_context.md)**: Summarize current status, what was completed, and next immediate steps.
- **[.context/memory/decisions.md](file://.context/memory/decisions.md)**: Log any new architectural or design decisions.
- **[.context/memory/learnings.md](file://.context/memory/learnings.md)**: Document any gotchas, bug solutions, or library workarounds discovered.
- **[.context/tasks/](file://.context/tasks/)**: Update in-progress and completed task lists.
- **`~/ai-brain/PROJECTS.md` & [.context/project_info.md](file://.context/project_info.md)**: Update the "Last Active" timestamp.
- **Knowledge Graph**: If code files were added or modified, run `graphify update .` to keep the AST graph synchronized without API costs.

---

## 5. Deletion Resilience
Even if the code in this directory is deleted or reset, all context and history in `~/ai-brain/contexts/SIH_Panchayat_Project` will be preserved permanently.
