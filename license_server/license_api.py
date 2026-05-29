import hashlib
import hmac
import os
import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, EmailStr


DB_PATH = Path(os.environ.get("LICENSE_DB_PATH", "licenses.db"))
ADMIN_TOKEN = os.environ.get("LICENSE_ADMIN_TOKEN", "change-this-admin-token")
APP_TOKEN = os.environ.get("LICENSE_APP_TOKEN", "change-this-public-app-token")
TOKEN_SECRET = os.environ.get("LICENSE_TOKEN_SECRET", secrets.token_hex(32))

app = FastAPI(title="SRT Drama Tool License API")

ADMIN_HTML = r"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>SRT Drama Tool License Admin</title>
  <style>
    :root {
      --bg: #f6f8fb;
      --panel: #ffffff;
      --text: #172033;
      --muted: #657084;
      --line: #d8dee9;
      --brand: #1267c4;
      --brand-dark: #0c4e98;
      --danger: #c92a2a;
      --warning: #b26a00;
      --success: #14783e;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: "Segoe UI", Arial, sans-serif;
      font-size: 14px;
    }
    header {
      background: #182233;
      color: white;
      padding: 16px 22px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
    }
    header h1 {
      margin: 0;
      font-size: 18px;
      font-weight: 650;
    }
    header span { color: #b8c4d6; font-size: 13px; }
    main {
      max-width: 1220px;
      margin: 0 auto;
      padding: 20px;
      display: grid;
      gap: 18px;
    }
    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
      align-items: end;
    }
    .grid.token { grid-template-columns: 1.5fr auto auto; }
    label {
      display: grid;
      gap: 6px;
      font-weight: 600;
      color: #2d3748;
    }
    input, select {
      width: 100%;
      height: 38px;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 8px 10px;
      background: white;
      color: var(--text);
    }
    button {
      height: 38px;
      border: 0;
      border-radius: 6px;
      padding: 0 14px;
      background: var(--brand);
      color: white;
      font-weight: 650;
      cursor: pointer;
      white-space: nowrap;
    }
    button:hover { background: var(--brand-dark); }
    button.secondary {
      background: #e8eef7;
      color: #19314f;
      border: 1px solid #c8d4e5;
    }
    button.secondary:hover { background: #dbe6f5; }
    button.danger { background: var(--danger); }
    button.danger:hover { background: #a61e1e; }
    .toolbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 12px;
    }
    .toolbar h2 {
      margin: 0;
      font-size: 16px;
    }
    .status {
      min-height: 22px;
      color: var(--muted);
    }
    table {
      width: 100%;
      border-collapse: collapse;
      background: white;
    }
    th, td {
      border-bottom: 1px solid var(--line);
      padding: 10px 8px;
      text-align: left;
      vertical-align: top;
    }
    th {
      background: #f0f4f9;
      font-size: 12px;
      text-transform: uppercase;
      color: #526071;
      letter-spacing: .03em;
    }
    td.actions {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      min-width: 260px;
    }
    .badge {
      display: inline-block;
      min-width: 70px;
      text-align: center;
      padding: 4px 8px;
      border-radius: 999px;
      font-weight: 700;
      font-size: 12px;
    }
    .active { background: #e7f6ed; color: var(--success); }
    .inactive, .expired { background: #fff4df; color: var(--warning); }
    .blocked { background: #fde8e8; color: var(--danger); }
    dialog {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 0;
      width: min(900px, calc(100vw - 32px));
    }
    dialog::backdrop { background: rgba(0,0,0,.35); }
    .dialog-body { padding: 16px; }
    .dialog-head {
      padding: 14px 16px;
      border-bottom: 1px solid var(--line);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .dialog-head h3 { margin: 0; font-size: 16px; }
    .mono {
      font-family: Consolas, "Courier New", monospace;
      font-size: 12px;
      word-break: break-all;
    }
    @media (max-width: 900px) {
      .grid, .grid.token { grid-template-columns: 1fr; }
      header { align-items: flex-start; flex-direction: column; }
      td.actions { min-width: 180px; }
    }
  </style>
</head>
<body>
  <header>
    <div>
      <h1>SRT Drama Tool License Admin</h1>
      <span>Create licenses, block users, and reset activated devices.</span>
    </div>
    <span id="serverStatus">Not connected</span>
  </header>

  <main>
    <section class="panel">
      <div class="grid token">
        <label>Admin Token
          <input id="adminToken" type="password" placeholder="LICENSE_ADMIN_TOKEN">
        </label>
        <button id="saveTokenBtn">Save Token</button>
        <button class="secondary" id="refreshBtn">Refresh</button>
      </div>
      <div class="status" id="message"></div>
    </section>

    <section class="panel">
      <div class="toolbar">
        <h2>Create / Update License</h2>
        <button class="secondary" id="randomKeyBtn">Generate Key</button>
      </div>
      <div class="grid">
        <label>License Key
          <input id="licenseKey" placeholder="CUS-001-2026">
        </label>
        <label>Email
          <input id="email" type="email" placeholder="customer@example.com">
        </label>
        <label>Status
          <select id="status">
            <option value="active">active</option>
            <option value="inactive">inactive</option>
            <option value="expired">expired</option>
            <option value="blocked">blocked</option>
          </select>
        </label>
        <label>Device Limit
          <input id="deviceLimit" type="number" min="1" value="1">
        </label>
        <label>Expires At
          <input id="expiresAt" placeholder="2026-12-31T23:59:59+00:00">
        </label>
        <button id="createBtn">Save License</button>
      </div>
    </section>

    <section class="panel">
      <div class="toolbar">
        <h2>Licenses</h2>
        <input id="search" placeholder="Search key or email">
      </div>
      <div style="overflow:auto">
        <table>
          <thead>
            <tr>
              <th>License</th>
              <th>Email</th>
              <th>Status</th>
              <th>Devices</th>
              <th>Expires</th>
              <th>Updated</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody id="licenseRows"></tbody>
        </table>
      </div>
    </section>
  </main>

  <dialog id="activationDialog">
    <div class="dialog-head">
      <h3 id="dialogTitle">Activations</h3>
      <button class="secondary" onclick="activationDialog.close()">Close</button>
    </div>
    <div class="dialog-body">
      <table>
        <thead>
          <tr>
            <th>Machine ID</th>
            <th>Activated</th>
            <th>Last Seen</th>
            <th>App Version</th>
          </tr>
        </thead>
        <tbody id="activationRows"></tbody>
      </table>
    </div>
  </dialog>

  <script>
    const tokenInput = document.getElementById("adminToken");
    const message = document.getElementById("message");
    const rows = document.getElementById("licenseRows");
    const search = document.getElementById("search");
    const activationDialog = document.getElementById("activationDialog");
    const activationRows = document.getElementById("activationRows");
    const dialogTitle = document.getElementById("dialogTitle");
    let licenses = [];

    tokenInput.value = localStorage.getItem("srt_license_admin_token") || "";

    function setMessage(text, type = "info") {
      message.textContent = text;
      message.style.color = type === "error" ? "#c92a2a" : type === "ok" ? "#14783e" : "#657084";
    }

    function headers() {
      return {
        "Authorization": `Bearer ${tokenInput.value.trim()}`,
        "Content-Type": "application/json"
      };
    }

    async function api(path, options = {}) {
      const res = await fetch(path, { ...options, headers: { ...headers(), ...(options.headers || {}) } });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const detail = data.detail && data.detail.message ? data.detail.message : data.detail || res.statusText;
        throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
      }
      return data;
    }

    function render() {
      const q = search.value.trim().toLowerCase();
      rows.innerHTML = "";
      const filtered = licenses.filter(item =>
        !q ||
        String(item.license_key || "").toLowerCase().includes(q) ||
        String(item.email || "").toLowerCase().includes(q)
      );
      if (!filtered.length) {
        const tr = document.createElement("tr");
        const td = document.createElement("td");
        td.colSpan = 7;
        td.textContent = "No licenses found.";
        tr.appendChild(td);
        rows.appendChild(tr);
        return;
      }
      for (const item of filtered) {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td class="mono"></td>
          <td></td>
          <td><span class="badge ${item.status}"></span></td>
          <td></td>
          <td></td>
          <td></td>
          <td class="actions"></td>
        `;
        tr.children[0].textContent = item.license_key || "";
        tr.children[1].textContent = item.email || "";
        tr.children[2].querySelector("span").textContent = item.status || "";
        tr.children[3].textContent = `${item.activations || 0} / ${item.device_limit || 1}`;
        tr.children[4].textContent = item.expires_at || "Lifetime";
        tr.children[5].textContent = item.updated_at || "";
        const actions = tr.children[6];
        actions.appendChild(actionButton("Edit", "secondary", () => fillForm(item)));
        actions.appendChild(actionButton("Devices", "secondary", () => showActivations(item.license_key)));
        actions.appendChild(actionButton("Active", "", () => patchLicense(item.license_key, { status: "active" })));
        actions.appendChild(actionButton("Block", "danger", () => patchLicense(item.license_key, { status: "blocked" })));
        actions.appendChild(actionButton("Reset Devices", "danger", () => resetDevices(item.license_key)));
        rows.appendChild(tr);
      }
    }

    function actionButton(text, cls, fn) {
      const btn = document.createElement("button");
      btn.textContent = text;
      if (cls) btn.className = cls;
      btn.onclick = fn;
      return btn;
    }

    function fillForm(item) {
      licenseKey.value = item.license_key || "";
      email.value = item.email || "";
      status.value = item.status || "active";
      deviceLimit.value = item.device_limit || 1;
      expiresAt.value = item.expires_at || "";
      window.scrollTo({ top: 0, behavior: "smooth" });
    }

    async function refresh() {
      try {
        const data = await api("/admin/v1/licenses");
        licenses = data.licenses || [];
        render();
        document.getElementById("serverStatus").textContent = "Connected";
        setMessage(`Loaded ${licenses.length} licenses.`, "ok");
      } catch (err) {
        document.getElementById("serverStatus").textContent = "Auth required";
        setMessage(err.message, "error");
      }
    }

    async function saveLicense() {
      try {
        const payload = {
          license_key: licenseKey.value.trim(),
          email: email.value.trim() || null,
          status: status.value,
          device_limit: Number(deviceLimit.value || 1),
          expires_at: expiresAt.value.trim() || null
        };
        await api("/admin/v1/licenses", { method: "POST", body: JSON.stringify(payload) });
        setMessage("License saved.", "ok");
        await refresh();
      } catch (err) {
        setMessage(err.message, "error");
      }
    }

    async function patchLicense(key, payload) {
      try {
        await api(`/admin/v1/licenses/${encodeURIComponent(key)}`, { method: "PATCH", body: JSON.stringify(payload) });
        setMessage("License updated.", "ok");
        await refresh();
      } catch (err) {
        setMessage(err.message, "error");
      }
    }

    async function resetDevices(key) {
      if (!confirm(`Reset all activated devices for ${key}?`)) return;
      await patchLicense(key, { reset_devices: true });
    }

    async function showActivations(key) {
      try {
        const data = await api(`/admin/v1/licenses/${encodeURIComponent(key)}/activations`);
        dialogTitle.textContent = `Activations: ${key}`;
        activationRows.innerHTML = "";
        for (const item of data.activations || []) {
          const tr = document.createElement("tr");
          tr.innerHTML = `<td class="mono"></td><td></td><td></td><td></td>`;
          tr.children[0].textContent = item.machine_id || "";
          tr.children[1].textContent = item.activated_at || "";
          tr.children[2].textContent = item.last_seen_at || "";
          tr.children[3].textContent = item.app_version || "";
          activationRows.appendChild(tr);
        }
        if (!activationRows.children.length) {
          const tr = document.createElement("tr");
          const td = document.createElement("td");
          td.colSpan = 4;
          td.textContent = "No activated devices.";
          tr.appendChild(td);
          activationRows.appendChild(tr);
        }
        activationDialog.showModal();
      } catch (err) {
        setMessage(err.message, "error");
      }
    }

    document.getElementById("saveTokenBtn").onclick = () => {
      localStorage.setItem("srt_license_admin_token", tokenInput.value.trim());
      setMessage("Admin token saved in this browser.", "ok");
      refresh();
    };
    document.getElementById("refreshBtn").onclick = refresh;
    document.getElementById("createBtn").onclick = saveLicense;
    document.getElementById("randomKeyBtn").onclick = () => {
      const part = () => Math.random().toString(36).slice(2, 6).toUpperCase();
      licenseKey.value = `SRT-${part()}-${part()}-${new Date().getFullYear()}`;
    };
    search.oninput = render;
    if (tokenInput.value) refresh();
  </script>
</body>
</html>
"""


class ActivateRequest(BaseModel):
    email: EmailStr
    license_key: str
    machine_id: str
    app_version: Optional[str] = None


class CheckRequest(BaseModel):
    token: str
    machine_id: str
    app_version: Optional[str] = None


class CreateLicenseRequest(BaseModel):
    license_key: str
    email: Optional[EmailStr] = None
    status: str = "active"
    device_limit: int = 1
    expires_at: Optional[str] = None


class UpdateLicenseRequest(BaseModel):
    email: Optional[EmailStr] = None
    status: Optional[str] = None
    device_limit: Optional[int] = None
    expires_at: Optional[str] = None
    reset_devices: bool = False


def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    with db() as con:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS licenses (
                license_key TEXT PRIMARY KEY,
                email TEXT,
                status TEXT NOT NULL DEFAULT 'active',
                device_limit INTEGER NOT NULL DEFAULT 1,
                expires_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS activations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                license_key TEXT NOT NULL,
                machine_id TEXT NOT NULL,
                token_hash TEXT NOT NULL,
                activated_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL,
                app_version TEXT,
                UNIQUE(license_key, machine_id),
                FOREIGN KEY(license_key) REFERENCES licenses(license_key)
            )
            """
        )


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/admin", response_class=HTMLResponse)
def admin_panel():
    return HTMLResponse(ADMIN_HTML)


def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def require_app_token(authorization: Optional[str] = Header(default=None)):
    if APP_TOKEN and authorization != f"Bearer {APP_TOKEN}":
        raise HTTPException(status_code=401, detail="Invalid app token")


def require_admin_token(authorization: Optional[str] = Header(default=None)):
    if ADMIN_TOKEN and authorization != f"Bearer {ADMIN_TOKEN}":
        raise HTTPException(status_code=401, detail="Invalid admin token")


def sign_token(license_key, machine_id):
    nonce = secrets.token_urlsafe(18)
    payload = f"{license_key}|{machine_id}|{nonce}"
    sig = hmac.new(TOKEN_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}|{sig}"


def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


def license_error(message, status_code=400):
    raise HTTPException(status_code=status_code, detail={"ok": False, "message": message})


def parse_expiry(value):
    if not value:
        return None
    text = str(value).replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        license_error("expires_at must be ISO format, for example 2026-12-31T23:59:59+00:00")


def validate_license_row(row):
    if not row:
        return False, "License key not found."
    if row["status"] != "active":
        return False, f"License is {row['status']}."
    expires_at = parse_expiry(row["expires_at"])
    if expires_at and datetime.now(timezone.utc) > expires_at:
        return False, "License expired."
    return True, "Valid"


@app.post("/api/v1/licenses/activate", dependencies=[Depends(require_app_token)])
def activate(req: ActivateRequest):
    license_key = req.license_key.strip()
    machine_id = req.machine_id.strip()
    if not license_key or not machine_id:
        license_error("License key and machine ID are required.")

    with db() as con:
        lic = con.execute("SELECT * FROM licenses WHERE license_key = ?", (license_key,)).fetchone()
        ok, message = validate_license_row(lic)
        if not ok:
            license_error(message)

        if lic["email"] and lic["email"].lower() != req.email.lower():
            license_error("Email does not match this license.")

        existing = con.execute(
            "SELECT COUNT(*) AS c FROM activations WHERE license_key = ? AND machine_id <> ?",
            (license_key, machine_id),
        ).fetchone()["c"]
        if existing >= int(lic["device_limit"]):
            license_error("Device limit reached. Ask admin to reset this license.")

        token = sign_token(license_key, machine_id)
        t_hash = token_hash(token)
        seen = now_iso()
        con.execute(
            """
            INSERT INTO activations (license_key, machine_id, token_hash, activated_at, last_seen_at, app_version)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(license_key, machine_id) DO UPDATE SET
                token_hash=excluded.token_hash,
                last_seen_at=excluded.last_seen_at,
                app_version=excluded.app_version
            """,
            (license_key, machine_id, t_hash, seen, seen, req.app_version),
        )

        return {
            "ok": True,
            "message": "License activated.",
            "token": token,
            "license_key": license_key,
            "email": req.email,
            "status": lic["status"],
            "expires_at": lic["expires_at"],
            "device_limit": lic["device_limit"],
        }


@app.post("/api/v1/licenses/check", dependencies=[Depends(require_app_token)])
def check(req: CheckRequest):
    parts = req.token.split("|")
    if len(parts) != 4:
        license_error("Invalid license token.", 401)
    license_key, machine_id, _nonce, sig = parts
    payload = "|".join(parts[:3])
    expected = hmac.new(TOKEN_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected) or machine_id != req.machine_id:
        license_error("Invalid license token.", 401)

    with db() as con:
        lic = con.execute("SELECT * FROM licenses WHERE license_key = ?", (license_key,)).fetchone()
        ok, message = validate_license_row(lic)
        if not ok:
            license_error(message)

        activation = con.execute(
            "SELECT * FROM activations WHERE license_key = ? AND machine_id = ? AND token_hash = ?",
            (license_key, machine_id, token_hash(req.token)),
        ).fetchone()
        if not activation:
            license_error("Device is not activated.", 401)

        con.execute(
            "UPDATE activations SET last_seen_at = ?, app_version = ? WHERE id = ?",
            (now_iso(), req.app_version, activation["id"]),
        )
        return {
            "ok": True,
            "message": "License valid.",
            "license_key": license_key,
            "status": lic["status"],
            "expires_at": lic["expires_at"],
            "device_limit": lic["device_limit"],
        }


@app.post("/admin/v1/licenses", dependencies=[Depends(require_admin_token)])
def create_license(req: CreateLicenseRequest):
    if req.status not in {"active", "inactive", "expired", "blocked"}:
        license_error("Invalid status.")
    if req.device_limit < 1:
        license_error("device_limit must be at least 1.")

    created = now_iso()
    with db() as con:
        con.execute(
            """
            INSERT OR REPLACE INTO licenses
            (license_key, email, status, device_limit, expires_at, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, COALESCE((SELECT created_at FROM licenses WHERE license_key = ?), ?), ?)
            """,
            (
                req.license_key.strip(),
                str(req.email) if req.email else None,
                req.status,
                req.device_limit,
                req.expires_at,
                req.license_key.strip(),
                created,
                created,
            ),
        )
    return {"ok": True, "message": "License saved.", "license_key": req.license_key}


@app.patch("/admin/v1/licenses/{license_key}", dependencies=[Depends(require_admin_token)])
def update_license(license_key: str, req: UpdateLicenseRequest):
    updates = []
    values = []
    if req.email is not None:
        updates.append("email = ?")
        values.append(str(req.email))
    if req.status is not None:
        if req.status not in {"active", "inactive", "expired", "blocked"}:
            license_error("Invalid status.")
        updates.append("status = ?")
        values.append(req.status)
    if req.device_limit is not None:
        if req.device_limit < 1:
            license_error("device_limit must be at least 1.")
        updates.append("device_limit = ?")
        values.append(req.device_limit)
    if req.expires_at is not None:
        updates.append("expires_at = ?")
        values.append(req.expires_at)

    with db() as con:
        if updates:
            updates.append("updated_at = ?")
            values.append(now_iso())
            values.append(license_key)
            con.execute(f"UPDATE licenses SET {', '.join(updates)} WHERE license_key = ?", values)
        if req.reset_devices:
            con.execute("DELETE FROM activations WHERE license_key = ?", (license_key,))

    return {"ok": True, "message": "License updated.", "license_key": license_key}


@app.get("/admin/v1/licenses", dependencies=[Depends(require_admin_token)])
def list_licenses():
    with db() as con:
        rows = con.execute(
            """
            SELECT l.*, COUNT(a.id) AS activations
            FROM licenses l
            LEFT JOIN activations a ON a.license_key = l.license_key
            GROUP BY l.license_key
            ORDER BY l.created_at DESC
            """
        ).fetchall()
    return {"ok": True, "licenses": [dict(row) for row in rows]}


@app.get("/admin/v1/licenses/{license_key}/activations", dependencies=[Depends(require_admin_token)])
def list_activations(license_key: str):
    with db() as con:
        rows = con.execute(
            """
            SELECT id, license_key, machine_id, activated_at, last_seen_at, app_version
            FROM activations
            WHERE license_key = ?
            ORDER BY last_seen_at DESC
            """,
            (license_key,),
        ).fetchall()
    return {"ok": True, "activations": [dict(row) for row in rows]}
