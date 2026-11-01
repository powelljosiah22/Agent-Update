#!/usr/bin/env python3
"""
Deterministic Biblical Philological Query Engine (CLI + MCP Backend)
Provides:
  1. vector_concept_lookup: Hybrid Vector (ChromaDB) + Lexical Concept-to-Lemma Router
  2. sql_concordance_query:
     - mode='interlinear': Word-by-word Markdown table for any verse/range (with automatic LXX parallel on OT verses)
     - mode='lemma': Full lexical entry, morphological distribution, book frequency, and concordance occurrences
     - mode='lxx_bridge': Traces Hebrew OT <-> Greek LXX <-> Greek NT lexical translations across parallel verses
     - mode='custom_sql': Read-only SQLite SELECT execution against corpus_words and lexicon_entries
"""
import os
import re
import sys
import json
import sqlite3
import argparse
import unicodedata

os.environ["OMP_NUM_THREADS"] = "4"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "biblical_corpus.db")
CHROMA_PATH = os.path.join(BASE_DIR, "chroma_lexicon")

BOOK_ALIASES = {
    # OT
    "genesis": "Gen", "gen": "Gen", "ge": "Gen",
    "exodus": "Exod", "exod": "Exod", "ex": "Exod", "exo": "Exod",
    "leviticus": "Lev", "lev": "Lev", "le": "Lev",
    "numbers": "Num", "num": "Num", "nu": "Num",
    "deuteronomy": "Deut", "deut": "Deut", "dt": "Deut",
    "joshua": "Josh", "josh": "Josh", "jos": "Josh",
    "judges": "Judg", "judg": "Judg", "jdg": "Judg",
    "ruth": "Ruth", "ru": "Ruth",
    "1samuel": "1Sam", "1sam": "1Sam", "1sa": "1Sam", "i samuel": "1Sam",
    "2samuel": "2Sam", "2sam": "2Sam", "2sa": "2Sam", "ii samuel": "2Sam",
    "1kings": "1Kgs", "1kgs": "1Kgs", "1ki": "1Kgs", "i kings": "1Kgs",
    "2kings": "2Kgs", "2kgs": "2Kgs", "2ki": "2Kgs", "ii kings": "2Kgs",
    "1chronicles": "1Chr", "1chr": "1Chr", "1ch": "1Chr",
    "2chronicles": "2Chr", "2chr": "2Chr", "2ch": "2Chr",
    "ezra": "Ezra", "ezr": "Ezra",
    "nehemiah": "Neh", "neh": "Neh", "ne": "Neh",
    "esther": "Esth", "esth": "Esth", "est": "Esth",
    "job": "Job", "jb": "Job",
    "psalms": "Ps", "psalm": "Ps", "ps": "Ps", "psa": "Ps",
    "proverbs": "Prov", "prov": "Prov", "pr": "Prov", "prv": "Prov",
    "ecclesiastes": "Eccl", "eccl": "Eccl", "ecc": "Eccl", "qoheleth": "Eccl",
    "songofsolomon": "Song", "song": "Song", "sos": "Song", "cant": "Song",
    "isaiah": "Isa", "isa": "Isa", "is": "Isa",
    "jeremiah": "Jer", "jer": "Jer", "je": "Jer",
    "lamentations": "Lam", "lam": "Lam", "la": "Lam",
    "ezekiel": "Ezek", "ezek": "Ezek", "ezk": "Ezek",
    "daniel": "Dan", "dan": "Dan", "da": "Dan",
    "hosea": "Hos", "hos": "Hos", "ho": "Hos",
    "joel": "Joel", "jl": "Joel",
    "amos": "Amos", "am": "Amos",
    "obadiah": "Obad", "obad": "Obad", "ob": "Obad",
    "jonah": "Jonah", "jon": "Jonah",
    "micah": "Mic", "mic": "Mic",
    "nahum": "Nah", "nah": "Nah", "na": "Nah",
    "habakkuk": "Hab", "hab": "Hab",
    "zephaniah": "Zeph", "zeph": "Zeph", "zep": "Zeph",
    "haggai": "Hag", "hag": "Hag",
    "zechariah": "Zech", "zech": "Zech", "zec": "Zech",
    "malachi": "Mal", "mal": "Mal",
    # NT
    "matthew": "Matt", "matt": "Matt", "mt": "Matt",
    "mark": "Mark", "mk": "Mark", "mrk": "Mark",
    "luke": "Luke", "lk": "Luke", "luk": "Luke",
    "john": "John", "jn": "John", "jhn": "John",
    "acts": "Acts", "ac": "Acts", "act": "Acts",
    "romans": "Rom", "rom": "Rom", "ro": "Rom",
    "1corinthians": "1Cor", "1cor": "1Cor", "1co": "1Cor",
    "2corinthians": "2Cor", "2cor": "2Cor", "2co": "2Cor",
    "galatians": "Gal", "gal": "Gal", "ga": "Gal",
    "ephesians": "Eph", "eph": "Eph",
    "philippians": "Phil", "phil": "Phil", "php": "Phil",
    "colossians": "Col", "col": "Col",
    "1thessalonians": "1Thess", "1thess": "1Thess", "1th": "1Thess",
    "2thessalonians": "2Thess", "2thess": "2Thess", "2th": "2Thess",
    "1timothy": "1Tim", "1tim": "1Tim", "1ti": "1Tim",
    "2timothy": "2Tim", "2tim": "2Tim", "2ti": "2Tim",
    "titus": "Titus", "tit": "Titus",
    "philemon": "Phlm", "phlm": "Phlm", "phm": "Phlm",
    "hebrews": "Heb", "heb": "Heb", "he": "Heb",
    "james": "Jas", "jas": "Jas", "jam": "Jas",
    "1peter": "1Pet", "1pet": "1Pet", "1pe": "1Pet",
    "2peter": "2Pet", "2pet": "2Pet", "2pe": "2Pet",
    "1john": "1John", "1jn": "1John",
    "2john": "2John", "2jn": "2John",
    "3john": "3John", "3jn": "3John",
    "jude": "Jude", "jud": "Jude",
    "revelation": "Rev", "rev": "Rev", "re": "Rev", "apocalypse": "Rev",
}


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def parse_reference(ref_str: str):
    """Parses references like 'Gen 1:1', 'Gen.1.1-3', '1 Cor 13:4-7', 'Rom 3:21-26'."""
    s = ref_str.strip().replace(".", " ")
    m = re.match(r"^([1-3]?\s*[A-Za-z]+)\s+(\d+)(?:[:\s](\d+)(?:\s*-\s*(\d+))?)?$", s)
    if not m:
        raise ValueError(f"Could not parse scripture reference: '{ref_str}'. Expected format like 'Gen 1:1' or 'Rom 3:21-26'.")
    raw_book = re.sub(r"\s+", "", m.group(1)).lower()
    book = BOOK_ALIASES.get(raw_book, m.group(1).strip())
    chapter = int(m.group(2))
    v_start = int(m.group(3)) if m.group(3) else 1
    v_end = int(m.group(4)) if m.group(4) else (v_start if m.group(3) else 999)
    return book, chapter, v_start, v_end


