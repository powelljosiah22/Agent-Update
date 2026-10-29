#!/usr/bin/env python3
"""
sync_database.py — Crash-Resilient ChromaDB Vector Sync
Uses subprocess isolation per-batch so that if ONNX/ChromaDB segfaults
during embedding on Apple Silicon, only the disposable child process dies.
"""
import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
os.environ["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"

import sys
import glob
import json
import re
import signal
import subprocess
import datetime

try:
    from dotenv import load_dotenv
    if os.path.exists(".env"):
        load_dotenv(".env")
    else:
        load_dotenv(os.path.expanduser("~/Agents/Agent 0/.env"))
except ImportError:
    pass

LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug_sync.log")


def log(msg):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{datetime.datetime.now()} - {msg}\n")


def chunk_text(text, max_chars=600, overlap=120):
    if len(text) <= max_chars:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = start + max_chars
        chunks.append(text[start:end])
        start += (max_chars - overlap)
    return chunks


WORKER_SCRIPT = r'''
import os, sys, json, signal
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

try:
    os.nice(19)
except Exception:
    pass

import chromadb
from chromadb.utils import embedding_functions

def main():
    data = json.loads(sys.stdin.read())
    db_path = data["db_path"]
    collection_name = data["collection_name"]
    docs = data["docs"]
    ids = data["ids"]
    metas = data["metas"]

    client = chromadb.PersistentClient(path=db_path)
    emb_fn = embedding_functions.DefaultEmbeddingFunction()
    coll = client.get_or_create_collection(name=collection_name, embedding_function=emb_fn)

    coll.add(documents=docs, metadatas=metas, ids=ids)
    print(json.dumps({"status": "ok", "count": len(docs)}))
    sys.stdout.flush()
    os.kill(os.getpid(), signal.SIGKILL)

if __name__ == "__main__":
    main()
'''


def run_batch_in_subprocess(db_path, collection_name, docs, ids, metas, python_exec):
    payload = json.dumps({
        "db_path": db_path,
        "collection_name": collection_name,
        "docs": docs,
        "ids": ids,
        "metas": metas,
    })

    try:
        proc = subprocess.run(
            [python_exec, "-c", WORKER_SCRIPT],
            input=payload,
            capture_output=True,
            text=True,
            timeout=120,
            env={
                **os.environ,
                "OBJC_DISABLE_INITIALIZE_FORK_SAFETY": "YES",
            }
        )
        if proc.stdout.strip():
            try:
                result = json.loads(proc.stdout.strip())
                if result.get("status") == "ok":
                    return True
            except json.JSONDecodeError:
                pass
        if proc.returncode in (-9, -signal.SIGKILL, 137):
            return True
        if proc.stderr.strip():
            log(f"Worker stderr: {proc.stderr.strip()[:200]}")
        return False
    except subprocess.TimeoutExpired:
        log(f"Batch timed out for {collection_name}")
        return False
    except Exception as e:
        log(f"Batch subprocess error: {e}")
        return False


def get_db_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_db")


def get_python_exec():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "venv", "bin", "python")


def resolve_notes_dir(vault_base):
    for cand in ("2-Permanent-Notes", "02_Permanent_Notes"):
        p = os.path.join(vault_base, cand)
        if os.path.exists(p):
            return p
    return os.path.join(vault_base, "2-Permanent-Notes")


def sync_obsidian_notes(reindex_files=None):
    vault_base = os.path.expanduser(os.environ.get("OBSIDIAN_VAULT_PATH", "~/Documents/Second Brain"))
    notes_dir = resolve_notes_dir(vault_base)

    if not os.path.exists(notes_dir):
        log(f"Vault directory not found: {notes_dir}")
        return

    files = glob.glob(os.path.join(notes_dir, "*.md"))
    valid_filenames = set(os.path.basename(f) for f in files)
    reindex_filenames = set(reindex_files or [])

    records = get_existing_records("obsidian_notes")
    existing_ids = set(records.get("ids", []))
    metadatas = records.get("metadatas", [])

    chunks_to_prune = []
    for cid, meta in zip(records.get("ids", []), metadatas):
        parent = meta.get("parent_file") if meta and meta.get("parent_file") else cid.split("_sub")[0]
        if parent not in valid_filenames or parent in reindex_filenames:
            chunks_to_prune.append(cid)

    if chunks_to_prune:
        log(f"[Vault] Pruning {len(chunks_to_prune)} orphaned/stale chunks from ChromaDB...")
        prune_ids("obsidian_notes", chunks_to_prune)
        existing_ids.difference_update(chunks_to_prune)

    docs_to_add, ids_to_add, metas_to_add = [], [], []

    for f in files:
        filename = os.path.basename(f)
        try:
            with open(f, "r", encoding="utf-8") as file:
                content = file.read()
                if content.strip():
                    chunks = chunk_text(content, max_chars=500, overlap=100)
                    for i, chunk in enumerate(chunks):
                        chunk_id = f"{filename}_sub{i}"
                        if chunk_id not in existing_ids and filename not in existing_ids:
                            docs_to_add.append(chunk)
                            ids_to_add.append(chunk_id)
                            metas_to_add.append({"parent_file": filename, "sub_index": i})
        except Exception as e:
            log(f"[Vault] Error reading {filename}: {e}")

    if docs_to_add:
        total = len(docs_to_add)
        log(f"[Vault] Found {total} new chunks to index.")
        process_batches("obsidian_notes", docs_to_add, ids_to_add, metas_to_add)
        log("[Vault] Finished indexing vault notes.")
    else:
        log("[Vault] No new notes to index.")


