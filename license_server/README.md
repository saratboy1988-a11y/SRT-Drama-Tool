# SRT Drama Tool Online License Server

This is a small FastAPI + SQLite license server for SRT Drama Tool.

## Run locally

```powershell
cd license_server
python -m pip install -r requirements.txt
$env:LICENSE_ADMIN_TOKEN="change-this-admin-token"
$env:LICENSE_APP_TOKEN="change-this-public-app-token"
python -m uvicorn license_api:app --host 0.0.0.0 --port 8000
```

## Configure the desktop app

Create this file on the customer/admin PC:

```text
%APPDATA%\SRTDramaTool\license_server_config.json
```

Example:

```json
{
  "enabled": true,
  "api_base_url": "https://your-domain.com",
  "app_token": "change-this-public-app-token",
  "timeout_seconds": 15
}
```

## Admin create license

```powershell
$headers = @{ Authorization = "Bearer change-this-admin-token" }
$body = @{
  license_key = "CUS-001-2026"
  email = "customer@example.com"
  status = "active"
  device_limit = 1
  expires_at = $null
} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/admin/v1/licenses" -Headers $headers -ContentType "application/json" -Body $body
```

## Admin block/deactivate license

```powershell
$headers = @{ Authorization = "Bearer change-this-admin-token" }
$body = @{ status = "blocked" } | ConvertTo-Json
Invoke-RestMethod -Method Patch -Uri "http://localhost:8000/admin/v1/licenses/CUS-001-2026" -Headers $headers -ContentType "application/json" -Body $body
```

Status values: `active`, `inactive`, `expired`, `blocked`.
