# 🩺 MPC-Plus

**Machine Performance Check Plus** — Professional Quality Assurance dashboard and reporting for **Varian TrueBeam** linear accelerators.

MPC-Plus is a unified, open-source monorepo designed to help medical physicists streamline the ingestion, analysis, and reporting of Machine Performance Check (MPC) data specifically from Varian TrueBeam systems. 

---

## 🏗 High-Level Architecture

MPC-Plus is composed of four primary layers, designed for modularity and scalability:

-   **Frontend**: A modern dashboard built with **Next.js 16 (App Router)** and **React 19**.
-   **Backend API**: A high-performance RESTful API built with **.NET 9** and **Dapper (PostgreSQL)**.
-   **ETL Watchdog**: An automated **Python** worker that monitors file shares (`iDrive`) and analyzes machine output images using `pylinac`.
-   **Database**: **PostgreSQL 16** with a medical-physics-optimized schema.

For a deeper dive, see [🏗 ARCHITECTURE.md](./docs/ARCHITECTURE.md).

---

## 🚀 Quick Start (Docker)

The recommended way to run MPC-Plus is with **Docker Compose**, which orchestrates all services and ensures environment consistency.

### Prerequisites
-   [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.

### 1. Configuration
Create a `.env` file in the project root based on the provided template:

```bash
cp .env.example .env
```
*(The defaults in `.env.example` are pre-configured for seamless Docker operation)*

### 2. Launch the Stack
From the project root, run:

```bash
docker-compose up -d --build
```

This will start:
-   **PostgreSQL 16** (Database) on port `5432`
-   **.NET 9 Backend** on `http://localhost:5132`
-   **Next.js Frontend** on `http://localhost:3000`
-   **Python ETL** background watchdog for `iDrive` scanning

### 3. Access
Open your browser and navigate to **[http://localhost:3000](http://localhost:3000)**.

For detailed Docker operations (logs, stopping, resets), refer to the [📦 DOCKER_GUIDE.md](./DOCKER_GUIDE.md).

---

## 🔑 Key Features

-   **Automated Ingestion**: Monitors for new MPC output files (CSV/XML) and processes them in real-time.
-   **Advanced Analysis**: Leverages `pylinac` for scientific analysis of `.xim` images (flatness, symmetry).
-   **Professional Reporting**: Generates physics-grade PDF reports via **QuestPDF**.
-   **Custom Thresholds**: Define passing/warning/failing limits per machine and energy variant.
-   **Medical-First UX**: Responsive, accessible interface using **Radix UI** and **Tailwind CSS**.

---

## 📦 Project Structure

```text
├── backend/            # .NET 9 API and Python ETL processes
│   ├── src/api/        # Main REST API project
│   └── src/data_manip/ # Python scripts for file monitoring and analysis
├── frontend/           # Next.js 16 Web Dashboard
├── backups/            # Database schema exports and seed data
├── docs/               # Detailed technical documentation
├── iDrive/             # Default mount for machine output files
└── docker-compose.yml  # Full stack orchestration
```

---

## 🤝 Contributing

We welcome contributions! MPC-Plus is a senior design project developed by Computer Science students at **Texas Christian University (TCU)** in collaboration with clinical partners.

---

## ⚖️ License

MPC-Plus is open-source software. Please refer to the LICENSE file for details.