def sync_class_materials(reindex_files=None):
    class_base = os.path.expanduser(os.environ.get("CLASS_FOLDERS_PATH", "~/Documents/Class Folders"))

    if not os.path.exists(class_base):
        log(f"Class materials directory not found: {class_base}")
        return

    # Walk recursively to support <CLASS_FOLDERS_PATH>/<COURSE>/2_Parsed_MD,
    # <CLASS_FOLDERS_PATH>/<SEMESTER>/<COURSE>/2_Parsed_MD, and 2_Parsed_Markdown
    all_files_with_course = []
    for root, dirs, files in os.walk(class_base):
        if os.path.basename(root) in ("2_Parsed_MD", "2_Parsed_Markdown"):
            course = os.path.basename(os.path.dirname(root)).upper().replace("-", "_").replace(" ", "_")
            for f in files:
                if f.endswith(".md") and not f.startswith("."):
                    all_files_with_course.append((os.path.join(root, f), course))

    reindex_filenames = set(reindex_files or [])
    records = get_existing_records("class_materials")
    existing_ids = set(records.get("ids", []))
    metadatas = records.get("metadatas", [])

    if reindex_filenames:
        chunks_to_prune = [
            cid for cid, meta in zip(records.get("ids", []), metadatas)
            if meta and meta.get("parent_file") in reindex_filenames
        ]
        if chunks_to_prune:
            prune_ids("class_materials", chunks_to_prune)
            existing_ids.difference_update(chunks_to_prune)

    docs_to_add, ids_to_add, metas_to_add = [], [], []

    for filepath, course in all_files_with_course:
        filename = os.path.basename(filepath)
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                content = file.read()
                if content.strip():
                    chunks = chunk_text(content, max_chars=600, overlap=120)
                    for i, chunk in enumerate(chunks):
                        chunk_id = f"{course}_{filename}_sub{i}"
                        if chunk_id not in existing_ids:
                            docs_to_add.append(chunk)
                            ids_to_add.append(chunk_id)

                            chap = ""
                            match_chap = re.search(r"(?i)(?:chapter|module|ch\.?)\s*(\d+)", filename)
                            if match_chap:
                                chap = str(int(match_chap.group(1)))

                            dtype = ""
                            pf_lower = filename.lower()
                            if any(k in pf_lower for k in ["slide", "ppt", "powerpoint", "notes"]):
                                dtype = "slide"
                            elif any(k in pf_lower for k in ["problem", "assignment", "hw", "hwk", "quiz", "exam", "mock", "study_guide", "study guide"]):
                                dtype = "problem"
                            elif any(k in pf_lower for k in ["textbook", "reading", "dalton", "harrington", "spiceland", "fundamentals_ch", "edition"]):
                                dtype = "textbook"

                            metas_to_add.append({
                                "parent_file": filename,
                                "course": course,
                                "file_path": filepath,
                                "sub_index": i,
                                "chapter": chap,
                                "document_type": dtype
                            })
        except Exception as e:
            log(f"[Class Materials] Error reading {filename}: {e}")

    if docs_to_add:
        total = len(docs_to_add)
        log(f"[Class Materials] Found {total} new chunks to index.")
        process_batches("class_materials", docs_to_add, ids_to_add, metas_to_add)
        log("[Class Materials] Finished indexing class materials.")
    else:
        log("[Class Materials] No new class materials to index.")


