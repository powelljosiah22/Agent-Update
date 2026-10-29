#!/usr/bin/env python3
import os
# 1. APPLE SILICON MULTI-THREADING (Speedup ONNX inference ~20ms)
os.environ["OMP_NUM_THREADS"] = "4"
os.environ["MKL_NUM_THREADS"] = "4"
os.environ["OPENBLAS_NUM_THREADS"] = "4"
os.environ["VECLIB_MAXIMUM_THREADS"] = "4"
os.environ["NUMEXPR_NUM_THREADS"] = "4"

import json
import re
import time
import chromadb
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from chromadb.utils import embedding_functions

try:
    from dotenv import load_dotenv
    env_file = os.path.expanduser("~/Agents/Agent 0/.env")
    if os.path.exists(env_file):
        load_dotenv(env_file)
except ImportError:
    pass


def tokenize(text):
    """BM25 tokenizer: case-insensitive, punctuation-free, splits letter/digit runs.
    Strips auto-generated '## Semantic Connections' wiki-link footers so backlinks
    to other notes do not hijack BM25 lexical rankings."""
    body = text.split("## Semantic Connections")[0]
    return re.findall(r"[a-z]+|\d+", body.lower())


COURSE_CODE_RE = re.compile(r"\b([a-z]{3})[\s_-]?(\d{4}h?)\b")


def course_codes(query_text, course_param=""):
    """Collect normalized course codes (e.g. 'spa3112', 'fin3105') from the explicit course arg and the query text."""
    codes = set()
    if course_param:
        norm = re.sub(r"[^a-z0-9]", "", course_param.lower())
        if norm:
            codes.add(norm)
    for m in COURSE_CODE_RE.finditer(query_text.lower()):
        codes.add(m.group(1) + m.group(2))
    return codes


STOPWORDS = {"the", "and", "for", "with", "what", "how", "why", "who", "are", "was", "from", "that", "this", "into", "about", "does", "his", "her", "its", "of", "to", "in", "on", "a", "an", "is", "vs"}
NOISE_QUERY_WORDS = STOPWORDS | {"chapter", "ch", "problem", "problems", "question", "questions", "slide", "slides", "notes", "note", "class", "exam"}
_title_token_cache = {}


def stem_token(t):
    """Lightweight stemmer so 'investor', 'invested', 'investing', 'investment' all map to 'invest'."""
    if len(t) <= 4 or t.isdigit():
        return t
    for suf in ("ments", "ment", "ings", "ing", "ions", "ion", "ors", "ers", "ied", "ies", "ed", "er", "or", "es", "s"):
        if t.endswith(suf) and len(t) - len(suf) >= 4:
            return t[:-len(suf)]
    return t[:6]


def title_tokens(parent_file):
    """Content tokens of a note filename (cached)."""
    toks = _title_token_cache.get(parent_file)
    if toks is None:
        base = re.sub(r"\.md$", "", parent_file, flags=re.I)
        toks = {t for t in tokenize(base) if t not in STOPWORDS and not t.isdigit()}
        _title_token_cache[parent_file] = toks
    return toks


def strip_course_codes(query_text):
    """Remove course codes from the query so phrase matching targets the content."""
    return re.sub(r"\s+", " ", COURSE_CODE_RE.sub(" ", query_text.lower())).strip()


from rank_bm25 import BM25Okapi

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_db")
client = chromadb.PersistentClient(path=db_path)
emb_fn = embedding_functions.DefaultEmbeddingFunction()

vault_coll = None
class_coll = None

# BM25 Globals for "Always Hot" Cache
bm25_class_ids = []
bm25_class_metadata = []
bm25_class_documents = []
bm25_class_corpus = []
bm25_class_stems = []
bm25_class_index = None
class_chunk_map = {}  # In-memory RAM mapping for instant 0.01ms chunk stitching
class_id_to_idx = {}

bm25_vault_ids = []
bm25_vault_metadata = []
bm25_vault_documents = []
bm25_vault_corpus = []
bm25_vault_index = None

