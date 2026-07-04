$body = @{
    user_id = "test_user"
    action_taken = "easy"
    outcome = "success"
    correct = $true
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8001/api/learning/decision/feedback" -Method POST -Body $body -ContentType "application/json"
