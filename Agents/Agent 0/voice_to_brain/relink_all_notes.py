#!/usr/bin/env python3
import os
import re
import time
import json
import logging
import requests
from dotenv import load_dotenv

AGENT0_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.exists(os.path.join(AGENT0_DIR, ".env")):
    load_dotenv(os.path.join(AGENT0_DIR, ".env"))
else:
    load_dotenv(os.path.expanduser("~/Agents/Agent 0/.env"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

VAULT_BASE = os.path.expanduser(os.environ.get("OBSIDIAN_VAULT_PATH", "~/Documents/Second Brain"))
PERMANENT_DIR = os.path.join(VAULT_BASE, "2-Permanent-Notes")
if not os.path.exists(PERMANENT_DIR) and os.path.exists(os.path.join(VAULT_BASE, "02_Permanent_Notes")):
    PERMANENT_DIR = os.path.join(VAULT_BASE, "02_Permanent_Notes")

CHROMADB_URL = os.environ.get("CHROMADB_URL", "http://localhost:8085")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_FREE_API_KEY", "")


def get_valid_vault_filenames():
    valid = set()
    if os.path.exists(PERMANENT_DIR):
        for f in os.listdir(PERMANENT_DIR):
            if f.endswith(".md"):
                valid.add(f.replace(".md", ""))
    return valid


def search_chromadb(query_text, n_results=10):
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
                header_body = line.replace("--- [VAULT NOTE]: ", "")
                fname = header_body.split(".md")[0].strip()
                if fname:
                    filenames.append(fname)
            elif line.startswith("--- FILE: ") and line.endswith(" ---"):
                fname = line.replace("--- FILE: ", "").replace(" ---", "").replace(".md", "").strip()
                if fname:
                    filenames.append(fname)
        return filenames
    except Exception as e:
        logging.error(f"ChromaDB search error: {e}")
        return []


def generate_tags(filename, content):
    if not GEMINI_API_KEY or GEMINI_API_KEY.startswith("YOUR_"):
        return ["note"]
    prompt = f"""You are formatting a note for an Obsidian vault. Given the note content below, return ONLY valid JSON (no markdown fences) with these fields:
- "tags": an array of 3-5 lowercase hierarchical or kebab-case tags

Note filename: {filename}
Note content:
{content[:2000]}
"""
    for model_name in ["gemini-3.5-flash-lite", "gemini-flash-lite-latest", "gemini-3.5-flash"]:
        try:
            resp = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}",
                json={"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.2}},
                timeout=15
            )
            if resp.status_code != 200:
                continue
            result = resp.json()
            text = result["candidates"][0]["content"]["parts"][0]["text"].strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            if text.endswith("```"):
                text = text[:-3]
            parsed = json.loads(text.strip())
            return parsed.get("tags", ["note"])
        except Exception:
            continue
    return ["note"]


def strip_frontmatter_and_connections(content):
    content_clean = content
    if content_clean.startswith("---"):
        parts = content_clean.split("---", 2)
        if len(parts) >= 3:
            content_clean = parts[2]

    if "## Semantic Connections" in content_clean:
        content_clean = content_clean.split("## Semantic Connections")[0]

    return content_clean.strip()


def process_file(filepath):
    filename = os.path.basename(filepath)
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            full_raw_content = f.read()
    except Exception as e:
        logging.error(f"Failed to read {filename}: {e}")
        return False

    body_text = strip_frontmatter_and_connections(full_raw_content)
    if not body_text:
        return False

    similar_files = search_chromadb(body_text[:1000], n_results=10)
    valid_filenames = get_valid_vault_filenames()

    current_basename = filename.replace(".md", "")
    verified_links = []
    for f in similar_files:
        cand_base = f.replace(".md", "")
        if cand_base in valid_filenames and cand_base != current_basename:
            if cand_base not in verified_links:
                verified_links.append(cand_base)
        if len(verified_links) >= 5:
            break

    tags = generate_tags(filename, body_text)
    tags_yaml = "\n".join([f"  - {t}" for t in tags])

    date_str = time.strftime("%Y-%m-%d")
    date_match = re.search(r"date:\s*([0-9]{4}-[0-9]{2}-[0-9]{2})", full_raw_content)
    if date_match:
        date_str = date_match.group(1)

    frontmatter = f"---\ndate: {date_str}\ntags:\n{tags_yaml}\n---\n\n"
    links_section = f"\n\n## Semantic Connections\n" + "\n".join([f"- [[{link}]]" for link in verified_links]) if verified_links else ""
    final_content = frontmatter + body_text + links_section

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(final_content)
        logging.info(f"Successfully relinked {filename} ({len(verified_links)} connections)")
        return True
    except Exception as e:
        logging.error(f"Failed to rewrite {filename}: {e}")
        return False


def relink_all():
    if not os.path.exists(PERMANENT_DIR):
        logging.error(f"Permanent directory not found: {PERMANENT_DIR}")
        return
    valid_files = [f for f in os.listdir(PERMANENT_DIR) if f.endswith(".md")]

    missing_files = []
    for f in valid_files:
        filepath = os.path.join(PERMANENT_DIR, f)
        try:
            with open(filepath, "r", encoding="utf-8") as fh:
                content = fh.read()
            if "## Semantic Connections" not in content:
                missing_files.append(f)
        except Exception:
            pass

    logging.info(f"Starting relink of {len(missing_files)} notes missing semantic connections...")
    success_count = 0
    for filename in missing_files:
        filepath = os.path.join(PERMANENT_DIR, filename)
        if process_file(filepath):
            success_count += 1
    logging.info(f"Completed relinking: {success_count}/{len(missing_files)} files updated.")


if __name__ == "__main__":
    relink_all()