try:
    vault_coll = client.get_or_create_collection(name="obsidian_notes", embedding_function=emb_fn)
    class_coll = client.get_or_create_collection(name="class_materials", embedding_function=emb_fn)
    _ = vault_coll.query(query_texts=["warmup"], n_results=1)

    print("Building BM25 Index for class materials...")
    class_docs = class_coll.get(include=["documents", "metadatas"])
    if class_docs and class_docs["documents"]:
        bm25_class_ids = class_docs["ids"]
        bm25_class_metadata = class_docs["metadatas"]
        bm25_class_documents = class_docs["documents"]
        class_chunk_map = {cid: doc for cid, doc in zip(bm25_class_ids, bm25_class_documents)}
        class_id_to_idx = {cid: idx for idx, cid in enumerate(bm25_class_ids)}
        bm25_class_corpus = [tokenize(doc) for doc in class_docs["documents"]]
        bm25_class_stems = [{stem_token(t) for t in toks} for toks in bm25_class_corpus]
        bm25_class_index = BM25Okapi(bm25_class_corpus)
        print(f"BM25 Class Index Built ({len(bm25_class_ids)} chunks in RAM).")

    print("Building BM25 Index for vault notes...")
    vault_docs = vault_coll.get(include=["documents", "metadatas"])
    if vault_docs and vault_docs["documents"]:
        bm25_vault_ids = vault_docs["ids"]
        bm25_vault_metadata = vault_docs["metadatas"]
        bm25_vault_documents = vault_docs["documents"]
        bm25_vault_corpus = [tokenize(doc) for doc in vault_docs["documents"]]
        bm25_vault_index = BM25Okapi(bm25_vault_corpus)
        print("BM25 Vault Index Built successfully.")
except Exception as e:
    print(f"Pre-warm warning: {e}")


class NoteCache:
    def __init__(self):
        self.cache = {}

    def get_content(self, file_path):
        try:
            current_mtime = os.path.getmtime(file_path)
        except Exception:
            return None

        cached = self.cache.get(file_path)
        if cached and cached["mtime"] == current_mtime:
            return cached["content"]

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.cache[file_path] = {"content": content, "mtime": current_mtime}
            return content
        except Exception:
            return None


note_cache = NoteCache()


def hybrid_search_vault(query_text, n_results, lexical_weight=1.5, course_param=""):
    if vault_coll is None:
        return None

    search_n = max(10, n_results * 3)
    vector_results = vault_coll.query(query_texts=[query_text], n_results=search_n)

    if not bm25_vault_index:
        return vector_results

    tokenized_query = tokenize(query_text)
    bm25_scores = bm25_vault_index.get_scores(tokenized_query)

    top_bm25_indices = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)[:search_n]
    top_bm25 = [(idx, bm25_scores[idx]) for idx in top_bm25_indices]

    rrf_scores = {}
    k_rrf = 60

    if vector_results and vector_results["ids"] and vector_results["ids"][0]:
        for rank, doc_id in enumerate(vector_results["ids"][0]):
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + 1.0 / (k_rrf + rank + 1)

    for rank, (idx, score) in enumerate(top_bm25):
        if score > 0:
            doc_id = bm25_vault_ids[idx]
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + lexical_weight * (1.0 / (k_rrf + rank + 1))

    clean_q = strip_course_codes(query_text.strip().strip("\"'"))
    for rank, (idx, score) in enumerate(top_bm25):
        if score > 0 and clean_q:
            doc_text = bm25_vault_documents[idx].split("## Semantic Connections")[0].lower()
            if clean_q in doc_text:
                doc_id = bm25_vault_ids[idx]
                rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + 50.0

    codes = course_codes(query_text, course_param)
    q_content = {t for t in tokenize(clean_q) if t not in STOPWORDS and not t.isdigit()}
    phrase_hits = set()
    for idx, meta in enumerate(bm25_vault_metadata):
        doc_id = bm25_vault_ids[idx]
        pf = (meta or {}).get("parent_file") or (meta or {}).get("filename") or doc_id.split("_sub")[0]
        if not pf:
            continue
        boost = 0.0
        if codes:
            pf_norm = re.sub(r"[^a-z0-9]", "", pf.lower())
            if any(c in pf_norm for c in codes):
                boost += 60.0 + bm25_scores[idx] * 0.5
                if "master_syllabus" in pf.lower():
                    boost += 30.0
                doc_body_lower = bm25_vault_documents[idx].split("## Semantic Connections")[0].lower()
                if clean_q and clean_q in doc_body_lower and doc_id not in phrase_hits:
                    if not any(bm25_vault_ids[i] == doc_id for i, s in top_bm25 if s > 0):
                        boost += 50.0
                    phrase_hits.add(doc_id)
        if q_content:
            t_toks = title_tokens(pf)
            overlap = len(q_content & t_toks)
            if overlap >= 1:
                boost += 80.0 * (overlap / len(q_content)) + 20.0 * (overlap / max(1, len(t_toks)))
        if boost:
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + boost

    sorted_doc_ids = sorted(rrf_scores.keys(), key=lambda d: rrf_scores[d], reverse=True)[:search_n]

    final_docs = []
    final_metadatas = []

    doc_map = {}
    if vector_results and vector_results["ids"] and vector_results["ids"][0]:
        for i, did in enumerate(vector_results["ids"][0]):
            doc_map[did] = (vector_results["documents"][0][i], vector_results["metadatas"][0][i])

    for did in sorted_doc_ids:
        if did in doc_map:
            final_docs.append(doc_map[did][0])
            final_metadatas.append(doc_map[did][1])
        else:
            try:
                idx = bm25_vault_ids.index(did)
                final_docs.append(bm25_vault_documents[idx])
                final_metadatas.append(bm25_vault_metadata[idx])
            except ValueError:
                pass

    return {"ids": [sorted_doc_ids], "documents": [final_docs], "metadatas": [final_metadatas]}


