# Docker Quickstart Guide

This guide covers the basic commands needed to manage the MPC Plus Docker environment.

All commands must be run from the root of the project repository (where the `docker-compose.yml` file is located).

## Starting the Application

To start the entire application (Database, Backend API, Frontend Web App, and ETL Pipeline) for normal usage:

```bash
docker-compose up -d
```
> The `-d` flag runs the containers in the "detached" background mode, freeing up your terminal.
> **Access the App:** Open your browser to `http://localhost:3000`

## Stopping the Application

To safely stop all running containers without destroying your database data:

```bash
docker-compose stop
```
> Use this when you are done working for the day.

## Rebuilding the Application (After Code Changes)

If you change code in the `frontend/`, `backend/`, or `api/` directories, you must tell Docker to rebuild the images so your new code is included:

```bash
docker-compose up -d --build
```

**Note:** Next.js (Frontend) "bakes" environment variables into its code at build-time. If you ever change the API URL or ports, you **must** use `--build`.

## Viewing Logs

If something isn't working, check the logs.

**View all logs together:**
```bash
docker-compose logs -f
```

**View logs for a specific service:**
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f db
docker-compose logs -f etl
```
> The `-f` flag "follows" the logs. Press `Ctrl+C` to stop watching.

## Completely Erasing and Restarting (Hard Reset)

If the environment is completely broken or you want to start fresh (e.g. wiping the database completely):

1. Stop containers and destroy them:
```bash
docker-compose down
```

2. Wipe the named volumes (WARNING: This heavily wipes your database data):
```bash
docker-compose down -v
```

## Useful Status Commands

**Check what is currently running:**
```bash
docker-compose ps
```

**Restart a single service:**
```bash
docker-compose restart backend
```
