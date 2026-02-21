@echooff
title MPC+ Server Startup
echo ========================================
echo   MPC+ Server Starting...
echo ========================================

REM --- Configuration ---
SETPROJECT_ROOT=%~dp0
SETDOTNET_PROJECT=%PROJECT_ROOT%backend\src\api
SETFRONTEND_DIR=%PROJECT_ROOT%frontend

REM --- 1. Check if PostgreSQL is running ---
echo [1/3] Checking PostgreSQL...
scquery postgresql-x64-16|find"RUNNING">nul2>&1
if%ERRORLEVEL%NEQ0 (
echo      Starting PostgreSQL service...
net start postgresql-x64-16
)else (
echo      PostgreSQL is already running.
)

REM --- 2. Start Backend (.NET API) ---
echo [2/3] Starting Backend API on port 5000...
start"MPC+ Backend"cmd /k"cd /d "%DOTNET_PROJECT%" && dotnet run --urls=http://0.0.0.0:5000 --environment Production"

timeout /t5 /nobreak>nul

REM --- 3. Start Frontend (Next.js) ---
echo [3/3] Starting Frontend on port 3000...
cd /d"%FRONTEND_DIR%"
ifnotexist node_modules (
echo      Installing npm dependencies...
call npm install
)
ifnotexist .next (
echo      Building Next.js app...
call npm run build
)
start"MPC+ Frontend"cmd /k"cd /d "%FRONTEND_DIR%" && npm run start"

echo ========================================
echo   MPC+ is running!
echo   Frontend: http://localhost:3000
echo   Backend:  http://localhost:5000
echo ========================================
pause