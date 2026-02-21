# MPC-Plus

Medical Physics Check Plus — Quality Assurance for Varian TrueBeam systems.

## 🚀 Quick Start (Docker)

The easiest way to run the full stack (Database + Backend + Frontend) is with Docker Compose.

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.

### 1. Configuration
Create a `.env` file in the project root (`SeniorDesign/.env`) based on the example:

```bash
# Copy the example env to a real .env file
cp backend/MPC-Plus/.env.example .env
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

## 🛠 Manual Setup (Local Dev)

If you want to run services individually without Docker:

### Backend (.NET API)
1. Ensure **PostgreSQL** is running locally (User: `postgres`, Pass: `postgres`, DB: `mpc_plus`).
2. Update `backend/MPC-Plus/.env` with `Host=localhost`.
3. Run:
   ```bash
   cd backend/MPC-Plus/src/api
   dotnet run
   ```
   API will be at `http://localhost:5132`.

### Frontend (Next.js)
1. Create `.env.local`:
   ```bash
   cd frontend/mpc-plus
   cp .env.local.example .env.local
   ```
2. Install & Run:
   ```bash
   npm install
   npm run dev
   ```
   App will be at `http://localhost:3000`.

---

## 📦 Project Structure

- `backend/MPC-Plus/src/api` — .NET 9 Web API
- `frontend/mpc-plus` — Next.js 14 App Router
- `docker-compose.yml` — Full stack orchestration
- `backups/` — Database schemas and seed data
