# MPC-Plus

Medical Physics Check Plus — Quality Assurance for Varian TrueBeam systems.

This project is a unified monorepo containing both the .NET backend and the Next.js frontend.

## 🚀 Quick Start (Docker)

The easiest way to run the full stack (Database + Backend + Frontend) is with Docker Compose.

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.

### 1. Configuration
Create a `.env` file in the project root (`SeniorDesign/.env`) based on the example:

```bash
# Copy the example env to a real .env file
cp .env.example .env
```
*(The default values in `.env.example` work out-of-the-box for Docker)*

### 2. Run the App
From the project root:

```bash
docker-compose up --build
```

This will start:
- **PostgreSQL 16** (Database)
- **.NET 9 Backend** on `http://localhost:5000`
- **Next.js Frontend** on `http://localhost:3000`

### 3. Access
Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 🔑 Environment Variables

The application requires a `.env` file at the root. See `.env.example` for the full list of variables.

| Variable | Description | Default |
|----------|-------------|---------|
| `POSTGRES_USER` | Database username | `postgres` |
| `POSTGRES_PASSWORD` | Database password | `postgres` |
| `POSTGRES_DB` | Database name | `mpc_plus` |
| `Database__ConnectionString` | Connection string for the .NET API | `Host=db;...` (Docker) |
| `NEXT_PUBLIC_API_URL` | API URL for the Frontend | `http://localhost:5000` |

---

## 🛠 Manual Setup (Local Dev)

If you want to run services individually without Docker:

### 1. Root Configuration
Ensure you have a `.env` file in the root directory.

### 2. Backend (.NET API)
1. Ensure **PostgreSQL** is running locally (User: `postgres`, Pass: `postgres`, DB: `mpc_plus`).
2. Run:
   ```bash
   cd backend/src/api
   dotnet run
   ```
   API will be at `http://localhost:5132`.

### 3. Frontend (Next.js)
1. Install & Run:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   App will be at `http://localhost:3000`.

---

## 📦 Project Structure

- `backend/` — .NET 9 Backend services and Data Processing
  - `src/api` — Main Web API
  - `src/data_manipulation` — Python ETL and Monitoring scripts
- `frontend/` — Next.js 16 App Router (React 19)
- `docker-compose.yml` — Full stack orchestration
- `backups/` — Database schemas and seed data
- `scripts/` — Utility scripts for automation
- `start_mpc.bat` — Windows shortcut to start the application
