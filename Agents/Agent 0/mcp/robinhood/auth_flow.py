#!/usr/bin/env python3
import base64
import hashlib
import json
import os
import secrets
import sys
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
import subprocess

REDIRECT_URI = "http://localhost:8080/callback"
REGISTER_URL = "https://agent.robinhood.com/oauth/trading/register"
TOKEN_URL = "https://api.robinhood.com/oauth2/token/"
ENV_PATH = os.path.expanduser("~/Agents/Agent 0/.env")

def register_client():
    print("[1/4] Registering client with Robinhood Agent Gateway...")
    reg_data = json.dumps({
        "client_name": "Antigravity Agent 0",
        "redirect_uris": [REDIRECT_URI]
    }).encode("utf-8")
    req = urllib.request.Request(
        REGISTER_URL,
        data=reg_data,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        client_id = res["client_id"]
        print(f"      Client ID registered: {client_id}")
        return client_id

def generate_pkce():
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("utf-8").rstrip("=")
    digest = hashlib.sha256(verifier.encode("utf-8")).digest()
    challenge = base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")
    return verifier, challenge

def update_env(token_data, client_id):
    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    token_type = token_data.get("token_type", "Bearer")
    expires_in = token_data.get("expires_in", "N/A")

    lines = []
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()

    filtered = [l for l in lines if not l.startswith("ROBINHOOD_")]
    if filtered and not filtered[-1].endswith("\n"):
        filtered[-1] += "\n"

    filtered.append("\n# Robinhood Agent MCP\n")
    filtered.append(f'ROBINHOOD_CLIENT_ID="{client_id}"\n')
    filtered.append(f'ROBINHOOD_ACCESS_TOKEN="{access_token}"\n')
    if refresh_token:
        filtered.append(f'ROBINHOOD_REFRESH_TOKEN="{refresh_token}"\n')
    filtered.append(f'ROBINHOOD_TOKEN_TYPE="{token_type}"\n')

    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.writelines(filtered)
    print(f"[4/4] Successfully saved tokens to {ENV_PATH}!")
    print(f"      Expires in: {expires_in}s")

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    client_id = None
    code_verifier = None
    expected_state = None

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/callback":
            params = urllib.parse.parse_qs(parsed.query)
            code = params.get("code", [None])[0]
            error = params.get("error", [None])[0]

            if error:
                self.send_response(400)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(f"<h1>OAuth Error</h1><p>{error}</p>".encode("utf-8"))
                return

            if not code:
                self.send_response(400)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(b"<h1>Missing code parameter</h1>")
                return

            print("\n[3/4] Received authorization code from Robinhood! Exchanging for tokens...")
            token_payload = urllib.parse.urlencode({
                "grant_type": "authorization_code",
                "client_id": self.client_id,
                "code": code,
                "code_verifier": self.code_verifier,
                "redirect_uri": REDIRECT_URI
            }).encode("utf-8")

            token_req = urllib.request.Request(
                TOKEN_URL,
                data=token_payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

            try:
                with urllib.request.urlopen(token_req) as resp:
                    token_data = json.loads(resp.read().decode("utf-8"))
                    update_env(token_data, self.client_id)

                    self.send_response(200)
                    self.send_header("Content-Type", "text/html")
                    self.end_headers()
                    self.wfile.write(b"<h1>Robinhood Connected!</h1><p>You can close this tab and return to Antigravity.</p>")
                    sys.exit(0)
            except urllib.error.HTTPError as e:
                err_body = e.read().decode("utf-8")
                self.send_response(500)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(f"<h1>Token Exchange Error</h1><p>{err_body}</p>".encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

def main():
    client_id = register_client()
    verifier, challenge = generate_pkce()
    state = secrets.token_hex(16)

    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": "internal",
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "state": state
    }
    auth_url = "https://robinhood.com/oauth?" + urllib.parse.urlencode(params)

    OAuthCallbackHandler.client_id = client_id
    OAuthCallbackHandler.code_verifier = verifier
    OAuthCallbackHandler.expected_state = state

    print(f"\n[2/4] Click to authorize in your browser:\n{auth_url}\n")
    try:
        subprocess.run(["open", auth_url], check=False)
    except Exception:
        pass

    server = HTTPServer(("localhost", 8080), OAuthCallbackHandler)
    try:
        server.handle_request()
    except SystemExit:
        pass
    finally:
        server.server_close()

if __name__ == "__main__":
    main()
