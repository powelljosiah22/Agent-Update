#!/usr/bin/env python3
import os
import sys
import time
import json
import logging
import subprocess
import requests
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

VENV_PYTHON = os.path.join(BASE_DIR, ".venv/bin/python")
CHROMADB_VENV_PYTHON = os.path.join(BASE_DIR, "mcp/obsidian_search/venv/bin/python")
CHROMADB_DAEMON = os.path.join(BASE_DIR, "mcp/obsidian_search/daemon.py")
BRAIN_DAEMON = os.path.join(BASE_DIR, "voice_to_brain/brain_daemon.py")
HEALTH_FILE = os.path.join(BASE_DIR, "voice_to_brain/.daemon_health.json")
CHROMADB_URL = os.environ.get("CHROMADB_URL", "http://localhost:8085")
VAULT_BASE = os.path.expanduser(os.environ.get("OBSIDIAN_VAULT_PATH", "~/Documents/Second Brain"))

def check_chromadb():
    try:
        resp = requests.post(CHROMADB_URL, json={"query": "healthcheck", "n_results": 1}, timeout=3)
        return resp.status_code == 200
    except Exception:
        return False

def start_chromadb():
    logging.warning("ChromaDB is offline. Attempting automatic restart...")
    try:
        daemon_log = os.path.join(BASE_DIR, "mcp/obsidian_search/daemon.log")
        with open(daemon_log, "a") as f:
            subprocess.Popen(
                [CHROMADB_VENV_PYTHON, CHROMADB_DAEMON],
                cwd=os.path.join(BASE_DIR, "mcp/obsidian_search"),
                stdout=f,
                stderr=f,
                start_new_session=True
            )
        time.sleep(3)
        if check_chromadb():
            logging.info("ChromaDB daemon successfully restarted.")
            return True
        else:
            logging.error("ChromaDB failed to start.")
            return False
    except Exception as e:
        logging.error(f"Error starting ChromaDB: {e}")
        return False

def check_brain_daemon():
    try:
        res = subprocess.run(["pgrep", "-f", "voice_to_brain/brain_daemon.py"], capture_output=True, text=True)
        if res.returncode != 0:
            return False

        inbox_path = os.path.join(VAULT_BASE, "1-Inbox")
        if os.path.exists(inbox_path):
            os.listdir(inbox_path)
        return True
    except Exception as e:
        logging.warning(f"Brain daemon healthcheck failed due to permission/access issue: {e}")
        subprocess.run(["pkill", "-f", "voice_to_brain/brain_daemon.py"])
        return False

def run_brain_daemon():
    if check_brain_daemon():
        logging.info("Brain daemon is already running.")
        return True, "Already running"

    logging.warning("Brain daemon is offline. Attempting automatic restart...")
    try:
        log_file = os.path.join(BASE_DIR, "voice_to_brain/brain_daemon.log")
        with open(log_file, "a") as f:
            subprocess.Popen(
                [VENV_PYTHON, BRAIN_DAEMON],
                cwd=BASE_DIR,
                stdout=f,
                stderr=subprocess.STDOUT,
                start_new_session=True
            )
        time.sleep(3)
        if check_brain_daemon():
            logging.info("Brain daemon successfully restarted.")
            return True, "Started successfully"
        else:
            logging.error("Brain daemon failed to start.")
            return False, "Failed to start"
    except Exception as e:
        logging.error(f"Error starting Brain daemon: {e}")
        return False, str(e)

def update_health_log(chroma_ok, daemon_ok, details=""):
    health_data = {
        "timestamp": time.time(),
        "datetime": time.strftime("%Y-%m-%d %H:%M:%S"),
        "chromadb_status": "ONLINE" if chroma_ok else "OFFLINE",
        "brain_daemon_status": "SUCCESS" if daemon_ok else "FAILED",
        "details": details
    }
    try:
        with open(HEALTH_FILE, "w", encoding="utf-8") as f:
            json.dump(health_data, f, indent=2)
    except Exception as e:
        logging.error(f"Failed to update health log: {e}")

if __name__ == "__main__":
    logging.info("--- Starting Infrastructure Watchdog Check ---")
    chroma_online = check_chromadb()
    if not chroma_online:
        chroma_online = start_chromadb()

    daemon_success, output = run_brain_daemon()
    update_health_log(chroma_online, daemon_success, output)
    logging.info("--- Watchdog Check Completed ---")
