#!/usr/bin/env python3
"""
Robinhood Agent MCP Bridge
Forwards stdio JSON-RPC messages from Antigravity to https://agent.robinhood.com/mcp/trading
Handles OAuth Bearer authentication, SSE parsing, and token auto-refresh.
"""
import sys
import json
import os
import urllib.request
import urllib.parse
import urllib.error

ENV_PATH = os.path.expanduser("~/Agents/Agent 0/.env")
URL = "https://agent.robinhood.com/mcp/trading"
TOKEN_URL = "https://api.robinhood.com/oauth2/token/"

def read_env():
    env_vars = {}
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line and not line.strip().startswith("#"):
                    k, v = line.strip().split("=", 1)
                    env_vars[k.strip()] = v.strip().strip('"').strip("'")
    return env_vars

def refresh_tokens():
    env_vars = read_env()
    refresh_token = env_vars.get("ROBINHOOD_REFRESH_TOKEN")
    if not refresh_token:
        return None

    client_id = env_vars.get("ROBINHOOD_CLIENT_ID") or "LtLiNmbs9owbYfWgBlC68Z2V-gemini"
    data = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id
    }).encode("utf-8")

    req = urllib.request.Request(TOKEN_URL, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req) as resp:
            token_data = json.loads(resp.read().decode("utf-8"))
            new_access = token_data.get("access_token")
            new_refresh = token_data.get("refresh_token", refresh_token)

            lines = []
            with open(ENV_PATH, "r", encoding="utf-8") as f:
                lines = f.readlines()
            new_lines = []
            for l in lines:
                if l.startswith("ROBINHOOD_ACCESS_TOKEN="):
                    new_lines.append(f'ROBINHOOD_ACCESS_TOKEN="{new_access}"\n')
                elif l.startswith("ROBINHOOD_REFRESH_TOKEN="):
                    new_lines.append(f'ROBINHOOD_REFRESH_TOKEN="{new_refresh}"\n')
                else:
                    new_lines.append(l)
            with open(ENV_PATH, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
            return new_access
    except Exception as e:
        sys.stderr.write(f"Token refresh failed: {e}\n")
        return None

class RobinhoodBridge:
    def __init__(self):
        self.session_id = None

    def post_rpc(self, msg, retried=False):
        env_vars = read_env()
        token = env_vars.get("ROBINHOOD_ACCESS_TOKEN", "")

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "Authorization": f"Bearer {token}"
        }
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id

        data = json.dumps(msg).encode("utf-8")
        req = urllib.request.Request(URL, data=data, headers=headers)

        try:
            with urllib.request.urlopen(req) as resp:
                if "Mcp-Session-Id" in resp.headers:
                    self.session_id = resp.headers["Mcp-Session-Id"]
                resp_text = resp.read().decode("utf-8")
                for line in resp_text.splitlines():
                    if line.startswith("data:"):
                        return json.loads(line[5:].strip())
                return None
        except urllib.error.HTTPError as e:
            if e.code == 401 and not retried:
                sys.stderr.write("401 Unauthorized received, attempting token refresh...\n")
                new_token = refresh_tokens()
                if new_token:
                    return self.post_rpc(msg, retried=True)
            err_body = e.read().decode("utf-8")
            if isinstance(msg, dict) and "id" in msg:
                return {
                    "jsonrpc": "2.0",
                    "id": msg["id"],
                    "error": {
                        "code": -32000,
                        "message": f"Robinhood API error {e.code}: {err_body}"
                    }
                }
            return None

    def run(self):
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except Exception:
                continue

            resp = self.post_rpc(msg)
            if resp is not None:
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()

if __name__ == "__main__":
    bridge = RobinhoodBridge()
    bridge.run()
