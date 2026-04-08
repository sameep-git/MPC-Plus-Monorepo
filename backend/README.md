# 🧱 MPC-Plus Backend Services

The backend for **MPC-Plus** is split into two primary components: the **.NET 9 REST API** and the **Python ETL Watchdog**. This project is an open-source initiative by **TCU Computer Science** students in collaboration with clinical partners.

## 🏗 Architectural Overview

-   **API Layer (`src/api`)**: Built with **.NET 9**, this serves as the central business logic layer. It uses the **Repository Pattern** and **Dapper** (Micro-ORM) for high-performance communication with PostgreSQL.
-   **Data Ingestion (`src/data_manipulation`)**: A Python-based watchdog that uses `pylinac` to automatically analyze Machine Performance Check (MPC) data from Varian TrueBeam linear accelerators.

For detailed documentation on the ETL Watchdog, see [src/data_manipulation/README.md](src/data_manipulation/README.md).

## 🚀 API Key Features

*   **Machine Management**: Track linear accelerators (linacs), their locations, and configurations.
*   **Performance Analysis**: Determine Pass/Fail status based on dynamically configurable thresholds.
*   **Report Generation**: Generate professional, high-fidelity PDF reports of machine performance using **QuestPDF**.
*   **Threshold Configuration**: Granular threshold management for various beam parameters (Uniformity, Output, Center Shift).
*   **DocFactors**: Manage Dose Output Correction factors.

## 🛠️ API Technology Stack

*   **Framework**: [.NET 9](https://dotnet.microsoft.com/en-us/download/dotnet/9.0) (ASP.NET Core Web API)
*   **Database Integration**: [Npgsql](https://www.npgsql.org/) / Dapper
*   **JSON Handling**: Custom Type Handlers to map PostgreSQL JSONB columns to C# DTOs.
*   **PDF Generation**: [QuestPDF](https://www.questpdf.com/)
*   **Documentation**: Swashbuckle / OpenAPI

## 📄 Database Schema

For detailed database schema documentation, see [DATABASE_SCHEMA.md](../guides/DATABASE_SCHEMA.md) or refer to the exported backups in the root `/backups` directory.

## 📦 Getting Started (Local Development)

We recommend using **Docker Compose** from the project root to run the entire stack. However, to run the API independently:

### Prerequisites

*   [.NET 9 SDK](https://dotnet.microsoft.com/en-us/download/dotnet/9.0)
*   A running PostgreSQL 16+ instance

### Configuration

Ensure you have a `.env` file in the project root configured with your database credentials (see `.env.example`).

### Running Locally

```bash
cd src/api
dotnet restore
dotnet run
```

The API will be available at `http://localhost:5132`.
Swagger UI is available at `http://localhost:5132/swagger`.

## 👥 Contributors

**Backend Team:**
*   **Brae Ogle**
*   **Alex Lee**
*   **Madhavam Shahi**
*   **Tristan Gonzales**

**Full Stack / Integration:**
*   **Sameep Shah**
*   **Alex Morales**

## 📄 License

This project is open-source software. Please refer to the LICENSE file in the project root for details.