def merge_overlapping_chunks(chunks, max_overlap=160):
    """Reconstruct seamless text from sliding-window chunks without duplicating overlaps."""
    if not chunks:
        return ""
    merged = chunks[0]
    for nxt in chunks[1:]:
        overlap_found = False
        if len(merged) >= 120 and len(nxt) >= 120 and merged.endswith(nxt[:120]):
            merged += nxt[120:]
            continue
        limit = min(len(merged), len(nxt), max_overlap)
        for length in range(limit, 15, -1):
            if merged.endswith(nxt[:length]):
                merged += nxt[length:]
                overlap_found = True
                break
        if not overlap_found:
            merged += "\n\n" + nxt
    return merged


def hybrid_search_class(query_text, n_results, where_clause=None, lexical_weight=1.5):
    if class_coll is None:
        return None

    search_n = max(10, n_results * 3)
    vector_results = class_coll.query(query_texts=[query_text], n_results=search_n, where=where_clause)

    if not bm25_class_index:
        return vector_results

    tokenized_query = tokenize(query_text)
    bm25_scores = bm25_class_index.get_scores(tokenized_query)

    filtered_bm25 = []
    for i, meta in enumerate(bm25_class_metadata):
        match = True
        if where_clause:
            for k, v in where_clause.items():
                if k == "$and":
                    for condition in v:
                        for ck, cv in condition.items():
                            if meta.get(ck) != cv:
                                match = False
                                break
                else:
                    if meta.get(k) != v:
                        match = False
                        break
        if match:
            filtered_bm25.append((i, bm25_scores[i]))

    filtered_bm25.sort(key=lambda x: x[1], reverse=True)
    top_bm25 = filtered_bm25[:search_n]

    rrf_scores = {}
    k_rrf = 60

    if vector_results and vector_results["ids"] and vector_results["ids"][0]:
        for rank, doc_id in enumerate(vector_results["ids"][0]):
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + 1.0 / (k_rrf + rank + 1)

    for rank, (idx, score) in enumerate(top_bm25):
        if score > 0:
            doc_id = bm25_class_ids[idx]
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + lexical_weight * (1.0 / (k_rrf + rank + 1))

    clean_q = query_text.strip().strip("\"'").lower()
    clean_no_course = strip_course_codes(clean_q)
    m_ch = re.search(r"\b(?:chapter|ch\.?)\s*#?\s*(\d+)\b", clean_no_course)
    m_qe = re.search(r"\b(quiz|exam|midterm|homework|hw)\s*#?\s*(\d+)\b", clean_no_course)
    m_qp = re.search(r"(?:\b(?:question|problem|prob\.?|exercise)\s*#?\s*|#\s*)(\d+|[ivxlc]+)\b", clean_no_course)
    m_ord = re.search(r"\b(\d+)(?:st|nd|rd|th)?\s+(?:question|problem)\b", clean_no_course)
    m_rule = re.search(r"\b(?:rule|section)\s*#?\s*([a-z0-9\(\)\.-]+)\b", clean_no_course)

    q_content = {t for t in tokenize(clean_no_course) if t not in NOISE_QUERY_WORDS and not t.isdigit()}
    q_stems = {stem_token(t) for t in q_content}

    if bm25_class_documents:
        for idx, doc_text in enumerate(bm25_class_documents):
            meta = bm25_class_metadata[idx]
            match = True
            if where_clause:
                if "course" in where_clause and meta.get("course") != where_clause["course"]:
                    match = False
                elif "$and" in where_clause:
                    for cond in where_clause["$and"]:
                        for ck, cv in cond.items():
                            if meta.get(ck) != cv:
                                match = False
                                break
            if not match:
                continue

            doc_lower = doc_text.lower()
            pf = (meta or {}).get("parent_file", "")
            pf_lower = pf.lower()
            boost = 0.0

            if m_ch:
                ch_num = str(int(m_ch.group(1)))
                meta_ch = str((meta or {}).get("chapter", "")).strip()
                pf_ch_match = re.search(r"\b(?:chapter|ch)[\s_-]*0*(\d+)\b", pf_lower)
                if meta_ch == ch_num or (pf_ch_match and str(int(pf_ch_match.group(1))) == ch_num):
                    boost += 45.0
                elif pf_ch_match and str(int(pf_ch_match.group(1))) != ch_num:
                    boost -= 35.0
                elif re.search(rf"\b(?:chapter|ch\.?)\s*0*{ch_num}\b", doc_lower):
                    boost += 12.0

            if m_qe:
                qe_kind, qe_num = m_qe.group(1), str(int(m_qe.group(2)))
                pf_qe = re.search(rf"\b{qe_kind}s?\s*#?\s*0*(\d+)\b", pf_lower)
                if pf_qe and str(int(pf_qe.group(1))) == qe_num:
                    boost += 45.0
                elif pf_qe and str(int(pf_qe.group(1))) != qe_num:
                    boost -= 35.0
                elif re.search(rf"\b{qe_kind}\s*#?\s*0*{qe_num}\b", doc_lower):
                    boost += 25.0

            if m_qp or m_ord:
                num = m_qp.group(1) if m_qp else m_ord.group(1)
                if re.search(rf"(?:^|\n)\s*(?:#+\s*)?(?:question|problem)\s*#?\s*{num}\b", doc_lower):
                    if "clickable problem index" in doc_lower or re.search(r"(?:^|\n)index\s*\n", doc_lower):
                        boost += 12.0
                    else:
                        boost += 32.0
                elif re.search(rf"\b(?:question|problem)\s*#?\s*{num}\b", doc_lower):
                    boost += 18.0
                elif re.search(rf"(?:^|\n)\s*{num}\s*(?:\.|\)|:|\n|$)", doc_lower):
                    boost += 12.0

            if m_rule and m_rule.group(0) in doc_lower:
                boost += 20.0

            if len(clean_no_course) >= 4 and clean_no_course in doc_lower:
                boost += 25.0

            if q_stems and idx < len(bm25_class_stems):
                doc_stems = bm25_class_stems[idx]
                stem_overlap = len(q_stems & doc_stems)
                if len(q_stems) >= 2 and stem_overlap == len(q_stems):
                    boost += 35.0
                    if any(k in pf_lower for k in ("notes", "slide", "problem", "in class", "study", "quicksheet")):
                        boost += 12.0
                elif stem_overlap >= 1:
                    boost += 10.0 * (stem_overlap / len(q_stems))

            if q_stems and pf:
                t_stems = {stem_token(t) for t in title_tokens(pf)}
                t_overlap = len(q_stems & t_stems)
                if t_overlap >= 1:
                    boost += 20.0 * (t_overlap / len(q_stems))

            if boost != 0.0:
                doc_id = bm25_class_ids[idx]
                rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + boost

    sorted_rrf = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:search_n]
    top_ids = [x[0] for x in sorted_rrf]

    if not top_ids:
        return None

    ordered_documents = []
    ordered_metadatas = []
    missing_ids = [did for did in top_ids if did not in class_id_to_idx]
    fallback_map = {}
    if missing_ids:
        final_docs = class_coll.get(ids=missing_ids, include=["documents", "metadatas"])
        fallback_map = {doc_id: (doc, meta) for doc_id, doc, meta in zip(final_docs["ids"], final_docs["documents"], final_docs["metadatas"])}

    for doc_id in top_ids:
        if doc_id in class_id_to_idx:
            i = class_id_to_idx[doc_id]
            ordered_documents.append(bm25_class_documents[i])
            ordered_metadatas.append(bm25_class_metadata[i])
        elif doc_id in fallback_map:
            ordered_documents.append(fallback_map[doc_id][0])
            ordered_metadatas.append(fallback_map[doc_id][1])

    if not ordered_documents:
        return None

    return {
        "ids": [top_ids],
        "documents": [ordered_documents],
        "metadatas": [ordered_metadatas],
    }


