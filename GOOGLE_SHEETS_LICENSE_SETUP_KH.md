# របៀបបង្កើត Google Sheets License API សម្រាប់ SRT Drama Tool

## 1. បង្កើត Google Sheet

1. ចូល Google Drive
2. ចុច New > Google Sheets
3. ដាក់ឈ្មោះឯកសារ: `SRT Drama Tool Licenses`
4. ប្តូរ sheet tab ឲ្យឈ្មោះ `Licenses`
5. ដាក់ header នៅ row 1:

```text
license_key | email | status | device_limit | expires_at | devices | updated_at
```

ឧទាហរណ៍ row 2:

```text
SRT-TEST-2026 | customer@example.com | active | 1 | 2026-12-31T23:59:59+00:00 |  | 
```

បើចង់ Lifetime ទុក `expires_at` ទទេ។

## 2. បង្កើត Apps Script

1. នៅក្នុង Google Sheet ចុច Extensions > Apps Script
2. លុប code ចាស់ចេញ
3. Copy code ពី file `google_apps_script_license_api.gs`
4. Paste ចូល Apps Script editor
5. កែតម្លៃនេះ:

```javascript
const APP_TOKEN = "change-this-public-app-token";
```

ឧទាហរណ៍:

```javascript
const APP_TOKEN = "my-secret-app-token-2026";
```

6. ចុច Save

## 3. Deploy ជា Web App

1. ចុច Deploy > New deployment
2. Select type: Web app
3. Description: `SRT License API`
4. Execute as: `Me`
5. Who has access: `Anyone`
6. ចុច Deploy
7. Copy Web app URL ដែលបញ្ចប់ដោយ `/exec`

ឧទាហរណ៍:

```text
https://script.google.com/macros/s/AKfycbxxxxxxx/exec
```

## 4. កែ SRT Drama Tool Config

កែ file `license_server_config.json`:

```json
{
  "enabled": true,
  "api_base_url": "https://script.google.com/macros/s/AKfycbxxxxxxx/exec",
  "app_token": "my-secret-app-token-2026",
  "strict_online": true,
  "timeout_seconds": 15
}
```

`app_token` ត្រូវដូច `APP_TOKEN` ក្នុង Apps Script។

## 5. របៀបប្រើ

នៅ Google Sheet:

- បង្កើត license key មួយក្នុង column `license_key`
- ដាក់ email customer
- ដាក់ status = `active`
- ដាក់ device_limit = `1`
- ទុក devices ទទេ

នៅ SRT Drama Tool:

1. Settings > License
2. ចុច Register License
3. ដាក់ Email និង License Key
4. ចុច Register

បើជោគជ័យ Google Sheet នឹងបំពេញ column `devices` ដោយស្វ័យប្រវត្តិ។

## Status

- `active`: ប្រើបាន
- `inactive`: បិទបណ្តោះអាសន្ន
- `blocked`: បិទមិនឲ្យប្រើ
- `expired`: ផុតកំណត់

## Reset Device

បើ customer ប្តូរម៉ាស៊ីន:

1. ទៅ Google Sheet
2. រក license key នោះ
3. លុប cell ក្នុង column `devices`
4. customer Register ម្តងទៀត
