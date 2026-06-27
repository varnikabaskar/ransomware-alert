Set-Location "$PSScriptRoot\.."
$body = @{
  behavioral_csv_path = "data/behavioral/sample_behavioral.csv"
  decoy_csv_path = "data/decoy/sample_decoy.csv"
  sequence_length = 2
  epochs = 60
  test_size = 0.5
  random_state = 42
} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/train" -Body $body -ContentType "application/json"