def locate_and_slice_file(full_content, anchor_chunk, query_text="", max_chars=3400):
    """Locate the matched chunk (or specific Problem N section) inside full_content,
    slice a clean line-aligned window of up to max_chars around the match, and return
    (sliced_text, start_line, end_line, total_lines)."""
    total_lines = full_content.count("\n") + 1
    if len(full_content) <= max_chars:
        return full_content, 1, total_lines, total_lines

    match_pos = -1
    clean_q = query_text.strip().lower()
    m_qp = re.search(r"(?:\b(?:question|problem|prob\.?)\s*#?\s*|#\s*)(\d+|[ivxlc]+)\b", clean_q)

    if m_qp:
        prob_num = m_qp.group(1)
        body_matches = list(re.finditer(rf"(?:^|\n)\s*(?:#+\s*)?(?:Problem|Question)\s*#?\s*{prob_num}\b[^\n]*", full_content, flags=re.I))
        if len(body_matches) >= 2:
            match_pos = body_matches[1].start()
        elif len(body_matches) == 1:
            match_pos = body_matches[0].start()

    if match_pos == -1 and anchor_chunk:
        for probe_len in (120, 80, 50):
            probe = anchor_chunk[:probe_len].strip()
            if len(probe) >= 20:
                pos = full_content.find(probe)
                if pos != -1:
                    match_pos = pos
                    break
        if match_pos == -1 and len(anchor_chunk) > 80:
            mid = len(anchor_chunk) // 3
            probe = anchor_chunk[mid : mid + 80].strip()
            if len(probe) >= 20:
                match_pos = full_content.find(probe)

    if match_pos < 0:
        match_pos = 0

    pre_chars = int(max_chars * 0.15) if not m_qp else 120
    start_pos = max(0, match_pos - pre_chars)
    if start_pos > 0:
        nl = full_content.find("\n", start_pos)
        if nl != -1 and nl < match_pos:
            start_pos = nl + 1

    end_pos = min(len(full_content), start_pos + max_chars)
    if end_pos < len(full_content):
        nl = full_content.rfind("\n", start_pos, end_pos)
        if nl != -1 and nl > match_pos:
            end_pos = nl

    start_line = full_content.count("\n", 0, start_pos) + 1
    end_line = full_content.count("\n", 0, end_pos) + 1
    sliced = full_content[start_pos:end_pos]
    return sliced, start_line, end_line, total_lines


