import hashlib
import hmac
import os
import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, EmailStr


DB_PATH = Path(os.environ.get("LICENSE_DB_PATH", "licenses.db"))
ADMIN_TOKEN = os.environ.get("LICENSE_ADMIN_TOKEN", "change-this-admin-token")
APP_TOKEN = os.environ.get("LICENSE_APP_TOKEN", "change-this-public-app-token")
TOKEN_SECRET = os.environ.get("LICENSE_TOKEN_SECRET", secrets.token_hex(32))

app = FastAPI(title="SRT Drama Tool License API")


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
