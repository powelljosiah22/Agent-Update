#!/usr/bin/env python3
import os
import sys
import re
import time
import json
import logging
import shutil
import mimetypes
import subprocess
import threading
import urllib.request
import urllib.parse
import requests
from dotenv import load_dotenv
from google import genai
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

AGENT0_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.exists(os.path.join(AGENT0_DIR, ".env")):
    load_dotenv(os.path.join(AGENT0_DIR, ".env"))
else:
    load_dotenv(os.path.expanduser("~/Agents/Agent 0/.env"))

VAULT_BASE = os.path.expanduser(os.environ.get("OBSIDIAN_VAULT_PATH", "~/Documents/Second Brain"))
CLASS_FOLDERS_BASE = os.path.expanduser(os.environ.get("CLASS_FOLDERS_PATH", "~/Documents/Class Folders"))


def _resolve_vault_subdir(vault_base, preferred, alt):
    p_pref = os.path.join(vault_base, preferred)
    p_alt = os.path.join(vault_base, alt)
    if os.path.exists(p_pref):
        return p_pref
    if os.path.exists(p_alt):
        return p_alt
    return p_pref


WATCH_DIR = _resolve_vault_subdir(VAULT_BASE, "1-Inbox", "00_Inbox")
PERMANENT_DIR = _resolve_vault_subdir(VAULT_BASE, "2-Permanent-Notes", "02_Permanent_Notes")
ARCHIVE_DIR = os.path.join(VAULT_BASE, "3-Archive")
CHROMADB_URL = os.environ.get("CHROMADB_URL", "http://localhost:8085")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_FREE_API_KEY", "")
DEFAULT_USER_EMAIL = os.environ.get("USER_EMAIL", "")
GOOGLE_CREDS_DIR = os.path.expanduser(os.environ.get("GOOGLE_CREDS_DIR", os.path.join(AGENT0_DIR, "credentials")))

client = genai.Client(api_key=GEMINI_API_KEY, http_options={"timeout": 120000}) if (GEMINI_API_KEY and not GEMINI_API_KEY.startswith("YOUR_")) else None


