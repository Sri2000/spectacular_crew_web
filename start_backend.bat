@echo off
echo Starting Retail Failure Simulator Backend...
echo.

cd backend

echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Initializing database...
python -c "from database import init_db; init_db()"

echo.
echo Starting FastAPI server...
echo Backend will be available at: http://localhost:8000
echo API Docs will be available at: http://localhost:8000/docs
echo.
uvicorn main:app --reload --host 0.0.0.0 --port 8000