def get_existing_records(collection_name):
    worker = r'''
import os, sys, json, signal
os.environ["OMP_NUM_THREADS"] = "1"
import chromadb
db_path = sys.argv[1]
coll_name = sys.argv[2]
client = chromadb.PersistentClient(path=db_path)
try:
    coll = client.get_collection(coll_name)
    res = coll.get()
    print(json.dumps({"ids": res.get("ids", []), "metadatas": res.get("metadatas", [])}))
except Exception:
    print(json.dumps({"ids": [], "metadatas": []}))
sys.stdout.flush()
os.kill(os.getpid(), signal.SIGKILL)
'''
    try:
        proc = subprocess.run(
            [get_python_exec(), "-c", worker, get_db_path(), collection_name],
            capture_output=True, text=True, timeout=30,
            env={**os.environ, "OBJC_DISABLE_INITIALIZE_FORK_SAFETY": "YES"}
        )
        if proc.stdout.strip():
            return json.loads(proc.stdout.strip())
    except Exception as e:
        log(f"Error getting existing records for {collection_name}: {e}")
    return {"ids": [], "metadatas": []}


def prune_ids(collection_name, ids_to_delete):
    if not ids_to_delete:
        return
    worker = r'''
import os, sys, json, signal
os.environ["OMP_NUM_THREADS"] = "1"
import chromadb
db_path = sys.argv[1]
coll_name = sys.argv[2]
ids = json.loads(sys.stdin.read())
client = chromadb.PersistentClient(path=db_path)
try:
    coll = client.get_collection(coll_name)
    for i in range(0, len(ids), 500):
        coll.delete(ids=ids[i:i+500])
    print("OK")
except Exception as e:
    print(f"ERR: {e}")
sys.stdout.flush()
os.kill(os.getpid(), signal.SIGKILL)
'''
    try:
        subprocess.run(
            [get_python_exec(), "-c", worker, get_db_path(), collection_name],
            input=json.dumps(list(ids_to_delete)),
            capture_output=True, text=True, timeout=30,
            env={**os.environ, "OBJC_DISABLE_INITIALIZE_FORK_SAFETY": "YES"}
        )
    except Exception as e:
        log(f"Error pruning IDs for {collection_name}: {e}")


def process_batches(collection_name, docs, ids, metas, batch_size=10):
    import time
    db_path = get_db_path()
    python_exec = get_python_exec()
    total = len(docs)
    succeeded = 0
    failed = 0

    for i in range(0, total, batch_size):
        batch_docs = docs[i:i+batch_size]
        batch_ids = ids[i:i+batch_size]
        batch_metas = metas[i:i+batch_size]

        ok = run_batch_in_subprocess(db_path, collection_name, batch_docs, batch_ids, batch_metas, python_exec)
        time.sleep(0.01)
        if ok:
            succeeded += len(batch_docs)
        else:
            for j in range(len(batch_docs)):
                ok2 = run_batch_in_subprocess(db_path, collection_name,
                    [batch_docs[j]], [batch_ids[j]], [batch_metas[j]], python_exec)
                if ok2:
                    succeeded += 1
                else:
                    failed += 1
                    log(f"[{collection_name}] Skipped poisoned chunk: {batch_ids[j]}")

    log(f"[{collection_name}] Batch processing complete: {succeeded} succeeded, {failed} failed out of {total}.")


def kill_daemon():
    try:
        subprocess.run(["pkill", "-9", "-f", "obsidian_search/daemon.py"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        import time
        time.sleep(1)
    except Exception:
        pass


def restart_daemon():
    try:
        daemon_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "daemon.py")
        python_exec = get_python_exec()
        log_path = os.path.join(os.path.dirname(daemon_script), "daemon.log")
        with open(log_path, "a") as f:
            subprocess.Popen([python_exec, daemon_script],
                             stdout=f, stderr=f, start_new_session=True)
        log("Search daemon restarted successfully.")
    except Exception as e:
        log(f"Warning: Could not restart daemon: {e}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Crash-resilient ChromaDB sync")
    parser.add_argument("--reindex", nargs="*", help="List of filenames to forcefully re-chunk and re-index")
    args = parser.parse_args()

    log("=== Starting crash-resilient database sync ===")
    kill_daemon()
    log("Syncing obsidian_notes...")
    sync_obsidian_notes(reindex_files=args.reindex)
    log("Syncing class_materials...")
    sync_class_materials(reindex_files=args.reindex)
    log("=== Sync complete ===")
    restart_daemon()