def extract_text_from_gdoc(gdoc_path):
    try:
        with open(gdoc_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        doc_id = data.get("doc_id")
        email = data.get("email") or DEFAULT_USER_EMAIL
        if not doc_id:
            logging.error(f"No doc_id found in {gdoc_path}")
            return None

        token_file = os.path.join(GOOGLE_CREDS_DIR, f".oauth2.{email}.json")
        gauth_file = os.path.join(GOOGLE_CREDS_DIR, "gauth.json")

        if not os.path.exists(token_file) or not os.path.exists(gauth_file):
            logging.error("Google Drive OAuth credentials not found for .gdoc export.")
            return None

        with open(token_file, "r", encoding="utf-8") as f:
            token_data = json.load(f)
        with open(gauth_file, "r", encoding="utf-8") as f:
            raw_gauth = json.load(f)
            gauth_data = raw_gauth.get("installed") or raw_gauth.get("web") or {}

        refresh_token = token_data.get("refresh_token")
        post_data = urllib.parse.urlencode({
            "client_id": gauth_data["client_id"],
            "client_secret": gauth_data["client_secret"],
            "refresh_token": refresh_token,
            "grant_type": "refresh_token"
        }).encode("utf-8")

        req = urllib.request.Request("https://oauth2.googleapis.com/token", data=post_data)
        with urllib.request.urlopen(req, timeout=10) as resp:
            token_resp = json.loads(resp.read().decode("utf-8"))
            access_token = token_resp["access_token"]

        export_url = f"https://www.googleapis.com/drive/v3/files/{doc_id}/export?mimeType=text/plain"
        req_export = urllib.request.Request(export_url, headers={"Authorization": f"Bearer {access_token}"})
        with urllib.request.urlopen(req_export, timeout=15) as resp:
            content = resp.read().decode("utf-8")
            return content.strip()
    except Exception as e:
        logging.error(f"Failed to extract .gdoc content from {gdoc_path}: {e}")
        return None


def get_valid_vault_filenames():
    valid = set()
    if os.path.exists(PERMANENT_DIR):
        for f in os.listdir(PERMANENT_DIR):
            if f.endswith(".md"):
                valid.add(f.replace(".md", ""))
    return valid


def search_chromadb(query_text, n_results=5):
    try:
        resp = requests.post(
            CHROMADB_URL,
            json={"query": query_text, "n_results": n_results, "target": "vault"},
            timeout=10
        )
        if resp.status_code != 200:
            return []

        result_text = resp.json().get("result", "")
        filenames = []
        for line in result_text.split("\n"):
            if line.startswith("--- [VAULT NOTE]: "):
                # Header format: --- [VAULT NOTE]: Filename.md (Lines X-Y of Z) | Path: ... ---
                header_body = line.replace("--- [VAULT NOTE]: ", "")
                fname = header_body.split(".md")[0].strip()
                if fname:
                    filenames.append(fname)
        return filenames
    except Exception as e:
        logging.error(f"ChromaDB search error: {e}")
        return []


def generate_tags_and_summary(content, default_name=""):
    if not client:
        return ["note"], [], default_name
    prompt = f"""You are an executive assistant formatting a note for an Obsidian Zettelkasten vault.
Given the note content below, return ONLY valid JSON (no markdown fences) with these fields:
- "title": a concise, descriptive title in CamelCase or Title_Case suitable for an Obsidian note filename (e.g. "Phonetics_Articulatory_Notes", "Romans_8_Study_Notes"). If the original file name '{default_name}' is already descriptive and not generic like 'Untitled document', you may use that.
- "tags": an array of 3-5 hierarchical nested tags using forward slashes (e.g. "academics/coursework", "theology/biblical-studies", "personal/planning").
- "summary": an array of 2 bullet point strings summarizing the core essence of the note.

Note content:
{content[:2000]}
"""
    for m in ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.8-flash", "gemini-3.6-flash", "gemini-3.5-flash"]:
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=m,
                    contents=prompt,
                    config={"temperature": 0.2}
                )
                text = response.text.strip()
                if text.startswith("```"):
                    text = text.split("\n", 1)[1] if "\n" in text else text[3:]
                if text.endswith("```"):
                    text = text[:-3]
                parsed = json.loads(text.strip())
                title = parsed.get("title", default_name).strip()
                tags = parsed.get("tags", ["note"])
                summary = parsed.get("summary", [])
                return tags, summary, title
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "503" in err_str or "UNAVAILABLE" in err_str:
                    time.sleep(2)
                else:
                    break
    logging.error("All models failed for tag & summary generation.")
    return ["note"], [], default_name


def process_file_with_gemini(filepath, mime_type):
    if not client:
        logging.error("Gemini client not initialized (GEMINI_API_KEY missing).")
        return None
    logging.info(f"Preparing {os.path.basename(filepath)} for Gemini processing...")
    staging_dir = "/tmp/brain_inbox_staging"
    os.makedirs(staging_dir, exist_ok=True)
    staged_path = os.path.join(staging_dir, f"{int(time.time())}_{os.path.basename(filepath)}")

    copied = False
    for attempt in range(5):
        try:
            shutil.copy2(filepath, staged_path)
            copied = True
            break
        except (OSError, PermissionError) as e:
            if attempt < 4:
                logging.warning(f"File {os.path.basename(filepath)} locked by OS/CloudStorage ({e}). Retrying copy in 2s ({attempt+1}/5)...")
                time.sleep(2)
            else:
                logging.error(f"Failed to copy locked file {filepath} to staging after 5 attempts: {e}")
                return None

    upload_target = staged_path if copied else filepath

    try:
        logging.info(f"Uploading {os.path.basename(filepath)} to Gemini File API...")
        uploaded_file = client.files.upload(file=upload_target, config={"mime_type": mime_type})

        while uploaded_file.state == "PROCESSING":
            logging.info("Waiting for file processing...")
            time.sleep(2)
            uploaded_file = client.files.get(name=uploaded_file.name)

        if uploaded_file.state == "FAILED":
            logging.error("File processing failed.")
            return None

        if mime_type.startswith("audio/") or mime_type.startswith("video/"):
            prompt = (
                "Transcribe this audio/video verbatim. Do not summarize. "
                "Output the result in a clean, highly readable Markdown format. "
                "Use Markdown headings (#, ##) and paragraphs logically if the speaker changes topics, "
                "but keep the text word-for-word. Do NOT wrap the output in markdown code fences."
            )
        else:
            prompt = (
                "Extract the text from this document verbatim. Do NOT summarize or shorten the content. "
                "Preserve and apply Markdown formatting (#, ##, ### for headings, * or - for bullets, "
                "**bold** or *italic* where emphasized, and standard Markdown table syntax). "
                "Do NOT wrap the output in markdown code fences. Output raw markdown."
            )

        models_to_try = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.8-flash", "gemini-3.6-flash", "gemini-3.5-flash"]
        response = None
        for m in models_to_try:
            for attempt in range(3):
                try:
                    response = client.models.generate_content(
                        model=m,
                        contents=[uploaded_file, prompt]
                    )
                    if response and hasattr(response, "text") and response.text:
                        break
                except Exception as err:
                    err_str = str(err)
                    if "429" in err_str or "503" in err_str or "UNAVAILABLE" in err_str:
                        time.sleep(2)
                    else:
                        break
            if response and hasattr(response, "text") and response.text:
                break

        if not response or not hasattr(response, "text") or not response.text:
            logging.error(f"Failed to generate content for {os.path.basename(filepath)} across all models.")
            return None

        markdown_text = response.text.strip()
        if markdown_text.startswith("```markdown"):
            markdown_text = markdown_text[11:-3].strip()
        elif markdown_text.startswith("```"):
            markdown_text = markdown_text[3:-3].strip()

        try:
            client.files.delete(name=uploaded_file.name)
        except Exception:
            pass

        return markdown_text
    except Exception as e:
        logging.error(f"Error processing with Gemini: {e}")
        return None
    finally:
        if staged_path and os.path.exists(staged_path):
            try:
                os.remove(staged_path)
            except Exception:
                pass