def vector_concept_lookup(query: str, language_filter: str = "all", n_results: int = 8) -> str:
    """
    Hybrid Concept-to-Lemma Router:
    Combines ChromaDB semantic vector search with exact/substring SQL lexical matching
    and returns candidate Hebrew, Aramaic, and Greek root_lemma IDs with corpus occurrence counts.
    """
    import chromadb
    from chromadb.utils import embedding_functions

    conn = get_conn()
    cur = conn.cursor()

    candidates = {}

    # 1. Exact/Lexical match in SQLite first (handles Strong's IDs, transliterations, Greek/Hebrew words, and exact English glosses)
    q_clean = unicodedata.normalize("NFC", query.strip())
    tokens = [t for t in re.split(r"[\s,;:/]+", q_clean) if len(t) >= 2]

    sql_conds = [
        "lemma_id = ?", "strongs_id = ?", "original_word = ?",
        "LOWER(transliteration) = LOWER(?)",
        "LOWER(primary_glosses) LIKE LOWER(?)"
    ]
    params = [q_clean, q_clean.upper(), q_clean, q_clean, f"%{q_clean}%"]
    for tok in tokens[:4]:
        sql_conds.append("LOWER(primary_glosses) LIKE LOWER(?)")
        params.append(f"%{tok}%")
        sql_conds.append("LOWER(idiomatic_notes) LIKE LOWER(?)")
        params.append(f"%{tok}%")

    lang_clause = ""
    if language_filter and language_filter.lower() in ("hebrew", "aramaic", "greek"):
        lang_clause = f" AND LOWER(language) = '{language_filter.lower()}'"

    cur.execute(
        f"""
        SELECT lemma_id, strongs_id, language, original_word, transliteration, primary_glosses, idiomatic_notes
        FROM lexicon_entries
        WHERE ({' OR '.join(sql_conds)}) {lang_clause}
        LIMIT 25
        """,
        params,
    )
    for row in cur.fetchall():
        lid = row["lemma_id"]
        score = 10.0
        if q_clean.lower() in (row["lemma_id"].lower(), (row["strongs_id"] or "").lower(), row["original_word"].lower(), (row["transliteration"] or "").lower()):
            score += 50.0
        if re.search(rf"\b{re.escape(q_clean.lower())}\b", (row["primary_glosses"] or "").lower()):
            score += 25.0
        for tok in tokens:
            if re.search(rf"\b{re.escape(tok.lower())}\b", (row["primary_glosses"] or "").lower()):
                score += 8.0
            elif re.search(rf"\b{re.escape(tok.lower())}\b", (row["idiomatic_notes"] or "").lower()):
                score += 5.0
        candidates[lid] = {"row": dict(row), "score": score, "source": "lexical+vector"}

    # 2. SQLite FTS5 BM25 search across primary_glosses and idiomatic_notes
    try:
        fts_tokens = [re.sub(r"[^a-zA-Z0-9\u0370-\u03ff\u1f00-\u1fff\u0590-\u05ff]", "", t) for t in tokens if len(t) >= 2]
        if fts_tokens:
            fts_q = " OR ".join(f'"{t}"*' for t in fts_tokens[:6])
            cur.execute(
                """
                SELECT lemma_id, bm25(lexicon_fts, 5.0, 5.0, 1.0, 8.0, 6.0, 10.0, 3.0) as rank_score
                FROM lexicon_fts
                WHERE lexicon_fts MATCH ?
                ORDER BY rank_score
                LIMIT 30
                """,
                (fts_q,),
            )
            for rank_idx, fts_row in enumerate(cur.fetchall()):
                lid = fts_row["lemma_id"]
                fts_boost = max(2.0, 22.0 - rank_idx * 0.7)
                if lid in candidates:
                    candidates[lid]["score"] += fts_boost
                else:
                    cur.execute("SELECT * FROM lexicon_entries WHERE lemma_id = ?", (lid,))
                    r = cur.fetchone()
                    if r:
                        if language_filter and language_filter.lower() in ("hebrew", "aramaic", "greek"):
                            if r["language"].lower() != language_filter.lower():
                                continue
                        candidates[lid] = {"row": dict(r), "score": fts_boost, "source": "fts5_bm25"}
    except Exception:
        pass

    # 3. ChromaDB semantic vector search (if collection has entries)
    try:
        if os.path.exists(CHROMA_PATH):
            import chromadb
            from chromadb.utils import embedding_functions
            client = chromadb.PersistentClient(path=CHROMA_PATH)
            emb_fn = embedding_functions.DefaultEmbeddingFunction()
            coll = client.get_collection(name="biblical_lexicon", embedding_function=emb_fn)
            if coll.count() > 0:
                where_filter = None
                if language_filter and language_filter.lower() in ("hebrew", "aramaic", "greek"):
                    where_filter = {"language": language_filter.capitalize()}
                res = coll.query(query_texts=[query], n_results=max(n_results * 2, 16), where=where_filter)
                if res and res.get("metadatas") and res["metadatas"][0]:
                    for rank, (meta, dist) in enumerate(zip(res["metadatas"][0], res["distances"][0])):
                        lid = meta["lemma_id"]
                        vec_score = max(0.0, 18.0 * (1.0 - float(dist))) + max(0.0, 8.0 - rank * 0.5)
                        if lid in candidates:
                            candidates[lid]["score"] += vec_score
                        else:
                            cur.execute("SELECT * FROM lexicon_entries WHERE lemma_id = ?", (lid,))
                            r = cur.fetchone()
                            if r:
                                candidates[lid] = {"row": dict(r), "score": vec_score, "source": "vector"}
    except Exception:
        pass

    # 4. Fetch corpus occurrence counts from precomputed lemma_counts table (0.1ms)
    ranked = sorted(candidates.values(), key=lambda x: x["score"], reverse=True)[: max(n_results * 3, 20)]
    results_out = []
    for item in ranked:
        r = item["row"]
        lid = r["lemma_id"]
        sid = r["strongs_id"]
        cur.execute(
            """
            SELECT testament, MAX(cnt) as cnt
            FROM lemma_counts
            WHERE key_id = ? OR (key_id = ? AND ? != '')
            GROUP BY testament
            """,
            (lid, sid or "", sid or ""),
        )
        counts = {c["testament"]: c["cnt"] for c in cur.fetchall()}
        total_occ = sum(counts.values())
        if total_occ > 0:
            item["score"] += min(15.0, (total_occ ** 0.28) * 2.2)
        item["counts"] = counts
        item["total_occ"] = total_occ
        results_out.append(item)

    results_out.sort(key=lambda x: x["score"], reverse=True)
    results_out = results_out[:n_results]

    lines = [
        f"### Concept-to-Lemma Router Results for: `{query}`",
        "",
        "| Rank | Lemma ID | Strong's | Language | Original | Transliteration | Primary Mechanical Glosses | Corpus Occurrences (OT / LXX / NT) |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ]
    for idx, item in enumerate(results_out, start=1):
        r = item["row"]
        c = item["counts"]
        occ_str = f"**{item['total_occ']}** (OT: {c.get('OT', 0)}, LXX: {c.get('LXX', 0)}, NT: {c.get('NT', 0)})"
        lines.append(
            f"| {idx} | `{r['lemma_id']}` | `{r['strongs_id'] or '-'}` | {r['language']} | **{r['original_word']}** | *{r['transliteration']}* | {r['primary_glosses'][:120]} | {occ_str} |"
        )

    lines.append("\n#### Detailed Lexical & Idiomatic Notes (Top Matches)")
    for item in results_out[:5]:
        r = item["row"]
        notes = (r["idiomatic_notes"] or "")[:450]
        lines.append(f"- **`{r['lemma_id']}` ({r['original_word']} / *{r['transliteration']}*)**: {notes}")

    conn.close()
    return "\n".join(lines)


def query_interlinear(conn: sqlite3.Connection, reference: str, testament: str = "all") -> str:
    book, ch, v_start, v_end = parse_reference(reference)
    cur = conn.cursor()

    t_clause = ""
    params = [book, ch, v_start, v_end]
    if testament and testament.upper() in ("OT", "NT", "LXX"):
        t_clause = " AND cw.testament = ?"
        params.append(testament.upper())

    cur.execute(
        f"""
        SELECT cw.testament, cw.book, cw.chapter, cw.verse, cw.word_index,
               cw.surface_text, cw.transliteration, cw.root_lemma, cw.strongs_id,
               cw.morph_code, cw.morph_decoded, cw.english_gloss,
               le.primary_glosses
        FROM corpus_words cw
        LEFT JOIN lexicon_entries le ON cw.root_lemma = le.lemma_id
        WHERE cw.book = ? AND cw.chapter = ? AND cw.verse BETWEEN ? AND ? {t_clause}
        ORDER BY CASE cw.testament WHEN 'OT' THEN 1 WHEN 'NT' THEN 2 WHEN 'LXX' THEN 3 END,
                 cw.verse ASC, cw.word_index ASC
        """,
        params,
    )
    rows = cur.fetchall()
    if not rows:
        return f"No words found for reference `{reference}` (parsed as `{book} {ch}:{v_start}-{v_end}`)."

    out = [f"### Interlinear & Morphological Breakdown: `{book} {ch}:{v_start}`" + (f"-`{v_end}`" if v_end != v_start and v_end < 900 else "")]
    grouped = {}
    for r in rows:
        key = (r["testament"], r["book"], r["chapter"], r["verse"])
        grouped.setdefault(key, []).append(r)

    for (test, b, c, v), w_rows in grouped.items():
        full_surface = " ".join(r["surface_text"] for r in w_rows)
        out.append(f"\n#### [{test}] {b} {c}:{v}")
        out.append(f"> **Original Text:** {full_surface}\n")
        out.append("| # | Surface | Transliteration | Root Lemma | Strong's | Morph Code | Decoded Grammar | Mechanical Gloss |")
        out.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
        for r in w_rows:
            gloss = r["english_gloss"] or (r["primary_glosses"].split(",")[0] if r["primary_glosses"] else "-")
            out.append(
                f"| {r['word_index']} | **{r['surface_text']}** | *{r['transliteration'] or '-'}* | `{r['root_lemma']}` | `{r['strongs_id'] or '-'}` | `{r['morph_code']}` | {r['morph_decoded'] or '-'} | {gloss} |"
            )

    return "\n".join(out)


def query_lemma_concordance(conn: sqlite3.Connection, lemma_id: str, testament: str = "all", limit: int = 25) -> str:
    cur = conn.cursor()
    q_lemma = unicodedata.normalize("NFC", lemma_id.strip())

    # 1. Lookup lexicon entry by lemma_id, strongs_id, or original_word
    cur.execute(
        """
        SELECT * FROM lexicon_entries
        WHERE lemma_id = ? OR strongs_id = ? OR original_word = ?
        LIMIT 3
        """,
        (q_lemma, q_lemma.upper(), q_lemma),
    )
    lex_rows = cur.fetchall()

    out = [f"### SQL Concordance & Morphological Profile: `{q_lemma}`\n"]
    target_lemmas = {q_lemma}
    target_strongs = {q_lemma.upper()} if re.match(r"^[HG]\d+$", q_lemma.upper()) else set()

    if lex_rows:
        for lr in lex_rows:
            target_lemmas.add(lr["lemma_id"])
            if lr["strongs_id"]:
                target_strongs.add(lr["strongs_id"])
            out.append(f"- **Lemma ID:** `{lr['lemma_id']}` | **Strong's:** `{lr['strongs_id'] or '-'}` | **Language:** {lr['language']}")
            out.append(f"- **Original Word:** **{lr['original_word']}** (*{lr['transliteration']}*)")
            out.append(f"- **Primary Mechanical Glosses:** {lr['primary_glosses']}")
            if lr["idiomatic_notes"]:
                out.append(f"- **Lexical & Idiomatic Notes:** {lr['idiomatic_notes']}\n")
    else:
        out.append(f"*(No direct header row in `lexicon_entries` for `{q_lemma}`; querying `corpus_words` directly)*\n")

    lemma_placeholders = ",".join("?" for _ in target_lemmas)
    where_parts = [f"root_lemma IN ({lemma_placeholders})"]
    params = list(target_lemmas)
    if target_strongs:
        s_placeholders = ",".join("?" for _ in target_strongs)
        where_parts.append(f"strongs_id IN ({s_placeholders})")
        params.extend(target_strongs)

    where_sql = "(" + " OR ".join(where_parts) + ")"
    if testament and testament.upper() in ("OT", "NT", "LXX"):
        where_sql += " AND testament = ?"
        params.append(testament.upper())

    # 2. Distribution by Testament & Book
    cur.execute(
        f"""
        SELECT testament, book, COUNT(*) as cnt
        FROM corpus_words
        WHERE {where_sql}
        GROUP BY testament, book
        ORDER BY CASE testament WHEN 'OT' THEN 1 WHEN 'LXX' THEN 2 WHEN 'NT' THEN 3 END, cnt DESC
        """,
        params,
    )
    book_counts = cur.fetchall()
    if not book_counts:
        return "\n".join(out) + f"\nNo occurrences found in `corpus_words` for `{q_lemma}`."

    by_test = {}
    for r in book_counts:
        by_test.setdefault(r["testament"], []).append(f"{r['book']} ({r['cnt']})")

    out.append("#### 1. Corpus Distribution Across Books")
    for t in ("OT", "LXX", "NT"):
        if t in by_test:
            total_t = sum(int(x.split("(")[1][:-1]) for x in by_test[t])
            out.append(f"- **{t} ({total_t} total):** " + ", ".join(by_test[t][:15]) + (" ..." if len(by_test[t]) > 15 else ""))

    # 3. Morphological Parsing Distribution
    cur.execute(
        f"""
        SELECT testament, morph_code, morph_decoded, COUNT(*) as cnt
        FROM corpus_words
        WHERE {where_sql}
        GROUP BY testament, morph_code, morph_decoded
        ORDER BY cnt DESC
        LIMIT 12
        """,
        params,
    )
    morph_rows = cur.fetchall()
    out.append("\n#### 2. Top Morphological Forms (`morph_code`)")
    out.append("| Testament | Morph Code | Decoded Grammatical Form | Count |")
    out.append("| :--- | :--- | :--- | :--- |")
    for mr in morph_rows:
        out.append(f"| {mr['testament']} | `{mr['morph_code']}` | {mr['morph_decoded'] or '-'} | {mr['cnt']} |")

    # 4. Sample Concordance Verses (spread across distinct books/authors to surface internal corpus voices)
    cur.execute(
        f"""
        SELECT testament, book, chapter, verse, surface_text, transliteration, morph_code, morph_decoded, english_gloss
        FROM corpus_words
        WHERE {where_sql}
        ORDER BY CASE testament WHEN 'OT' THEN 1 WHEN 'NT' THEN 2 WHEN 'LXX' THEN 3 END, id ASC
        """,
        params,
    )
    all_occ = cur.fetchall()

    # Sample evenly across occurrences so diverse biblical authors (e.g. Torah, Prophets, Wisdom, Paul, James, Gospels) appear
    step = max(1, len(all_occ) // max(1, limit))
    sampled = all_occ[::step][:limit]

    out.append(f"\n#### 3. Representative Concordance Occurrences ({len(sampled)} of {len(all_occ)} total)")
    out.append("| Ref | Form (`surface_text`) | Morph (`morph_code`) | Verse Context (Original + Mechanical Gloss) |")
    out.append("| :--- | :--- | :--- | :--- |")

    for occ in sampled:
        cur.execute(
            """
            SELECT surface_text, english_gloss, word_index
            FROM corpus_words
            WHERE testament = ? AND book = ? AND chapter = ? AND verse = ?
            ORDER BY word_index ASC
            """,
            (occ["testament"], occ["book"], occ["chapter"], occ["verse"]),
        )
        v_words = cur.fetchall()
        v_str = " ".join(
            f"**{w['surface_text']}** [{w['english_gloss'] or ''}]" if w["surface_text"] == occ["surface_text"]
            else f"{w['surface_text']} ({w['english_gloss'] or ''})"
            for w in v_words[:18]
        )
        if len(v_words) > 18:
            v_str += " ..."
        ref_label = f"**[{occ['testament']}] {occ['book']} {occ['chapter']}:{occ['verse']}**"
        out.append(f"| {ref_label} | **{occ['surface_text']}** (*{occ['transliteration']}*) | `{occ['morph_code']}` ({occ['morph_decoded']}) | {v_str} |")

    return "\n".join(out)


def query_lxx_bridge(conn: sqlite3.Connection, lemma_id: str, limit: int = 15) -> str:
    """Traces OT Hebrew <-> LXX Greek lexical correspondences by joining parallel (book, chapter, verse) across OT and LXX."""
    cur = conn.cursor()
    q = unicodedata.normalize("NFC", lemma_id.strip())

    # Determine if input is Hebrew ('H...') or Greek ('G...' or Greek script)
    is_hebrew = q.upper().startswith("H") or any(0x0590 <= ord(c) <= 0x05FF for c in q)

    if is_hebrew:
        cur.execute(
            """
            SELECT lxx.root_lemma AS grk_lemma, lxx.strongs_id AS grk_strongs,
                   lxx.english_gloss AS grk_gloss, COUNT(DISTINCT ot.book || '.' || ot.chapter || '.' || ot.verse) AS shared_verses
            FROM corpus_words ot
            JOIN corpus_words lxx
              ON ot.book = lxx.book AND ot.chapter = lxx.chapter AND ot.verse = lxx.verse
            WHERE ot.testament = 'OT' AND lxx.testament = 'LXX'
              AND (ot.root_lemma = ? OR ot.strongs_id = ?)
              AND lxx.pos NOT IN ('P', 'RA', 'C', 'PREP', 'CONJ', 'PRT', 'RP', 'RD', 'RI', 'RR', 'R', 'D', 'X')
              AND lxx.root_lemma NOT IN ('αὐτός', 'κύριος', 'θεός', 'πᾶς', 'οὐ', 'μή', 'ἐγώ', 'σύ', 'ὅς', 'οὗτος', 'εἰμί', 'λέγω')
            GROUP BY lxx.root_lemma, lxx.strongs_id
            ORDER BY shared_verses DESC
            LIMIT ?
            """,
            (q.upper(), q.upper(), limit),
        )
        rows = cur.fetchall()
        out = [
            f"### OT-to-LXX Septuagint Lexical Bridge for Hebrew `{q}`",
            "*(Greek content lemmas co-occurring in the same verse as this Hebrew root across the Septuagint)*\n",
            "| Rank | LXX Greek Lemma | Strong's | LXX Mechanical Gloss | Co-occurring Verses |",
            "| :--- | :--- | :--- | :--- | :--- |",
        ]
        for idx, r in enumerate(rows, 1):
            out.append(f"| {idx} | **{r['grk_lemma']}** (*{r['grk_strongs'] or '-'}*) | `{r['grk_strongs'] or '-'}` | {r['grk_gloss'] or '-'} | {r['shared_verses']} |")
        return "\n".join(out)
    else:
        cur.execute(
            """
            SELECT ot.root_lemma AS heb_lemma, le.original_word AS heb_word, le.transliteration AS heb_xlit,
                   le.primary_glosses AS heb_gloss, COUNT(DISTINCT lxx.book || '.' || lxx.chapter || '.' || lxx.verse) AS shared_verses
            FROM corpus_words lxx
            JOIN corpus_words ot
              ON lxx.book = ot.book AND lxx.chapter = ot.chapter AND lxx.verse = ot.verse
            LEFT JOIN lexicon_entries le ON ot.root_lemma = le.lemma_id
            WHERE lxx.testament = 'LXX' AND ot.testament = 'OT'
              AND (lxx.root_lemma = ? OR lxx.strongs_id = ?)
              AND ot.root_lemma NOT IN ('H853', 'H3588', 'H3068', 'H430', 'H559', 'H1961', 'H3808', 'H5921', 'H413')
            GROUP BY ot.root_lemma
            ORDER BY shared_verses DESC
            LIMIT ?
            """,
            (q, q.upper(), limit),
        )
        rows = cur.fetchall()
        out = [
            f"### LXX-to-OT Hebrew Underlying Roots for Greek `{q}`",
            "*(Hebrew content roots co-occurring in parallel verses where the LXX uses this Greek lemma)*\n",
            "| Rank | OT Hebrew Root | Hebrew Word | Transliteration | Primary Hebrew Glosses | Co-occurring Verses |",
            "| :--- | :--- | :--- | :--- | :--- | :--- |",
        ]
        for idx, r in enumerate(rows, 1):
            out.append(
                f"| {idx} | `{r['heb_lemma']}` | **{r['heb_word'] or '-'}** | *{r['heb_xlit'] or '-'}* | {(r['heb_gloss'] or '-')[:90]} | {r['shared_verses']} |"
            )
        return "\n".join(out)


def query_custom_sql(conn: sqlite3.Connection, sql_query: str, limit: int = 50) -> str:
    sql_clean = sql_query.strip()
    if not re.match(r"^(SELECT|WITH)\b", sql_clean, flags=re.IGNORECASE):
        return "Error: Only read-only `SELECT` or `WITH` queries are permitted."
    cur = conn.cursor()
    cur.execute(sql_clean)
    rows = cur.fetchall()
    if not rows:
        return "Query returned 0 rows."
    cols = rows[0].keys()
    out = [
        f"### Custom SQL Results ({min(len(rows), limit)} of {len(rows)} rows)",
        "| " + " | ".join(cols) + " |",
        "| " + " | ".join(":---" for _ in cols) + " |",
    ]
    for r in rows[:limit]:
        out.append("| " + " | ".join(str(r[c]).replace("|", "\\|").replace("\n", " ") for c in cols) + " |")
    return "\n".join(out)


def sql_concordance_query(
    mode: str = "interlinear",
    reference: str = "",
    lemma_id: str = "",
    sql_query: str = "",
    testament: str = "all",
    limit: int = 25,
) -> str:
    conn = get_conn()
    try:
        m = mode.lower().strip()
        if m == "interlinear":
            return query_interlinear(conn, reference, testament)
        elif m == "lemma":
            return query_lemma_concordance(conn, lemma_id, testament, limit)
        elif m == "lxx_bridge":
            return query_lxx_bridge(conn, lemma_id, limit)
        elif m == "custom_sql":
            return query_custom_sql(conn, sql_query, limit)
        else:
            return f"Unknown mode '{mode}'. Valid modes: 'interlinear', 'lemma', 'lxx_bridge', 'custom_sql'."
    finally:
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Biblical Philological Engine CLI")
    sub = parser.add_subparsers(dest="cmd")

    p_vec = sub.add_parser("vector", help="Concept-to-Lemma lookup")
    p_vec.add_argument("query", type=str)
    p_vec.add_argument("--lang", type=str, default="all")
    p_vec.add_argument("--n", type=int, default=8)

    p_sql = sub.add_parser("sql", help="SQL Concordance & Interlinear lookup")
    p_sql.add_argument("--mode", type=str, required=True, choices=["interlinear", "lemma", "lxx_bridge", "custom_sql"])
    p_sql.add_argument("--ref", type=str, default="")
    p_sql.add_argument("--lemma", type=str, default="")
    p_sql.add_argument("--query", type=str, default="")
    p_sql.add_argument("--testament", type=str, default="all")
    p_sql.add_argument("--limit", type=int, default=25)

    args = parser.parse_args()
    if args.cmd == "vector":
        print(vector_concept_lookup(args.query, args.lang, args.n))
    elif args.cmd == "sql":
        print(sql_concordance_query(args.mode, args.ref, args.lemma, args.query, args.testament, args.limit))
    else:
        parser.print_help()
