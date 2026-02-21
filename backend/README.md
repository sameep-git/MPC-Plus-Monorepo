# MPC Plus - Backend API

The backend API for **MPC Plus**, a comprehensive Machine Performance Check system for radiation therapy quality assurance. This project is an open-source initiative by **TCU Computer Science** students in collaboration with **The Center for Cancer and Blood Disorders**.

## Overview

This API serves as the central logic layer for the MPC Plus platform, handling data persistence, business logic, and report generation. It acts as a bridge between the frontend application and the database (accessed via PostgREST or Supabase).

## 🚀 Key Features

*   **Machine Management**: Track linear accelerators (linacs), their locations, and configurations.
*   **Performance Analysis**: Process and analyze beam data, including determining Pass/Fail status based on configurable thresholds.
*   **Report Generation**: Generate detailed PDF reports of machine performance using **QuestPDF**.
*   **Threshold Configuration**: Dynamic threshold management for various beam parameters (Uniformity, Output, Center Shift).
*   **DocFactors**: Manage Dose Output Correction factors.

## 🛠️ Technology Stack

*   **Framework**: [.NET 9](https://dotnet.microsoft.com/en-us/download/dotnet/9.0) (ASP.NET Core Web API)
*   **Database Integration**: [Supabase C# SDK](https://github.com/supabase-community/supabase-csharp) / PostgREST
*   **PDF Generation**: [QuestPDF](https://www.questpdf.com/)
*   **Documentation**: Swagger / OpenAPI

## 📄 Database Schema

For detailed database schema documentation, see [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md).

## 📦 Getting Started

For full local deployment instructions (including database setup), please refer to the [DEPLOYMENT.md](../../DEPLOYMENT.md) guide in the root directory.

### Prerequisites

*   [.NET 9 SDK](https://dotnet.microsoft.com/en-us/download/dotnet/9.0)
*   A running Postgres + PostgREST instance (or Supabase project)

### Configuration

Copy `.env.local.example` to `.env` and configure your database connection:

```bash
cp .env.local.example .env
```

### Running Locally

```bash
cd src/api
dotnet restore
dotnet run
```

The API will be available at `http://localhost:5000` (by default).
Swagger UI is available at `http://localhost:5000/swagger`.

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

This project is open source.