def resolve_notes_dir(vault_base):
    """Support both '2-Permanent-Notes' and '02_Permanent_Notes' vault layouts."""
    for cand in ("2-Permanent-Notes", "02_Permanent_Notes"):
        p = os.path.join(vault_base, cand)
        if os.path.exists(p):
            return p
    return os.path.join(vault_base, "2-Permanent-Notes")


class QueryHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/health", "/"):
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "ok",
                "vault_chunks": len(bm25_vault_ids),
                "class_chunks": len(bm25_class_ids),
            }).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        try:
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length)
            req = json.loads(post_data)

            query = req.get("query", "")
            n_results = max(1, min(6, int(req.get("n_results", 3))))
            target = req.get("target", "all").lower()
            lexical_weight = float(req.get("lexical_weight", 1.5))
            chunk_window = max(1, min(30, int(req.get("chunk_window", 8))))

            MAX_TOTAL_INLINE_CHARS = 3800
            per_result_cap = min(2400, max(900, int((MAX_TOTAL_INLINE_CHARS - 200) / max(1, n_results))))

            course_filter = req.get("course", "").upper().replace("-", "_")
            if course_filter in ("SIE", "FINRA_SIE"):
                course_filter = "FINRA_SIE"
            chapter_filter = str(req.get("chapter", "")).strip()
            if chapter_filter:
                m_ch = re.search(r"\d+", chapter_filter)
                if m_ch:
                    chapter_filter = str(int(m_ch.group(0)))
            doc_type_filter = req.get("document_type", "")

            where_conditions = []
            if course_filter:
                where_conditions.append({"course": course_filter})
            if chapter_filter:
                where_conditions.append({"chapter": chapter_filter})
            if doc_type_filter:
                where_conditions.append({"document_type": doc_type_filter})

            where_clause = None
            if len(where_conditions) == 1:
                where_clause = where_conditions[0]
            elif len(where_conditions) > 1:
                where_clause = {"$and": where_conditions}

            output = []
            current_total_chars = 0

            # --- 1. SEARCH VAULT ---
            if target in ["vault", "all"]:
                try:
                    search_n = max(10, n_results * 3)
                    results = hybrid_search_vault(query, search_n, lexical_weight, course_filter)

                    seen_files = set()
                    if results and "documents" in results and results["documents"]:
                        docs = results["documents"][0]
                        metadatas = results["metadatas"][0]
                        vault_base = os.path.expanduser(os.environ.get("OBSIDIAN_VAULT_PATH", "~/Documents/Second Brain"))
                        notes_dir = resolve_notes_dir(vault_base)

                        for idx_m, meta in enumerate(metadatas):
                            parent_file = meta.get("parent_file") or meta.get("filename")
                            if not parent_file or parent_file in seen_files:
                                continue

                            seen_files.add(parent_file)
                            if len(seen_files) > n_results or current_total_chars >= MAX_TOTAL_INLINE_CHARS:
                                break

                            file_path = os.path.join(notes_dir, parent_file)
                            anchor_doc = docs[idx_m] if idx_m < len(docs) else ""

                            full_content = note_cache.get_content(file_path)
                            if full_content:
                                sliced, s_line, e_line, tot_lines = locate_and_slice_file(full_content, anchor_doc, query, max_chars=per_result_cap)
                                entry = f"--- [VAULT NOTE]: {parent_file} (Lines {s_line}-{e_line} of {tot_lines}) | Path: {file_path} ---\n{sliced}\n"
                                output.append(entry)
                                current_total_chars += len(entry)
                            elif anchor_doc:
                                entry = f"--- [VAULT NOTE]: {parent_file} ---\n{anchor_doc}\n"
                                output.append(entry)
                                current_total_chars += len(entry)
                except Exception as e:
                    print(f"Vault search error: {e}")

            # --- 2. SEARCH CLASS MATERIALS ---
            if target in ["classes", "all"]:
                try:
                    search_n = max(10, n_results * 3)
                    results = hybrid_search_class(query, search_n, where_clause, lexical_weight)

                    if results and "documents" in results and results["documents"]:
                        docs = results["documents"][0]
                        metas = results["metadatas"][0]

                        seen_files = set()
                        seen_chunks = set()
                        for i in range(min(search_n, len(docs))):
                            if len(output) >= n_results or current_total_chars >= MAX_TOTAL_INLINE_CHARS:
                                break
                            meta = metas[i]
                            parent_file = meta.get("parent_file", "Class_Material.md")
                            course = meta.get("course", "Course")
                            sub_idx = meta.get("sub_index", 0)
                            file_path = meta.get("file_path", "")

                            is_problem_or_notes = any(term in parent_file.lower() for term in ["in_class", "in class", "problem", "practice", "study_guide", "study guide", "quiz", "homework", "notes", "quicksheet", "syllabus", "checklist"])
                            if is_problem_or_notes and file_path and os.path.exists(file_path):
                                file_key = f"{course}_{parent_file}"
                                if file_key in seen_files:
                                    continue
                                full_content = note_cache.get_content(file_path)
                                if full_content:
                                    seen_files.add(file_key)
                                    sliced, s_line, e_line, tot_lines = locate_and_slice_file(full_content, docs[i], query, max_chars=per_result_cap)
                                    entry = f"--- [CLASS MATERIAL | {course}]: {parent_file} (Lines {s_line}-{e_line} of {tot_lines}) | Path: {file_path} ---\n{sliced}\n"
                                    output.append(entry)
                                    current_total_chars += len(entry)
                                    continue

                            chunk_key = f"{course}_{parent_file}_{sub_idx}"
                            if chunk_key in seen_chunks:
                                continue

                            back_chunks = max(1, int(round(chunk_window * 0.35))) if chunk_window > 1 else 0
                            fwd_chunks = max(1, chunk_window - back_chunks)
                            start_idx = max(0, sub_idx - back_chunks)
                            end_idx = sub_idx + fwd_chunks
                            max_stitched_chars = min(per_result_cap, max(1200, chunk_window * 450))
                            stitched_parts = []
                            total_chars = 0

                            for k in range(start_idx, end_idx):
                                target_id = f"{course}_{parent_file}_sub{k}"
                                doc_chunk = class_chunk_map.get(target_id)
                                if doc_chunk:
                                    stitched_parts.append(doc_chunk)
                                    seen_chunks.add(target_id)
                                    total_chars += len(doc_chunk)
                                    if total_chars >= max_stitched_chars:
                                        break
                                elif k >= sub_idx:
                                    break

                            stitched = merge_overlapping_chunks(stitched_parts) if stitched_parts else docs[i]
                            if len(stitched) > per_result_cap:
                                stitched = stitched[:per_result_cap] + "\n...[Use read_file or grep on Path above for remaining lines]..."

                            line_info = f"Chunks {start_idx}-{min(end_idx-1, start_idx+len(stitched_parts)-1)}"
                            if file_path and os.path.exists(file_path):
                                full_content = note_cache.get_content(file_path)
                                if full_content:
                                    pos = full_content.find(docs[i][:80].strip()) if len(docs[i]) >= 40 else -1
                                    if pos != -1:
                                        s_line = full_content.count("\n", 0, pos) + 1
                                        e_line = s_line + stitched.count("\n")
                                        line_info = f"Lines ~{s_line}-{e_line}, {line_info}"
                            path_info = f" | Path: {file_path}" if file_path else ""
                            entry = f"--- [CLASS MATERIAL | {course}]: {parent_file} ({line_info}){path_info} ---\n{stitched}\n"
                            output.append(entry)
                            current_total_chars += len(entry)
                except Exception as e:
                    print(f"Class materials search error: {e}")

            final_text = "\n".join(output) if output else "No results found."
            if len(final_text) > MAX_TOTAL_INLINE_CHARS:
                final_text = final_text[:MAX_TOTAL_INLINE_CHARS] + "\n\n...[INLINE CAP REACHED: Use read_file(Path, StartLine, EndLine) or single-file grep on Path above]..."

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"result": final_text}).encode("utf-8"))
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

    def log_message(self, format, *args):
        return


if __name__ == "__main__":
    port = 8085
    ThreadingHTTPServer.allow_reuse_address = True
    server = ThreadingHTTPServer(("127.0.0.1", port), QueryHandler)
    print(f"Optimized Vector Database Daemon listening on http://127.0.0.1:{port}")
    server.serve_forever()
