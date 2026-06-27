Set-Location "$PSScriptRoot\.."
python -m uvicorn server.app.main:app --host 0.0.0.0 --port 8000 --reload
