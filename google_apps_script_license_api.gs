/*
  SRT Drama Tool - Google Sheets License API

  Sheet name: Licenses
  Headers:
  license_key | email | status | device_limit | expires_at | devices | updated_at
*/

const APP_TOKEN = "change-this-public-app-token";
const SHEET_NAME = "Licenses";

function doPost(e) {
  try {
    const body = JSON.parse((e.postData && e.postData.contents) || "{}");
    if (APP_TOKEN && body._app_token !== APP_TOKEN) {
      return jsonResponse({ ok: false, message: "Invalid app token" });
    }

    const path = String(body._path || "");
    if (path === "/api/v1/licenses/activate") {
      return activateLicense(body);
    }
    if (path === "/api/v1/licenses/check") {
      return checkLicense(body);
    }
    return jsonResponse({ ok: false, message: "Unknown endpoint: " + path });
  } catch (err) {
    return jsonResponse({ ok: false, message: String(err && err.message ? err.message : err) });
  }
}

function activateLicense(req) {
  const email = String(req.email || "").trim().toLowerCase();
  const licenseKey = String(req.license_key || "").trim();
  const machineId = String(req.machine_id || "").trim();
  if (!email || !licenseKey || !machineId) {
    return jsonResponse({ ok: false, message: "Email, license key, and machine ID are required." });
  }

  const sheet = getSheet();
  const rowInfo = findLicenseRow(sheet, licenseKey);
  if (!rowInfo) {
    return jsonResponse({ ok: false, message: "License key not found." });
  }

  const row = rowInfo.data;
  const status = String(row.status || "").toLowerCase();
  if (status !== "active") {
    return jsonResponse({ ok: false, message: "License is " + (status || "inactive") + "." });
  }

  const savedEmail = String(row.email || "").trim().toLowerCase();
  if (savedEmail && savedEmail !== email) {
    return jsonResponse({ ok: false, message: "Email does not match this license." });
  }

  if (isExpired(row.expires_at)) {
    return jsonResponse({ ok: false, message: "License expired." });
  }

  const deviceLimit = Math.max(1, parseInt(row.device_limit || "1", 10));
  const devices = parseDevices(row.devices);
  const existing = devices.find((item) => item.machine_id === machineId);
  if (!existing && devices.length >= deviceLimit) {
    return jsonResponse({ ok: false, message: "Device limit reached. Ask admin to reset this license." });
  }

  const now = new Date().toISOString();
  const token = makeToken(licenseKey, machineId);
  if (existing) {
    existing.token = token;
    existing.last_seen_at = now;
    existing.app_version = req.app_version || "";
  } else {
    devices.push({
      machine_id: machineId,
      token: token,
      activated_at: now,
      last_seen_at: now,
      app_version: req.app_version || "",
    });
  }

  writeLicenseFields(sheet, rowInfo.rowNumber, {
    devices: JSON.stringify(devices),
    updated_at: now,
  });

  return jsonResponse({
    ok: true,
    message: "License activated.",
    token: token,
    license_key: licenseKey,
    email: email,
    status: status,
    expires_at: row.expires_at || "",
    device_limit: deviceLimit,
  });
}

function checkLicense(req) {
  const token = String(req.token || "").trim();
  const machineId = String(req.machine_id || "").trim();
  const parts = token.split("|");
  if (parts.length < 3 || !machineId) {
    return jsonResponse({ ok: false, message: "Invalid license token." });
  }

  const licenseKey = parts[0];
  const tokenMachineId = parts[1];
  if (tokenMachineId !== machineId) {
    return jsonResponse({ ok: false, message: "Invalid license token." });
  }

  const sheet = getSheet();
  const rowInfo = findLicenseRow(sheet, licenseKey);
  if (!rowInfo) {
    return jsonResponse({ ok: false, message: "License key not found." });
  }

  const row = rowInfo.data;
  const status = String(row.status || "").toLowerCase();
  if (status !== "active") {
    return jsonResponse({ ok: false, message: "License is " + (status || "inactive") + "." });
  }
  if (isExpired(row.expires_at)) {
    return jsonResponse({ ok: false, message: "License expired." });
  }

  const devices = parseDevices(row.devices);
  const device = devices.find((item) => item.machine_id === machineId && item.token === token);
  if (!device) {
    return jsonResponse({ ok: false, message: "Device is not activated." });
  }

  device.last_seen_at = new Date().toISOString();
  device.app_version = req.app_version || device.app_version || "";
  writeLicenseFields(sheet, rowInfo.rowNumber, {
    devices: JSON.stringify(devices),
    updated_at: new Date().toISOString(),
  });

  return jsonResponse({
    ok: true,
    message: "Online license valid.",
    license_key: licenseKey,
    status: status,
    expires_at: row.expires_at || "",
    device_limit: Math.max(1, parseInt(row.device_limit || "1", 10)),
  });
}

function getSheet() {
  const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = spreadsheet.getSheetByName(SHEET_NAME) || spreadsheet.getActiveSheet();
  const headers = ["license_key", "email", "status", "device_limit", "expires_at", "devices", "updated_at"];
  const existing = sheet.getRange(1, 1, 1, headers.length).getValues()[0];
  if (existing.join("") === "") {
    sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
  }
  return sheet;
}

function findLicenseRow(sheet, licenseKey) {
  const values = sheet.getDataRange().getValues();
  const headers = values[0].map(String);
  for (let i = 1; i < values.length; i++) {
    const data = {};
    headers.forEach((header, index) => data[header] = values[i][index]);
    if (String(data.license_key || "").trim() === licenseKey) {
      return { rowNumber: i + 1, data: data, headers: headers };
    }
  }
  return null;
}

function writeLicenseFields(sheet, rowNumber, fields) {
  const headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0].map(String);
  Object.keys(fields).forEach((name) => {
    const index = headers.indexOf(name);
    if (index >= 0) {
      sheet.getRange(rowNumber, index + 1).setValue(fields[name]);
    }
  });
}

function parseDevices(value) {
  try {
    const parsed = JSON.parse(String(value || "[]"));
    return Array.isArray(parsed) ? parsed : [];
  } catch (err) {
    return [];
  }
}

function isExpired(value) {
  if (!value) return false;
  const expires = new Date(value);
  if (isNaN(expires.getTime())) return false;
  return new Date().getTime() > expires.getTime();
}

function makeToken(licenseKey, machineId) {
  return licenseKey + "|" + machineId + "|" + Utilities.getUuid();
}

function jsonResponse(data) {
  return ContentService
    .createTextOutput(JSON.stringify(data))
    .setMimeType(ContentService.MimeType.JSON);
}
