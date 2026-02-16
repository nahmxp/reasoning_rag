@echo off
echo Starting ReasonableRAG...
echo.
echo Checking Ollama...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Ollama is not running!
    echo Please start Ollama first: ollama serve
    pause
    exit /b 1
)
echo [OK] Ollama is running
echo.
echo Starting Streamlit app...
streamlit run app.py


