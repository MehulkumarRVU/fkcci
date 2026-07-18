# PocketCoach AI Upgrade Plan

## Purpose
This plan organizes the next phases to evolve the existing PocketCoach AI codebase into a production-ready, enterprise-grade platform while preserving all current functionality.

## Phase 1: Audit and Modular Foundation
1. Maintain existing functionality for Table Tennis and Boxing.
2. Introduce a modular AI engine under `backend/app/pose_engine/`:
   - `base_analyzer.py`
   - `sports/table_tennis_analyzer.py`
   - `sports/boxing_analyzer.py`
   - `shared/utils.py`
   - `analyzer_factory.py`
3. Keep current backend routes unchanged while redirecting analysis logic to the new analyzer factory.
4. Validate imports and runtime behavior.

## Phase 2: Clean Architecture & Domain Modeling
1. Refactor backend layers into clear modules:
   - `database`
   - `models`
   - `repositories`
   - `services`
   - `routes`
   - `pose_engine`
2. Add repository pattern abstractions for `Athlete`, `Session`, and `Skill`.
3. Add domain service wrappers around authentication and analysis.
4. Expand database schema incrementally with migrations if needed.

## Phase 3: Cloud-Ready Backend Improvements
1. Replace SQLite with support for PostgreSQL via environment configuration.
2. Add Redis support for caching and rate limiting.
3. Add configuration management using environment variables and a `.env` loader.
4. Harden security: refresh tokens, RBAC, rate limiting, CORS restrictions, audit logging.
5. Add tooling for production deployment: Dockerfile, docker-compose, Nginx reverse proxy.

## Phase 4: Frontend Modernization and UX Upgrade
1. Retain existing page structure while refining UI toward premium blue-themed styling.
2. Introduce design system and reusable components in CSS.
3. Implement responsive layout, dark/light theme, improved dashboard, session, and profile UX.
4. Enhance AI camera experience with overlay, score cards, and smoother feedback.

## Phase 5: Modular Sports Platform
1. Define an extensible sports registry and metadata model.
2. Build placeholder modules for future sport types.
3. Keep existing Table Tennis and Boxing fully implemented.
4. Ensure new sport modules can be enabled via configuration.

## Phase 6: Product & Enterprise Features
1. Add coach and enterprise dashboards with richer analytics.
2. Add challenge, achievement, and community support in the data model.
3. Add organization and membership entities.
4. Add audit, messaging, notifications, and reporting.

## Phase 7: Documentation and Delivery
1. Update the README with architecture, setup, and deployment guides.
2. Add developer documentation, ER diagrams, and API docs.
3. Add verification scripts and health checks.
4. Create CI workflows for test and deployment automation.

## Notes
- All changes must preserve backward compatibility.
- Existing live functionality must be tested after every phase.
- Refactor only when necessary; extend modules wherever possible.
- Keep the current feature set working while building the platform foundation.
