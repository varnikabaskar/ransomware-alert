param(
    [string]$OutputPath = "demo_video/rguard_demo.mp4",
    [int]$DurationSeconds = 420,
    [int]$Fps = 30,
    [string]$DashboardUrl = "http://127.0.0.1:8000/dashboard",
    [string]$DecoyDir = "agent/decoy_files_wiretrap_test",
    [switch]$AutoAttack,
    [int]$AttackDelaySeconds = 150,
    [double]$AttackFileDelay = 0.25,
    [switch]$OpenExplorer,
    [switch]$OpenDashboard
)

$ErrorActionPreference = "Stop"

function Resolve-WorkspacePath {
    param([string]$RelativeOrAbsolute)
    if ([System.IO.Path]::IsPathRooted($RelativeOrAbsolute)) {
        return $RelativeOrAbsolute
    }
    return [System.IO.Path]::GetFullPath((Join-Path (Get-Location).Path $RelativeOrAbsolute))
}

$ffmpeg = Get-Command ffmpeg -ErrorAction SilentlyContinue
if (-not $ffmpeg) {
    Write-Error "ffmpeg not found in PATH. Install ffmpeg and retry."
}

$pythonExe = Resolve-WorkspacePath ".venv/Scripts/python.exe"
if (-not (Test-Path $pythonExe)) {
    Write-Error "Python executable not found at .venv/Scripts/python.exe. Activate your environment first."
}

$finalOutputPath = Resolve-WorkspacePath $OutputPath
$outDir = Split-Path -Parent $finalOutputPath
if (-not (Test-Path $outDir)) {
    New-Item -ItemType Directory -Path $outDir | Out-Null
}

if ($OpenExplorer) {
    $explorerTarget = Resolve-WorkspacePath "agent/decoy_files"
    if (Test-Path $explorerTarget) {
        Start-Process explorer.exe $explorerTarget | Out-Null
        Write-Host "Opened decoy folder: $explorerTarget"
    }
}

if ($OpenDashboard) {
    Start-Process $DashboardUrl | Out-Null
    Write-Host "Opened dashboard: $DashboardUrl"
}

$attackJob = $null
if ($AutoAttack) {
    $attackScript = Resolve-WorkspacePath "scripts/demo_fake_attack.py"
    if (-not (Test-Path $attackScript)) {
        Write-Error "Attack script not found at scripts/demo_fake_attack.py"
    }

    $jobScript = {
        param($delaySec, $pyExe, $scriptPath, $targetDir, $fileDelay)
        Start-Sleep -Seconds $delaySec
        & $pyExe $scriptPath --dir $targetDir --delay $fileDelay
    }

    $attackJob = Start-Job -ScriptBlock $jobScript -ArgumentList @(
        $AttackDelaySeconds,
        $pythonExe,
        $attackScript,
        $DecoyDir,
        $AttackFileDelay
    )

    Write-Host "AutoAttack enabled. Fake attack will run after $AttackDelaySeconds seconds."
}

Write-Host "Starting screen capture..."
Write-Host "Output: $finalOutputPath"
Write-Host "Duration: $DurationSeconds seconds"

$ffmpegArgs = @(
    "-y",
    "-f", "gdigrab",
    "-framerate", "$Fps",
    "-i", "desktop",
    "-t", "$DurationSeconds",
    "-c:v", "libx264",
    "-preset", "veryfast",
    "-crf", "23",
    "-pix_fmt", "yuv420p",
    $finalOutputPath
)

$recordProc = Start-Process -FilePath $ffmpeg.Source -ArgumentList $ffmpegArgs -PassThru -NoNewWindow
$recordProc.WaitForExit()

if ($attackJob) {
    $attackOutput = Receive-Job -Job $attackJob -Keep
    if ($attackOutput) {
        Write-Host "---- AutoAttack Output ----"
        $attackOutput | ForEach-Object { Write-Host $_ }
    }
    Remove-Job -Job $attackJob -Force
}

if ($recordProc.ExitCode -eq 0 -and (Test-Path $finalOutputPath)) {
    Write-Host "Video created successfully: $finalOutputPath"
} else {
    Write-Error "Recording failed with ffmpeg exit code $($recordProc.ExitCode)"
}
