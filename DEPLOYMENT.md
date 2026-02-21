# Local Deployment Guide

Deploy MPC Plus on a local server using **Postgres** directly (no Supabase/PostgREST).

---

## Architecture

```
┌─────────────┐       ┌──────────────┐       ┌────────────┐
│   Frontend   │──────▶│  C# Backend  │──────▶│  Postgres  │
│  (Next.js)   │       │  (ASP.NET)   │       │   (DB)     │
│  :3000       │       │  :5000       │       │  :5432     │
└─────────────┘       └──────────────┘       └────────────┘
```

The C# backend uses **Npgsql** and **Dapper** to talk directly to PostgreSQL.

---

## Prerequisites

- **Docker** and **Docker Compose** (for Postgres)
- **.NET 9 SDK** (for the C# backend)
- **Node.js 18+** (for the Next.js frontend)
- Your **Supabase database backup** (`.sql` file)

---

## Step-by-Step Setup

### 1. Restore Your Database (Optional)

If you have a backup file, place it in `backups/`:

```bash
cp your-backup.sql backups/mpc_backup.sql
```

The `docker-compose.yml` mounts this file to `/docker-entrypoint-initdb.d/backup.sql`, so it runs automatically on the **first run** of the database container.

### 2. Start Postgres

```bash
cd /path/to/SeniorDesign
docker-compose up -d db
```

Verify it's running:

```bash
docker-compose logs db
```

### 3. Configure the Backend

```bash
cd backend/MPC-Plus/src/api
cp appsettings.json appsettings.Development.json
```

Ensure `appsettings.Development.json` has the correct connection string (default matches docker-compose):

```json
"Database": {
  "ConnectionString": "Host=localhost;Port=5432;Database=mpc_plus;Username=postgres;Password=postgres"
}
```

### 4. Run the Backend

```bash
cd backend/MPC-Plus/src/api
dotnet run
```

The API should start on `http://localhost:5000`.

### 5. Configure the Frontend

```bash
cd frontend/mpc-plus
cp .env.local.example .env.local
```

Edit the `SeniorDesign/.env` file directly. You no longer need separate configuration files for the frontend or backend! 
Ensure the root `.env` has:
```env
NEXT_PUBLIC_API_URL=http://localhost:5000
Database__ConnectionString=Host=localhost;Port=5432;Database=mpc_plus;Username=postgres;Password=your_secure_password
```

### 6. Run the Frontend

```bash
cd frontend/mpc-plus
npm install
npm run dev
```

Open `http://localhost:3000` in your browser.

---

## Running Everything via Docker Compose

You can run the full stack (DB, Backend, Frontend) with one command from the project root:

```bash
docker-compose up --build
```

- Backend: http://localhost:5000
- Frontend: http://localhost:3000

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `connection refused :5432` | Postgres not running | `docker-compose up -d db` |
| `relation "X" does not exist` | Backup not restored | Delete volume `docker-compose down -v` and restart |
| `Cannot connect to database` | Password mismatch | Check `SeniorDesign/.env` vs `docker-compose.yml` |

---

## Production Configuration (Setting a Custom Password)

If your production database uses a password different from `postgres`, follow these steps:

### Using Docker Compose OR Bare Metal

MPC+ uses a single unified `.env` file in the project root (`SeniorDesign/.env`).

```env
# Database Initialization (Used by docker-compose)
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=mpc_plus

# Backend Connection String
Database__ConnectionString=Host=localhost;Port=5432;Database=mpc_plus;Username=postgres;Password=your_secure_password

# Optional Customizations
CORS_ORIGINS=http://localhost:3000
NEXT_PUBLIC_API_URL=http://localhost:5000
```

Both Docker and bare metal deployment scripts (`start_mpc.bat`) natively parse this exact file. No other `.env` files are necessary.


