# 🧱 MPC-Plus Backend API

A high-performance RESTful API built with **.NET 9** that serves as the core business logic layer for MPC-Plus.

---

## 🏗 Architectural Patterns

This project follows several key architectural patterns to ensure maintainability and high performance:

### 1. Repository Pattern
We use the **Repository Pattern** to decouple our API controllers from the direct data access logic. This allows for cleaner code and easier unit testing. All repositories are defined by interfaces in the `Repositories/Abstractions` directory.

### 2. Micro-ORM: Dapper
Instead of a heavy ORM like Entity Framework Core, we use **Dapper**. This provides maximum performance and complete control over our SQL queries. 

### 3. Custom Type Mapping
To handle PostgreSQL's powerful **JSONB** column types, we've implemented custom **Type Handlers** (see `Database/TypeHandlers`). These automatically serialize and deserialize complex C# objects (like Dictionaries and Lists) to and from JSON in the database.

---

## 🔬 Key Components

-   **Controllers**: REST endpoints for managing machines, beams, thresholds, and reports.
-   **Services**: Complex business logic, such as the `ReportService` which leverages **QuestPDF** to generate professional medical reports.
-   **Extensions**: A modular approach to dependency injection (see `ServiceCollectionExtensions.cs`).
-   **Models**: Strongly-typed C# classes representing our database schema and API payloads.

---

## 🛠 Tech Stack

-   **.NET 9** (Latest LTS features)
-   **PostgreSQL** (via `Npgsql`)
-   **Dapper** (Fast data mapping)
-   **QuestPDF** (High-fidelity report generation)
-   **Swashbuckle/OpenAPI** (Auto-generated documentation)
-   **DotNetEnv** (Environment variable management)

---

## 🚀 Running the API Locally

### Prerequisites
-   [.NET 9 SDK](https://dotnet.microsoft.com/download/dotnet/9.0)
-   PostgreSQL 16+ instance

### Setup
1.  Navigate to this directory:
    ```bash
    cd backend/src/api
    ```
2.  Configure your database connection in a root `.env` file (see root `.env.example`).
3.  Run the application:
    ```bash
    dotnet run
    ```
The API will be available at `http://localhost:5132` by default. You can view the OpenAPI documentation at `http://localhost:5132/swagger`.

---

## 🐳 Docker Integration

The API is fully containerized. In the context of the MPC-Plus stack, it is orchestrated via `docker-compose.yml`. The Dockerfile in this directory is optimized for multi-stage builds and production performance.
