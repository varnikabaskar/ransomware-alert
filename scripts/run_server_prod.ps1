Set-Location "$PSScriptRoot\.."

$python = "c:/Users/Shabutha/R-GUARD/.venv/Scripts/python.exe"
if (-not (Test-Path $python)) {
  throw "Python executable not found at $python"
}

& $python -m uvicorn server.app.main:app --host 0.0.0.0 --port 8000
