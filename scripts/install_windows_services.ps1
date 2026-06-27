param(
  [string]$ServerServiceName = "RGuardServer",
  [string]$AgentServiceName = "RGuardAgent",
  [string]$AgentConfigPath = "C:\Users\Shabutha\R-GUARD\agent\config.example.yaml"
)

$projectRoot = "C:\Users\Shabutha\R-GUARD"
$pythonExe = "C:\Users\Shabutha\R-GUARD\.venv\Scripts\python.exe"

if (-not (Test-Path $pythonExe)) {
  throw "Python executable not found at $pythonExe"
}

$serverBin = '"' + $pythonExe + '" -m uvicorn server.app.main:app --host 0.0.0.0 --port 8000'
$agentBin = '"' + $pythonExe + '" -m agent.agent --config "' + $AgentConfigPath + '"'

if (-not (Get-Service -Name $ServerServiceName -ErrorAction SilentlyContinue)) {
  New-Service -Name $ServerServiceName -BinaryPathName $serverBin -DisplayName "R-GUARD Server" -Description "R-GUARD FastAPI server" -StartupType Automatic
}

if (-not (Get-Service -Name $AgentServiceName -ErrorAction SilentlyContinue)) {
  New-Service -Name $AgentServiceName -BinaryPathName $agentBin -DisplayName "R-GUARD Agent" -Description "R-GUARD endpoint agent" -StartupType Automatic
}

Write-Output "Services configured. Run as Administrator to install/start services."
Write-Output "Start-Service $ServerServiceName"
Write-Output "Start-Service $AgentServiceName"
