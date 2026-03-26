from __future__ import annotations

import hashlib
import http.server
import secrets
import threading
import urllib.parse
import webbrowser
from typing import Any

import httpx
from rich.console import Console

from happi.config.config import set_config_value
from happi.log import get_logger

_log = get_logger("config.auth")
console = Console()
err_console = Console(stderr=True)

_CALLBACK_PORT = 18923
_REDIRECT_URI = f"http://localhost:{_CALLBACK_PORT}/callback"


def oauth_login(
    api_name: str,
    *,
    authorize_url: str,
    token_url: str,
    client_id: str,
    scopes: str = "",
    manual: bool = False,
) -> bool:
    state = secrets.token_urlsafe(32)
    code_verifier = secrets.token_urlsafe(64)
    code_challenge = hashlib.sha256(code_verifier.encode()).digest().hex()

    params: dict[str, str] = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": _REDIRECT_URI,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    if scopes:
        params["scope"] = scopes

    auth_url = f"{authorize_url}?{urllib.parse.urlencode(params)}"

    if manual:
        return _manual_flow(api_name, auth_url, token_url, client_id, code_verifier, state)
    return _browser_flow(api_name, auth_url, token_url, client_id, code_verifier, state)


def _browser_flow(
    api_name: str,
    auth_url: str,
    token_url: str,
    client_id: str,
    code_verifier: str,
    state: str,
) -> bool:
    result: dict[str, str] = {}
    error_result: dict[str, str] = {}

    class _Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            parsed = urllib.parse.urlparse(self.path)
            query = dict(urllib.parse.parse_qsl(parsed.query))
            if query.get("state") != state:
                error_result["error"] = "State mismatch"
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"State mismatch. Close this window.")
                return
            if "code" in query:
                result["code"] = query["code"]
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"Login successful! You can close this window.")
            else:
                error_result["error"] = query.get("error", "unknown")
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Login failed. Close this window.")

        def log_message(self, format: str, *args: object) -> None:
            return

    server = http.server.HTTPServer(("127.0.0.1", _CALLBACK_PORT), _Handler)
    thread = threading.Thread(target=server.handle_request, daemon=True)
    thread.start()

    console.print(f"Opening browser for {api_name} login...")
    webbrowser.open(auth_url)

    thread.join(timeout=120)
    server.server_close()

    if error_result:
        err_console.print(f"[red]✗[/red] Login failed: {error_result.get('error', 'unknown')}")
        err_console.print()
        err_console.print("Try manual mode:")
        err_console.print(f"  happi auth login {api_name} --manual")
        return False

    if "code" not in result:
        err_console.print("[red]✗[/red] No authorization code received (timed out)")
        err_console.print()
        err_console.print("Try manual mode:")
        err_console.print(f"  happi auth login {api_name} --manual")
        return False

    return _exchange_code(api_name, token_url, client_id, result["code"], code_verifier)


def _manual_flow(
    api_name: str,
    auth_url: str,
    token_url: str,
    client_id: str,
    code_verifier: str,
    state: str,
) -> bool:
    _ = state
    console.print("Open this URL in your browser:")
    console.print(f"  {auth_url}")
    console.print()
    code = console.input("Paste the authorization code: ").strip()
    if not code:
        err_console.print("[red]✗[/red] No code provided")
        return False
    return _exchange_code(api_name, token_url, client_id, code, code_verifier)


def _exchange_code(
    api_name: str,
    token_url: str,
    client_id: str,
    code: str,
    code_verifier: str,
) -> bool:
    try:
        response = httpx.post(
            token_url,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": _REDIRECT_URI,
                "client_id": client_id,
                "code_verifier": code_verifier,
            },
            timeout=30,
        )
        response.raise_for_status()
        token_data: dict[str, Any] = response.json()
        access_token = str(token_data.get("access_token", ""))
        if not access_token:
            err_console.print("[red]✗[/red] No access_token in response")
            return False

        auth_config: dict[str, str] = {
            "type": "bearer",
            "token": access_token,
        }
        refresh = token_data.get("refresh_token")
        if refresh:
            auth_config["refresh_token"] = str(refresh)

        set_config_value(f"apis.{api_name}.auth", auth_config)
        console.print(f"[green]✓[/green] Logged in to [cyan]{api_name}[/cyan]")
        return True
    except httpx.HTTPStatusError as e:
        err_console.print(f"[red]✗[/red] Token exchange failed ({e.response.status_code})")
        return False
    except Exception as e:
        err_console.print(f"[red]✗[/red] Token exchange failed: {e}")
        return False