def process_inbox_file(filepath):
    filename = os.path.basename(filepath)
    logging.info(f"Processing inbox item: {filename}")

    try:
        size1 = os.path.getsize(filepath)
        time.sleep(1)
        size2 = os.path.getsize(filepath)
        if size1 != size2:
            logging.info(f"File {filename} is still writing to disk. Will retry in next sweep.")
            return False
    except OSError as e:
        logging.info(f"File {filename} currently locked or syncing ({e}). Will retry in next sweep.")
        return False

    mime_type, _ = mimetypes.guess_type(filepath)
    content = ""

    if filename.endswith(".md") or filename.endswith(".txt"):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            logging.error(f"Failed to read text file {filename}: {e}")
            return False
    elif filename.endswith(".gdoc"):
        logging.info(f"Extracting Google Doc content via Drive API for {filename}...")
        content = extract_text_from_gdoc(filepath)
        if not content:
            return False
    else:
        lower_name = filename.lower()
        if lower_name.endswith(".m4a"): mime_type = "audio/mp4"
        elif lower_name.endswith(".mp3"): mime_type = "audio/mp3"
        elif lower_name.endswith(".wav"): mime_type = "audio/wav"
        elif lower_name.endswith(".aac"): mime_type = "audio/aac"
        elif lower_name.endswith(".ogg"): mime_type = "audio/ogg"
        elif lower_name.endswith(".docx"): mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        elif lower_name.endswith(".pptx"): mime_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        elif lower_name.endswith(".pdf"): mime_type = "application/pdf"
        elif not mime_type:
            logging.warning(f"Unknown mime type for {filename}. Skipping.")
            return False

        content = process_file_with_gemini(filepath, mime_type)

    if not content or not content.strip():
        logging.warning(f"No content extracted for {filename}. Skipping.")
        return False

    similar_files = search_chromadb(content[:1000])
    valid_filenames = get_valid_vault_filenames()
    base_name = os.path.splitext(filename)[0]

    tags, summary_bullets, gen_title = generate_tags_and_summary(content, default_name=base_name)
    tags_yaml = "\n".join([f"  - {t}" for t in tags])

    _, ext = os.path.splitext(filename)
    is_audio_video = ext.lower() in (".m4a", ".mp3", ".wav", ".ogg", ".aac", ".flac", ".mp4", ".mov", ".webm", ".mkv")

    generic_patterns = [
        r"^untitled", r"^my recording", r"^new recording", r"^voice[\s_]?\d*",
        r"^audio[\s_]?\d*", r"^recording[\s_]?\d*", r"^note[\s_]?\d*$",
        r"^document[\s_]?\d*$", r"^img[_\s]?\d+", r"^screenshot[\s_]?\d*", r"^\d+$",
    ]
    is_generic = any(re.match(pat, base_name.lower().strip()) for pat in generic_patterns)

    if (is_audio_video or is_generic) and gen_title:
        clean_title = "".join(c for c in gen_title if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
        if clean_title:
            base_name = clean_title

    # Cross-platform filename sanitization (macOS, Windows, Android DriveSync, FAT32)
    base_name = re.sub(r"[:|/\\]+", " - ", base_name)
    base_name = re.sub(r'[*?"<>]+', "", base_name).strip()
    base_name = re.sub(r"\s+", " ", base_name).strip()

    verified_links = [f for f in similar_files if f in valid_filenames and f != base_name][:5]

    summary_section = ""
    if summary_bullets:
        bullets_text = "\n".join([f"> - {b}" for b in summary_bullets])
        summary_section = f"> [!NOTE] Executive Summary\n{bullets_text}\n\n"

    frontmatter = f"---\ndate: {time.strftime('%Y-%m-%d')}\ntags:\n{tags_yaml}\n---\n\n"
    links_section = f"\n\n## Semantic Connections\n" + "\n".join([f"- [[{link}]]" for link in verified_links]) if verified_links else ""
    final_content = frontmatter + summary_section + content + links_section

    os.makedirs(PERMANENT_DIR, exist_ok=True)
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    dest_filename = f"{base_name}.md"
    dest_path = os.path.join(PERMANENT_DIR, dest_filename)

    try:
        with open(dest_path, "w", encoding="utf-8") as f:
            f.write(final_content)

        _, extension = os.path.splitext(filename)
        archive_path = os.path.join(ARCHIVE_DIR, f"{base_name}_original_{int(time.time())}{extension}")
        shutil.move(filepath, archive_path)

        logging.info(f"Successfully processed {filename} -> {dest_filename}")
        return True
    except Exception as e:
        logging.error(f"Failed to save note or archive {filename}: {e}")
        return False


def process_class_folder_raw_files():
    if not CLASS_FOLDERS_BASE or not os.path.exists(CLASS_FOLDERS_BASE):
        return 0

    # Snapshot pending raw files across all 1_* folders.
    # pipeline_parser.py processes all pending files in a single batch run.
    pending = []
    for root, dirs, files in os.walk(CLASS_FOLDERS_BASE):
        if os.path.basename(root).startswith("1_"):
            course = os.path.basename(os.path.dirname(root))
            for f in files:
                if not f.startswith(".") and f.lower().endswith((".pptx", ".pdf", ".docx", ".xlsx", ".csv", ".txt", ".md", ".jpg", ".jpeg", ".png")):
                    pending.append((course, f, os.path.join(root, f)))

    if not pending:
        return 0

    parser_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pipeline_parser.py")
    sys_python = sys.executable

    for course, f, _ in pending:
        logging.info(f"Auto-parsing raw class file: {course} / {f}")

    try:
        # 900s hard timeout so a hung API call can never freeze the daemon
        res = subprocess.run([sys_python, parser_script], capture_output=True, text=True, timeout=900)
        if res.returncode != 0:
            logging.error(f"Pipeline parser exited {res.returncode}: {res.stderr[-1500:]}")
    except subprocess.TimeoutExpired:
        logging.error("Pipeline parser timed out after 900s; will retry next sweep.")
        res = None
    except Exception as e:
        logging.error(f"Error executing pipeline_parser.py: {e}")
        return 0

    out_lines = (res.stdout.splitlines() if res and res.stdout else [])
    processed_count = 0
    for course, f, path in pending:
        if not os.path.exists(path):
            class_folder = os.path.dirname(os.path.dirname(path))
            review = os.path.join(class_folder, "4_Needs_Review", f)
            if os.path.exists(review):
                logging.error(f"QUARANTINED after repeated failures: {course}/4_Needs_Review/{f}")
            else:
                processed_count += 1
                logging.info(f"Successfully auto-parsed class material: {f}")
        else:
            detail = next((l.strip() for l in out_lines if f in l and ("WARNING" in l or "Error" in l)), "no detail")
            logging.warning(f"Parse FAILED (file retained for retry): {course}/{f} | {detail}")
    return processed_count


class BrainEventHandler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        self.lock = threading.Lock()

    def process_event(self, filepath):
        with self.lock:
            basename = os.path.basename(filepath)
            if basename.startswith(".") or "_original_" in basename or basename.endswith(".tmp"):
                return

            time.sleep(1)

            if filepath.startswith(WATCH_DIR):
                if os.path.isfile(filepath):
                    if process_inbox_file(filepath):
                        self.trigger_sync()
            elif "1_" in filepath:
                if os.path.isfile(filepath):
                    processed = process_class_folder_raw_files()
                    if processed > 0:
                        self.trigger_sync()

    def on_created(self, event):
        if not event.is_directory:
            self.process_event(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self.process_event(event.src_path)

    def trigger_sync(self):
        try:
            sys_python = os.environ.get("PYTHON_EXEC", os.path.join(AGENT0_DIR, "mcp/obsidian_search/venv/bin/python"))
            sync_script = os.environ.get("SYNC_SCRIPT", os.path.join(AGENT0_DIR, "mcp/obsidian_search/sync_database.py"))
            if os.path.exists(sync_script):
                subprocess.run([sys_python, sync_script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                logging.info("ChromaDB vector database synced successfully.")
        except Exception as e:
            logging.error(f"Error auto-syncing ChromaDB database: {e}")


if __name__ == "__main__":
    os.makedirs(WATCH_DIR, exist_ok=True)
    os.makedirs(PERMANENT_DIR, exist_ok=True)
    os.makedirs(ARCHIVE_DIR, exist_ok=True)

    logging.info("Performing initial startup sweep...")
    files_processed = 0
    try:
        for filename in os.listdir(WATCH_DIR):
            if not filename.startswith(".") and "_original_" not in filename:
                filepath = os.path.join(WATCH_DIR, filename)
                if os.path.isfile(filepath):
                    if process_inbox_file(filepath):
                        files_processed += 1
    except Exception as e:
        logging.warning(f"Initial inbox sweep notice: {e}")

    try:
        files_processed += process_class_folder_raw_files()
    except Exception as e:
        logging.error(f"Error during class materials initial sweep: {e}")

    event_handler = BrainEventHandler()
    if files_processed > 0:
        event_handler.trigger_sync()

    logging.info("Initial sweep complete. Starting real-time watchdog daemon...")
    observer = Observer()
    try:
        observer.schedule(event_handler, WATCH_DIR, recursive=False)
    except Exception as e:
        logging.warning(f"Unable to schedule watchdog on {WATCH_DIR}: {e}")

    if os.path.exists(CLASS_FOLDERS_BASE):
        try:
            observer.schedule(event_handler, CLASS_FOLDERS_BASE, recursive=True)
        except Exception as e:
            logging.warning(f"Unable to schedule watchdog on {CLASS_FOLDERS_BASE}: {e}")

    observer.start()

    try:
        while True:
            time.sleep(45)

            # 1. Periodic Inbox Sweep
            try:
                if os.path.exists(WATCH_DIR):
                    inbox_files = [f for f in os.listdir(WATCH_DIR) if not f.startswith(".") and not f.endswith(".tmp") and "_original_" not in f]
                    if inbox_files:
                        with event_handler.lock:
                            processed_any = False
                            for filename in inbox_files:
                                fpath = os.path.join(WATCH_DIR, filename)
                                if os.path.isfile(fpath):
                                    if process_inbox_file(fpath):
                                        processed_any = True
                            if processed_any:
                                event_handler.trigger_sync()
            except Exception as e:
                logging.error(f"Error during periodic inbox sweep: {e}")

            # 2. Periodic Class Folders Sweep
            try:
                with event_handler.lock:
                    processed_class = process_class_folder_raw_files()
                    if processed_class > 0:
                        event_handler.trigger_sync()
            except Exception as e:
                logging.error(f"Error during periodic class folder sweep: {e}")

            # 3. Daily Full Vault Graph Resync (Once every 24 hours)
            last_resync_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".last_daily_resync")
            now = time.time()
            should_resync = not os.path.exists(last_resync_file)
            if not should_resync:
                try:
                    if (now - os.path.getmtime(last_resync_file)) > 86400:
                        should_resync = True
                except Exception:
                    should_resync = True

            if should_resync:
                try:
                    sys_python = os.path.join(AGENT0_DIR, "mcp/obsidian_search/venv/bin/python")
                    relink_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "relink_all_notes.py")
                    if os.path.exists(relink_script):
                        subprocess.run([sys_python, relink_script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        with open(last_resync_file, "w") as f:
                            f.write(str(now))
                        logging.info("Daily full vault vector resync completed successfully.")
                except Exception as e:
                    logging.error(f"Daily resync error: {e}")
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
