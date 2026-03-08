@echo off
echo =========================================
echo Retail Failure Simulator - Setup Script
echo =========================================
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo X Docker is not installed. Please install Docker first.
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo X Docker Compose is not installed. Please install Docker Compose first.
    exit /b 1
)

echo √ Docker and Docker Compose are installed
echo.

REM Create .env file for backend if it doesn't exist
if not exist backend\.env (
    echo Creating backend .env file...
    copy backend\.env.example backend\.env
    echo √ Backend .env file created
) else (
    echo √ Backend .env file already exists
)

echo.
echo Starting services with Docker Compose...
echo.

REM Start Docker Compose
docker-compose up -d

echo.
echo Waiting for services to be ready...
timeout /t 10 /nobreak >nul

echo.
echo =========================================
echo √ Setup Complete!
echo =========================================
echo.
echo Services are running:
echo   - Frontend: http://localhost:5173
echo   - Backend API: http://localhost:8000
echo   - API Docs: http://localhost:8000/docs
echo   - MySQL: localhost:3306
echo.
echo To view logs:
echo   docker-compose logs -f
echo.
echo To stop services:
echo   docker-compose down
echo.
pause
