param(
  [string]$ConfigPath = "agent/config.example.yaml"
)

Set-Location "$PSScriptRoot\.."

$python = "c:/Users/Shabutha/R-GUARD/.venv/Scripts/python.exe"
if (-not (Test-Path $python)) {
  throw "Python executable not found at $python"
}

& $python -m agent.agent --config $ConfigPath
