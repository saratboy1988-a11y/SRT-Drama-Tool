import os
import signal
import subprocess
import sys
import threading
import time
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import messagebox


APP_DIR = Path(__file__).resolve().parent
SERVER_DIR = APP_DIR / "license_server"
HOST = "0.0.0.0"
PORT = 8000
ADMIN_URL = f"http://localhost:{PORT}/admin"
REQUIRED_MODULES = ("fastapi", "uvicorn", "pydantic", "email_validator")


class LicenseServerLauncher(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("SRT Drama Tool - License Server")
        self.geometry("720x460")
        self.minsize(620, 380)
        self.configure(bg="#f4f7fb")
        self.server_process: subprocess.Popen[str] | None = None
        self.reader_thread: threading.Thread | None = None
        self.installing_requirements = False

        self.admin_token = tk.StringVar(value=os.environ.get("LICENSE_ADMIN_TOKEN", "change-this-admin-token"))
        self.app_token = tk.StringVar(value=os.environ.get("LICENSE_APP_TOKEN", "change-this-public-app-token"))
        self.status_text = tk.StringVar(value="Stopped")

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self) -> None:
        header = tk.Frame(self, bg="#0f172a", height=74)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text="SRT Drama Tool License Server",
            bg="#0f172a",
            fg="#f8fafc",
            font=("Segoe UI", 16, "bold"),
        ).pack(anchor="w", padx=18, pady=(12, 0))
        tk.Label(
            header,
            text=f"Admin panel: {ADMIN_URL}",
            bg="#0f172a",
            fg="#93c5fd",
            font=("Segoe UI", 9),
        ).pack(anchor="w", padx=18, pady=(2, 0))

        body = tk.Frame(self, bg="#f4f7fb")
        body.pack(fill="both", expand=True, padx=18, pady=14)

        form = tk.LabelFrame(body, text="Server Tokens", bg="#f4f7fb", fg="#172033", font=("Segoe UI", 10, "bold"))
        form.pack(fill="x")

        tk.Label(form, text="Admin Token:", bg="#f4f7fb", font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w", padx=10, pady=8)
        admin_entry = tk.Entry(form, textvariable=self.admin_token, show="*", font=("Consolas", 10))
        admin_entry.grid(row=0, column=1, sticky="ew", padx=10, pady=8)

        tk.Label(form, text="App Token:", bg="#f4f7fb", font=("Segoe UI", 9)).grid(row=1, column=0, sticky="w", padx=10, pady=8)
        app_entry = tk.Entry(form, textvariable=self.app_token, show="*", font=("Consolas", 10))
        app_entry.grid(row=1, column=1, sticky="ew", padx=10, pady=8)
        form.columnconfigure(1, weight=1)

        controls = tk.Frame(body, bg="#f4f7fb")
        controls.pack(fill="x", pady=12)

        self.start_btn = tk.Button(controls, text="Start Server", command=self.start_server, bg="#16a34a", fg="white", font=("Segoe UI", 10, "bold"), relief="flat", padx=16, pady=8)
        self.start_btn.pack(side="left", padx=(0, 8))

        self.stop_btn = tk.Button(controls, text="Stop Server", command=self.stop_server, bg="#dc2626", fg="white", font=("Segoe UI", 10, "bold"), relief="flat", padx=16, pady=8, state="disabled")
        self.stop_btn.pack(side="left", padx=8)

        tk.Button(controls, text="Open Admin Panel", command=lambda: webbrowser.open(ADMIN_URL), bg="#2563eb", fg="white", font=("Segoe UI", 10, "bold"), relief="flat", padx=16, pady=8).pack(side="left", padx=8)
        tk.Button(controls, text="Copy Admin Token", command=self.copy_admin_token, bg="#7c3aed", fg="white", font=("Segoe UI", 10, "bold"), relief="flat", padx=16, pady=8).pack(side="left", padx=8)
        tk.Button(controls, text="Copy App Config", command=self.copy_app_config, bg="#475569", fg="white", font=("Segoe UI", 10, "bold"), relief="flat", padx=16, pady=8).pack(side="left", padx=8)

        tk.Label(controls, textvariable=self.status_text, bg="#f4f7fb", fg="#334155", font=("Segoe UI", 10, "bold")).pack(side="right")

        log_frame = tk.LabelFrame(body, text="Server Log", bg="#f4f7fb", fg="#172033", font=("Segoe UI", 10, "bold"))
        log_frame.pack(fill="both", expand=True)
        self.log_box = tk.Text(log_frame, height=12, bg="#0b1220", fg="#dbeafe", insertbackground="#dbeafe", font=("Consolas", 9), wrap="word")
        self.log_box.pack(fill="both", expand=True, padx=8, pady=8)
        self._log("Ready. Click Start Server.")

    def _log(self, message: str) -> None:
        self.log_box.insert("end", f"{time.strftime('%H:%M:%S')}  {message}\n")
        self.log_box.see("end")

    def start_server(self) -> None:
        if self.server_process and self.server_process.poll() is None:
            self._log("Server is already running.")
            return

        if not SERVER_DIR.exists():
            messagebox.showerror("Missing Server", f"Cannot find:\n{SERVER_DIR}")
            return

        missing = self._missing_requirements()
        if missing and not self.installing_requirements:
            self.installing_requirements = True
            self.start_btn.configure(state="disabled")
            self.status_text.set("Installing requirements...")
            self._log(f"Missing Python packages: {', '.join(missing)}")
            self._log("Installing license server requirements. Please wait...")
            threading.Thread(target=self._install_requirements_then_start, daemon=True).start()
            return

        env = os.environ.copy()
        env["LICENSE_ADMIN_TOKEN"] = self.admin_token.get().strip() or "change-this-admin-token"
        env["LICENSE_APP_TOKEN"] = self.app_token.get().strip() or "change-this-public-app-token"

        cmd = [
            sys.executable,
            "-m",
            "uvicorn",
            "license_api:app",
            "--host",
            HOST,
            "--port",
            str(PORT),
        ]

        try:
            self.server_process = subprocess.Popen(
                cmd,
                cwd=str(SERVER_DIR),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
        except Exception as exc:
            messagebox.showerror("Start Failed", str(exc))
            return

        self.status_text.set(f"Running on localhost:{PORT}")
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self._log("Starting license server...")
        self._log("Use the Admin Token from this launcher when the admin page asks for a token.")
        self.reader_thread = threading.Thread(target=self._read_server_output, daemon=True)
        self.reader_thread.start()
        self.after(1200, lambda: webbrowser.open(ADMIN_URL))

    def _missing_requirements(self) -> list[str]:
        import importlib.util

        return [name for name in REQUIRED_MODULES if importlib.util.find_spec(name) is None]

    def _install_requirements_then_start(self) -> None:
        try:
            process = subprocess.Popen(
                [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                cwd=str(SERVER_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
            if process.stdout:
                for line in process.stdout:
                    self.after(0, self._log, line.rstrip())
            code = process.wait()
            if code != 0:
                self.after(0, messagebox.showerror, "Install Failed", "Could not install license server requirements. Check the log.")
                self.after(0, self._server_stopped)
                return
            self.after(0, self._log, "Requirements installed.")
        except Exception as exc:
            self.after(0, messagebox.showerror, "Install Failed", str(exc))
            self.after(0, self._server_stopped)
            return
        finally:
            self.installing_requirements = False

        self.after(0, self.start_server)

    def _read_server_output(self) -> None:
        process = self.server_process
        if not process or not process.stdout:
            return
        for line in process.stdout:
            self.after(0, self._log, line.rstrip())
        self.after(0, self._server_stopped)

    def _server_stopped(self) -> None:
        self.status_text.set("Stopped")
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self._log("Server stopped.")

    def stop_server(self) -> None:
        process = self.server_process
        if not process or process.poll() is not None:
            self._server_stopped()
            return

        self._log("Stopping server...")
        try:
            if sys.platform == "win32":
                subprocess.run(
                    ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    timeout=10,
                )
            else:
                process.send_signal(signal.SIGTERM)
        except Exception as exc:
            self._log(f"Stop failed: {exc}")

    def copy_app_config(self) -> None:
        config = (
            "{\n"
            '  "enabled": true,\n'
            f'  "api_base_url": "http://localhost:{PORT}",\n'
            f'  "app_token": "{self.app_token.get().strip()}",\n'
            '  "timeout_seconds": 15\n'
            "}\n"
        )
        self.clipboard_clear()
        self.clipboard_append(config)
        self._log("App config copied to clipboard.")
        messagebox.showinfo("Copied", "license_server_config.json content copied to clipboard.")

    def copy_admin_token(self) -> None:
        token = self.admin_token.get().strip()
        self.clipboard_clear()
        self.clipboard_append(token)
        self._log("Admin token copied to clipboard.")
        messagebox.showinfo(
            "Copied",
            "Admin token copied. Paste it into the Admin Token box in the browser.\n\n"
            "If you changed this token while the server was already running, stop and start the server first.",
        )

    def _on_close(self) -> None:
        if self.server_process and self.server_process.poll() is None:
            if messagebox.askyesno("Stop Server?", "License server is running. Stop it before closing?"):
                self.stop_server()
                self.after(500, self.destroy)
                return
        self.destroy()


if __name__ == "__main__":
    LicenseServerLauncher().mainloop()
