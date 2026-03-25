# 🏗 MPC-Plus Architecture

This document provides a technical overview of how MPC-Plus components interact to provide a seamless Quality Assurance (QA) workflow for **Varian TrueBeam** linear accelerators, specifically processing and visualizing **Machine Performance Check (MPC)** data.

## 🌉 System Overview

The system is composed of four primary layers, orchestrated via Docker Compose:

1.  **Frontend (Next.js 16/React 19)**: The user-facing dashboard for reviewing results, managing thresholds, and generating reports.
2.  **Backend API (.NET 9)**: The core business logic and data access layer, providing a RESTful interface to the database and PDF generation services.
3.  **ETL Watchdog (Python/pylinac)**: An automated background worker that monitors the `iDrive` (mounted storage) for new MPC machine outputs, processes them, and ingests them into the database.
4.  **Database (PostgreSQL 16)**: The persistent storage for all machine data, results, baselines, and application settings.

---

## 📁 Component Deep-Dive

### 1. Frontend Layer (`/frontend`)
- **Framework**: Next.js 16 (App Router) with React 19.
- **Styling**: Tailwind CSS 4.0 for utility-first responsive design.
- **UI Components**: Radix UI primitives for accessible, high-quality interaction patterns.
- **Data Fetching**: A custom `api-client.ts` layer that abstracts `fetch` calls and handles the impedance mismatch between PostgreSQL snake_case and Frontend camelCase.
- **State Management**: Uses React Context for application-wide settings (like Timezone and Theme).

### 2. Backend API Layer (`/backend/src/api`)
- **Framework**: ASP.NET Core (.NET 9).
- **Architecture**: **Repository Pattern** to decouple business logic from data access.
- **Data Access**: **Dapper** (Micro-ORM) for high-performance SQL execution. Uses custom **Type Handlers** to map PostgreSQL JSONB columns directly to C# DTOs.
- **Reporting**: **QuestPDF** for high-fidelity PDF report generation, allowing physicists to export monthly QA reviews.
- **Concurrency**: Fully asynchronous (async/await) pipeline for scalability.

### 3. ETL Watchdog Layer (`/backend/src/data_manipulation`)
- **Framework**: Python 3.13.
- **Core Engine**: `pylinac` for scientific analysis of `.xim` images (flatness, symmetry, field analysis).
- **Monitoring**: Uses a custom watchdog system that scans the `iDrive` mount for new `Results.csv` or `Results.xml` files.
- **Ingestion**: Handles complex data normalization, flood-field correction, and UTC timestamp conversion based on the facility's configured timezone.

### 4. Persistence Layer (`/backups`)
- **Engine**: PostgreSQL 16.
- **Storage Strategy**: Large datasets (like machine images) are stored on the filesystem (mounted via Docker volumes) while metadata and analysis results are stored in the relational database.
- **Schema**: Organized around `machines`, `beams`, `geo_checks`, `baselines`, and `thresholds`.

---

## 🛰 Communication Flow

1.  **Ingestion**: `iDrive` (File) → `ETL Watchdog` (Python) → `PostgreSQL` (DB) + `wwwroot/images` (Storage).
2.  **Display**: `Frontend` (Browser) → `Backend API` (.NET) → `PostgreSQL` (DB).
3.  **Reporting**: `Frontend` → `Backend API` → `QuestPDF` → `Frontend` (Download).

---

## 🛠 Engineering Best Practices

- **Monorepo Structure**: Frontend and Backend are co-located for easier synchronization of types and environment configurations.
- **Docker-First Development**: Every component is containerized to ensure "works on my machine" reliability.
- **Environment Parity**: Using `.env` files and Docker Compose ensures that development, staging, and production environments remain as close as possible.
- **Type Safety**: End-to-end type safety using TypeScript on the frontend and strong C# typing on the backend.
