#!/usr/bin/env python3
import os
import re
import chromadb

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_db")
client = chromadb.PersistentClient(path=db_path)
col = client.get_or_create_collection("class_materials")

docs = col.get(include=["metadatas"])
metas = docs["metadatas"]
ids = docs["ids"]

new_metas = []
for m in metas:
    pf = m.get("parent_file", "")

    chap = ""
    match_chap = re.search(r"(?i)(?:chapter|module|ch\.?)\s*(\d+)", pf)
    if match_chap:
        chap = str(int(match_chap.group(1)))

    dtype = ""
    pf_lower = pf.lower()
    if any(k in pf_lower for k in ["slide", "ppt", "powerpoint", "notes"]):
        dtype = "slide"
    elif any(k in pf_lower for k in ["problem", "assignment", "hw", "hwk", "quiz", "exam", "mock", "study_guide", "study guide"]):
        dtype = "problem"
    elif any(k in pf_lower for k in ["textbook", "reading", "dalton", "harrington", "spiceland", "fundamentals_ch", "edition"]):
        dtype = "textbook"

    m["chapter"] = chap
    m["document_type"] = dtype
    new_metas.append(m)

batch_size = 5000
for i in range(0, len(ids), batch_size):
    col.update(ids=ids[i:i+batch_size], metadatas=new_metas[i:i+batch_size])
print(f"Updated {len(ids)} metadata entries successfully.")
