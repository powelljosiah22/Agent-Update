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


# ---------------------------------------------------------------------------
# Canonical genre scheme (explicit + labeled so the classification itself is auditable).
# Christian (Protestant) ordering: Daniel -> Prophets, Lamentations -> Prophets.
# In the Hebrew Tanakh both sit in Ketuvim; outputs flag this.
# ---------------------------------------------------------------------------
GENRES = {
    "Torah": ["Gen", "Exod", "Lev", "Num", "Deut"],
    "Historical": ["Josh", "Judg", "Ruth", "1Sam", "2Sam", "1Kgs", "2Kgs", "1Chr", "2Chr", "Ezra", "Neh", "Esth"],
    "Wisdom/Poetry": ["Job", "Ps", "Prov", "Eccl", "Song"],
    "Prophets": ["Isa", "Jer", "Lam", "Ezek", "Dan", "Hos", "Joel", "Amos", "Obad", "Jonah", "Mic", "Nah", "Hab", "Zeph", "Hag", "Zech", "Mal"],
    "Gospels/Acts": ["Matt", "Mark", "Luke", "John", "Acts"],
    "Pauline": ["Rom", "1Cor", "2Cor", "Gal", "Eph", "Phil", "Col", "1Thess", "2Thess", "1Tim", "2Tim", "Titus", "Phlm"],
    "General Epistles": ["Heb", "Jas", "1Pet", "2Pet", "1John", "2John", "3John", "Jude"],
    "Apocalypse": ["Rev"],
}
BOOK_TO_GENRE = {b: g for g, bs in GENRES.items() for b in bs}
GENRE_NOTE = "*(Genre scheme: Protestant ordering — Daniel & Lamentations counted as Prophets; Tanakh places them in Ketuvim.)*"

_BOOK_TOTALS = None


def book_totals(conn) -> dict:
    """Word totals per canonical book (OT+NT) for length normalization. ~0.2s, cached per process."""
    global _BOOK_TOTALS
    if _BOOK_TOTALS is None:
        _BOOK_TOTALS = {r[1]: r[2] for r in conn.execute(
            "SELECT testament, book, COUNT(*) FROM corpus_words WHERE testament IN ('OT','NT') GROUP BY testament, book")}
    return _BOOK_TOTALS


def core_gloss(primary_glosses: str) -> str:
    """Strong's core gloss only. The '; BDB:' half is misaligned in thousands of Hebrew rows
    (e.g. H3 'green; BDB: father'), so it is never shown as a definition."""
    return (primary_glosses or "").split("; BDB:")[0].strip()


# Canonical Versification Shift Map (Hebrew MT / WLC <-> English Bibles)
MT_TO_ENG_SHIFTS = {
    "Eccl": lambda ch, v: (5, 1) if (ch == 4 and v == 17) else ((5, v + 1) if ch == 5 else None),
    "Mal": lambda ch, v: (4, v - 18) if (ch == 3 and 19 <= v <= 24) else None,
    "Joel": lambda ch, v: (2, v + 27) if ch == 3 else ((3, v) if ch == 4 else None),
    "Jonah": lambda ch, v: (1, 17) if (ch == 2 and v == 1) else ((2, v - 1) if (ch == 2 and 2 <= v <= 11) else None),
}

ENG_TO_MT_SHIFTS = {
    "Eccl": lambda ch, v: (4, 17) if (ch == 5 and v == 1) else ((5, v - 1) if (ch == 5 and 2 <= v <= 20) else None),
    "Mal": lambda ch, v: (3, v + 18) if ch == 4 else None,
    "Joel": lambda ch, v: (3, v - 27) if (ch == 2 and 28 <= v <= 32) else ((4, v) if ch == 3 else None),
    "Jonah": lambda ch, v: (2, 1) if (ch == 1 and v == 17) else ((2, v + 1) if ch == 2 else None),
}


def mt_to_eng_ref(book: str, ch: int, v: int):
    fn = MT_TO_ENG_SHIFTS.get(book)
    return fn(ch, v) if fn else None


def eng_to_mt_ref(book: str, ch: int, v: int):
    fn = ENG_TO_MT_SHIFTS.get(book)
    return fn(ch, v) if fn else None


def _lemma_where(lemmas):
    if isinstance(lemmas, str):
        lemmas = [l for l in re.split(r"[;,]+", lemmas) if l.strip()]
    lemmas = [unicodedata.normalize("NFC", l.strip()) for l in lemmas if l.strip()]
    ph = ",".join("?" for _ in lemmas)
    return f"(root_lemma IN ({ph}) OR strongs_id IN ({ph}))", lemmas + [l.upper() for l in lemmas]


def genre_dispersion(conn, lemmas, as_bar: bool = False) -> str:
    """Mechanical canonical spread over DISTINCT VERSES (not tokens), normalized per 10k words of each genre.
    Pure SQL arithmetic — the LLM cannot reweight it."""
    if isinstance(lemmas, str):
        lemmas = [l for l in re.split(r"[;,]+", lemmas) if l.strip()]
    where, params = _lemma_where(lemmas)
    rows = conn.execute(
        f"""SELECT book, COUNT(DISTINCT chapter || ':' || verse) AS v
            FROM corpus_words WHERE testament IN ('OT','NT') AND {where}
            GROUP BY book""", params).fetchall()
    totals = book_totals(conn)
    g_hits = {g: 0 for g in GENRES}
    g_words = {g: sum(totals.get(b, 0) for b in bs) for g, bs in GENRES.items()}
    per_book = []
    for r in rows:
        g = BOOK_TO_GENRE.get(r["book"])
        if g:
            g_hits[g] += r["v"]
            per_book.append((r["book"], r["v"]))
    total = sum(g_hits.values())
    if total == 0:
        return "Canonical spread: 0 verses in OT/NT (LXX-only or not found)." if as_bar else "No OT/NT occurrences."
    if as_bar:
        return " | ".join(f"{g.split('/')[0][:6]} {round(100 * h / total)}%" for g, h in g_hits.items() if h)
    lines = [
        f"### Canonical Genre Dispersion — lemma cluster: `{', '.join(lemmas)}`",
        f"Total: **{total} distinct verses** in OT+NT (LXX excluded). {GENRE_NOTE}",
        "",
        "| Genre | Verses | % of hits | Rate per 10k words (length-normalized) |",
        "| :--- | :--- | :--- | :--- |",
    ]
    for g, h in g_hits.items():
        rate = (10000 * h / g_words[g]) if g_words[g] else 0
        lines.append(f"| {g} | {h} | {round(100 * h / total)}% | {rate:.2f} |")
    silent = [g for g, h in g_hits.items() if h == 0]
    if silent:
        lines.append(f"\n**Silent genres (0 hits for this cluster):** {', '.join(silent)} — any claim that these genres teach this concept must rest on OTHER lemmas or on inference, and must say so.")
    per_book.sort(key=lambda x: -x[1])
    lines.append("\n**Per-book (distinct verses):** " + ", ".join(f"{b} ({n})" for b, n in per_book[:20]) + (" ..." if len(per_book) > 20 else ""))
    return "\n".join(lines)


def _stem_variants(w: str) -> list:
    w_low = w.lower()
    variants = [w_low]
    for suffix in ("ity", "ities", "tion", "tions", "ness", "nesses", "ment", "ments", "ing", "ings", "ed", "able", "ful", "less", "ship", "s", "es"):
        if w_low.endswith(suffix) and len(w_low) - len(suffix) >= 3:
            base = w_low[:-len(suffix)]
            variants.append(base)
            if base.endswith("i"):
                variants.append(base[:-1] + "y")
            break
    cognates = {
        "generosity": ["generous", "liberal", "liberality", "bountiful"],
        "generous": ["generosity", "liberal", "bountiful"],
        "stewardship": ["steward", "dispensation"],
        "coercion": ["compulsion", "force", "necessity"],
        "enjoyment": ["enjoy", "pleasure"],
        "giving": ["give", "gift", "giver"],
        "taxation": ["tribute", "tax", "levy", "tithe"],
    }
    if w_low in cognates:
        variants.extend(cognates[w_low])
    return list(dict.fromkeys(variants))


def gloss_attestation(conn, query: str) -> str:
    """Data-driven emic/etic check: does each query word or its stem/cognates appear in Strong's CORE gloss
    of a lemma that occurs >=3 times in OT/NT? Guards against Barr's Lexicalization Fallacy."""
    stop = {"the", "and", "for", "with", "from", "that", "this", "what", "does", "say", "about", "how",
            "should", "bible", "biblical", "god", "into", "unto", "over", "vs", "versus"}
    words = [w for w in re.findall(r"[A-Za-z]{3,}", query) if w.lower() not in stop]
    if not words:
        return ""
    out = []
    for w in words:
        w_low = w.lower()
        # 1. Exact match in core gloss
        n_exact = conn.execute(
            """SELECT COUNT(*) FROM lexicon_entries le
               WHERE (' ' || LOWER(REPLACE(REPLACE(SUBSTR(le.primary_glosses, 1,
                        CASE WHEN INSTR(le.primary_glosses, '; BDB:') > 0 THEN INSTR(le.primary_glosses, '; BDB:') ELSE 400 END),
                        ',', ' '), ';', ' ')) || ' ') LIKE ?
                 AND EXISTS (SELECT 1 FROM lemma_counts lc WHERE lc.key_id = le.lemma_id AND lc.testament IN ('OT','NT') AND lc.cnt >= 3)""",
            (f"% {w_low} %",)).fetchone()[0]
        if n_exact:
            out.append(f"`{w}` → gloss-attested ({n_exact} lemma{'s' if n_exact != 1 else ''})")
            continue

        # 2. Stem / cognate match
        variants = _stem_variants(w_low)[1:]
        matched_var = None
        n_var = 0
        for var in variants:
            c = conn.execute(
                """SELECT COUNT(*) FROM lexicon_entries le
                   WHERE (' ' || LOWER(REPLACE(REPLACE(SUBSTR(le.primary_glosses, 1,
                            CASE WHEN INSTR(le.primary_glosses, '; BDB:') > 0 THEN INSTR(le.primary_glosses, '; BDB:') ELSE 400 END),
                            ',', ' '), ';', ' ')) || ' ') LIKE ?
                     AND EXISTS (SELECT 1 FROM lemma_counts lc WHERE lc.key_id = le.lemma_id AND lc.testament IN ('OT','NT') AND lc.cnt >= 3)""",
                (f"% {var} %",)).fetchone()[0]
            if c:
                matched_var = var
                n_var = c
                break
        if matched_var:
            out.append(f"`{w}` → stem/cognate-attested via `{matched_var}` ({n_var} lemma{'s' if n_var != 1 else ''})")
        else:
            out.append(f"`{w}` → **NO direct Strong's gloss match (test idioms & semantic domain)**")

    res = "**Gloss Attestation (emic/etic check):** " + "; ".join(out) + \
          "\n*(⚠️ Lexicalization Warning: Absence of an exact 19th-c. English abstract noun in Strong's does NOT prove the concept or idiom is absent [Barr's Lexical Fallacy; e.g. Hebrew 'good eye' / טוֹב־עַיִן in Prov 22:9 and Matt 20:15 denotes generosity]. Test semantic domains and idioms before asserting a concept is etic.)*"
    return res


def verify_claims(conn, claims: str) -> str:
    """Evidence ledger check. Input: 'Luke 12:33=πωλέω; 2Cor 8:13=G2471; Deut 14:26=H183'.
    Confirms the lemma/Strong's actually occurs in that verse, catching hallucinated citations."""
    out = ["### Claim Verification Ledger", "", "| Claim | Status | Found in verse |", "| :--- | :--- | :--- |"]
    for part in [p.strip() for p in claims.split(";") if p.strip()]:
        if "=" not in part:
            out.append(f"| {part} | ⚠️ malformed (use Ref=lemma) | - |")
            continue
        ref, lem = [x.strip() for x in part.split("=", 1)]
        try:
            book, ch, vs, ve = parse_reference(ref)
        except ValueError as e:
            out.append(f"| {part} | ⚠️ {e} | - |")
            continue
        lemN = unicodedata.normalize("NFC", lem)

        # Check direct reference
        hit = conn.execute(
            """SELECT testament, book, chapter, verse, surface_text, root_lemma, strongs_id, morph_decoded FROM corpus_words
               WHERE book=? AND chapter=? AND verse BETWEEN ? AND ? AND testament IN ('OT','NT')
                 AND (root_lemma=? OR strongs_id=? OR normalized_text=? OR surface_text LIKE ?)""",
            (book, ch, vs, ve, lemN, lemN.upper(), lemN, f"%{lemN}%")).fetchone()

        shift_note = ""
        if not hit and vs == ve:
            mt_target = eng_to_mt_ref(book, ch, vs)
            if mt_target:
                hit = conn.execute(
                    """SELECT testament, book, chapter, verse, surface_text, root_lemma, strongs_id, morph_decoded FROM corpus_words
                       WHERE book=? AND chapter=? AND verse=? AND testament='OT'
                         AND (root_lemma=? OR strongs_id=? OR normalized_text=? OR surface_text LIKE ?)""",
                    (book, mt_target[0], mt_target[1], lemN, lemN.upper(), lemN, f"%{lemN}%")).fetchone()
                if hit:
                    shift_note = f" (verified via MT {book} {mt_target[0]}:{mt_target[1]} [= Eng {ch}:{vs}])"

        if hit:
            out.append(f"| {part} | ✅ verified{shift_note} | {hit['surface_text']} (`{hit['root_lemma']}`/{hit['strongs_id'] or '-'}; {hit['morph_decoded'] or '-'}) |")
        else:
            out.append(f"| {part} | ❌ NOT FOUND — remove or mark (unverified) | - |")
    return "\n".join(out)


def parse_reference(ref_str: str):
    """Parses a single reference like 'Gen 1:1', 'Gen.1.1-3', '1 Cor 13:4-7', 'Rom 3:21-26'."""
    spans = parse_references(ref_str)
    if not spans:
        raise ValueError(f"Could not parse scripture reference: '{ref_str}'.")
    return spans[0]


def parse_references(ref_str: str):
    """
    Parses single or batch scripture references separated by semicolons or commas.
    Examples:
      - 'Gen 1:1'
      - '2Cor 8:2-3, 12-14'
      - '2Cor 9:7; 1Cor 16:2; Deut 14:22-26, 28-29; Luke 12:15, 21, 33'
    Returns list of (book, chapter, v_start, v_end) tuples.
    """
    spans = []
    cur_book = None
    cur_chapter = None

    # Split on semicolons or commas
    raw_parts = [p.strip() for p in re.split(r"[;,]+", ref_str.strip()) if p.strip()]
    for part in raw_parts:
        s = part.replace(".", " ").strip()
        # Case 1: Full reference with book and chapter (and optional verse range): '1 Cor 16:1-2' or 'Deut 14'
        m_full = re.match(r"^([1-3]?\s*[A-Za-z]+)\s+(\d+)(?:[:\s](\d+)(?:\s*[-–—]\s*(\d+))?)?$", s)
        if m_full:
            raw_book = re.sub(r"\s+", "", m_full.group(1)).lower()
            cur_book = BOOK_ALIASES.get(raw_book, m_full.group(1).strip())
            cur_chapter = int(m_full.group(2))
            v_start = int(m_full.group(3)) if m_full.group(3) else 1
            v_end = int(m_full.group(4)) if m_full.group(4) else (v_start if m_full.group(3) else 999)
            spans.append((cur_book, cur_chapter, v_start, v_end))
            continue

        # Case 2: Chapter:verse-verse inheriting cur_book (e.g., '9:7' after '2Cor 8:12')
        m_ch_v = re.match(r"^(\d+)[:\s](\d+)(?:\s*[-–—]\s*(\d+))?$", s)
        if m_ch_v and cur_book:
            cur_chapter = int(m_ch_v.group(1))
            v_start = int(m_ch_v.group(2))
            v_end = int(m_ch_v.group(3)) if m_ch_v.group(3) else v_start
            spans.append((cur_book, cur_chapter, v_start, v_end))
            continue

        # Case 3: Verse or verse range inheriting cur_book and cur_chapter (e.g., '12-14' or '21' after '2Cor 8:2-3')
        m_v_only = re.match(r"^(\d+)(?:\s*[-–—]\s*(\d+))?$", s)
        if m_v_only and cur_book and cur_chapter is not None:
            v_start = int(m_v_only.group(1))
            v_end = int(m_v_only.group(2)) if m_v_only.group(2) else v_start
            spans.append((cur_book, cur_chapter, v_start, v_end))
            continue

        raise ValueError(
            f"Could not parse scripture reference segment '{part}' in '{ref_str}'. "
            "Expected format like 'Gen 1:1', '2Cor 8:2-3, 12-14', or '2Cor 9:7; 1Cor 16:2'."
        )

    return spans


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

    # 1. Exact/Lexical match in SQLite first (handles Strong's IDs, transliterations, Greek/Hebrew words, and per-token primary glosses)
    q_clean = unicodedata.normalize("NFC", query.strip())
    STOPWORDS = {"the", "and", "for", "with", "from", "that", "this", "what", "does", "say", "about", "how", "should", "into", "unto"}
    tokens = [t for t in re.split(r"[\s,;:/]+", q_clean) if len(t) >= 3 and t.lower() not in STOPWORDS]
    if not tokens:
        tokens = [q_clean]

    lang_clause = ""
    if language_filter and language_filter.lower() in ("hebrew", "aramaic", "greek"):
        lang_clause = f" AND LOWER(language) = '{language_filter.lower()}'"

    # 1A. Direct ID / Word / Transliteration / Full-Phrase match
    cur.execute(
        f"""
        SELECT lemma_id, strongs_id, language, original_word, transliteration, primary_glosses, idiomatic_notes
        FROM lexicon_entries
        WHERE (lemma_id = ? OR strongs_id = ? OR original_word = ? OR LOWER(transliteration) = LOWER(?) OR LOWER(primary_glosses) LIKE LOWER(?))
        {lang_clause}
        LIMIT 30
        """,
        (q_clean, q_clean.upper(), q_clean, q_clean, f"%{q_clean}%"),
    )
    rows_pool = {r["lemma_id"]: dict(r) for r in cur.fetchall()}

    # 1B. Per-token primary_glosses search across BOTH Hebrew and Greek (with token specificity / IDF weighting)
    token_doc_freq = {}
    for tok in tokens[:6]:
        cur.execute(
            "SELECT COUNT(*) as c FROM lexicon_entries WHERE LOWER(primary_glosses) LIKE LOWER(?)",
            (f"%{tok}%",),
        )
        token_doc_freq[tok.lower()] = max(1, cur.fetchone()["c"])
        for lang_sub in (["Hebrew", "Aramaic", "Greek"] if not lang_clause else [language_filter.capitalize()]):
            cur.execute(
                """
                SELECT lemma_id, strongs_id, language, original_word, transliteration, primary_glosses, idiomatic_notes
                FROM lexicon_entries
                WHERE language = ? AND LOWER(primary_glosses) LIKE LOWER(?)
                LIMIT 30
                """,
                (lang_sub, f"%{tok}%"),
            )
            for r in cur.fetchall():
                rows_pool.setdefault(r["lemma_id"], dict(r))

    for lid, row in rows_pool.items():
        score = 5.0
        pg_lower = (row["primary_glosses"] or "").lower()
        notes_lower = (row["idiomatic_notes"] or "").lower()
        # Extract the core gloss before '; BDB:' to prioritize the primary definition over long BDB/KJV sub-lists
        cg = pg_lower.split("; bdb:")[0]

        if q_clean.lower() in (row["lemma_id"].lower(), (row["strongs_id"] or "").lower(), row["original_word"].lower(), (row["transliteration"] or "").lower()):
            score += 60.0
        if re.search(rf"\b{re.escape(q_clean.lower())}\b", cg):
            score += 35.0
        # NOTE: BDB half of primary_glosses is misaligned in ~70% of Hebrew entries (audit 2026-11-04);
        # scoring uses ONLY the Strong's core gloss to avoid false matches (e.g. H802 'woman; BDB: offering by fire').

        matched_tokens = 0
        for tok in tokens:
            tl = tok.lower()
            df = token_doc_freq.get(tl, 50)
            # Specific terms (e.g. 'tithe' df~5) get up to +28 bonus; broad terms ('offering' df~150) get +10
            idf_mult = max(0.6, min(1.8, 12.0 / (df ** 0.35)))
            if re.search(rf"\b{re.escape(tl)}\b", cg):
                score += 18.0 * idf_mult
                matched_tokens += 1
            elif re.search(rf"\b{re.escape(tl)}[a-z]*\b", cg):
                score += 12.0 * idf_mult
                matched_tokens += 1
            elif re.search(rf"\b{re.escape(tl)}\b", notes_lower):
                score += 2.5
        if matched_tokens > 1:
            score += matched_tokens * 6.0

        candidates[lid] = {"row": row, "score": score, "source": "lexical+vector"}

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
                facets = [f.strip() for f in re.split(r"[;|]", query) if f.strip()]
                if not facets:
                    facets = [query]
                res = coll.query(query_texts=facets, n_results=max(n_results * 2, 12), where=where_filter)
                if res and res.get("metadatas"):
                    for facet_meta, facet_dist in zip(res["metadatas"], res["distances"]):
                        for rank, (meta, dist) in enumerate(zip(facet_meta, facet_dist)):
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
    ranked = sorted(candidates.values(), key=lambda x: x["score"], reverse=True)[: max(n_results * 8, 60)]
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
        canon_occ = counts.get("OT", 0) + counts.get("NT", 0)
        if canon_occ > 0:
            item["score"] += 12.0 + min(10.0, (canon_occ ** 0.22) * 1.8)
        elif total_occ > 0:
            item["score"] += min(4.0, (total_occ ** 0.2) * 1.0)
        else:
            item["score"] -= 15.0
        item["counts"] = counts
        item["total_occ"] = total_occ
        results_out.append(item)

    results_out.sort(key=lambda x: x["score"], reverse=True)

    # Guarantee balanced OT (Hebrew/Aramaic) and NT/LXX (Greek) representation when language_filter == 'all'
    if (not language_filter or language_filter.lower() == "all") and n_results >= 4:
        heb_items = [x for x in results_out if x["row"]["language"] in ("Hebrew", "Aramaic") and x["counts"].get("OT", 0) > 0]
        grk_items = [x for x in results_out if x["row"]["language"] == "Greek" and x["counts"].get("NT", 0) > 0]
        if heb_items and grk_items:
            half = n_results // 2
            selected = []
            seen_ids = set()
            for x in heb_items[:half] + grk_items[:half]:
                selected.append(x)
                seen_ids.add(x["row"]["lemma_id"])
            for x in results_out:
                if len(selected) >= n_results:
                    break
                if x["row"]["lemma_id"] not in seen_ids:
                    selected.append(x)
                    seen_ids.add(x["row"]["lemma_id"])
            results_out = sorted(selected, key=lambda x: x["score"], reverse=True)
        else:
            results_out = results_out[:n_results]
    else:
        results_out = results_out[:n_results]

    lines = [
        f"### Concept-to-Lemma Router Results for: `{query}`",
        gloss_attestation(conn, query),
        "",
        "| Rank | Lemma ID | Strong's | Language | Original | Transliteration | Core Gloss (Strong's) | Occurrences (OT / LXX / NT) | Genre Spread (distinct verses) | Top Books |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ]
    for idx, item in enumerate(results_out, start=1):
        r = item["row"]
        c = item["counts"]
        lid = r["lemma_id"]
        sid = r["strongs_id"] or ""
        occ_str = f"**{item['total_occ']}** (OT: {c.get('OT', 0)}, LXX: {c.get('LXX', 0)}, NT: {c.get('NT', 0)})"

        # Fetch top books across OT and NT to expose full canonical spread (anti-prooftexting heatmap)
        cur.execute(
            """
            SELECT testament, book, COUNT(*) as cnt
            FROM corpus_words
            WHERE (root_lemma = ? OR (strongs_id = ? AND ? != ''))
              AND testament IN ('OT', 'NT')
            GROUP BY testament, book
            ORDER BY cnt DESC
            LIMIT 6
            """,
            (lid, sid, sid),
        )
        top_books = [f"{b['book']} ({b['cnt']})" for b in cur.fetchall()]
        books_str = ", ".join(top_books) if top_books else "-"

        lines.append(
            f"| {idx} | `{r['lemma_id']}` | `{r['strongs_id'] or '-'}` | {r['language']} | **{r['original_word']}** | *{r['transliteration']}* | {core_gloss(r['primary_glosses'])[:90]} | {occ_str} | {genre_dispersion(conn, [lid] + ([sid] if sid else []), as_bar=True)} | {books_str} |"
        )

    lines.append("\n*Next step: run `sql --mode dispersion --lemma \"<cluster of relevant IDs above>\"` and choose anchor + counter-weight passages FROM the dispersion output, not from memory.*")

    # Cross-Testament Semantic Anchor check
    q_low = query.lower()
    if any(k in q_low for k in ("tithe", "give", "giving", "steward", "money", "wealth", "possession", "alms", "enjoy", "pleasure")):
        lines.append("\n> 💡 **Cross-Testament Cluster Guide (Giving & Wealth):** Balance terms across canonical divisions to avoid false silence: (1) Torah/Hist agrarian dues (`H4643` ma'aser, `H8641` terumah); (2) Gospels/Acts charity & renunciation (`G1654` eleēmosynē, `G2344` thēsauros, `G4453` pōleō); (3) Pauline partnership & liberality (`G2842` koinōnia, `G572` haplotēs, `G2130` eumetadotos); (4) Wisdom enjoyment (`H7980` shalaṭ, `G619` apolausis). Include anchors from each division in your Step 2 dispersion cluster.")
    elif any(k in q_low for k in ("tax", "tribute", "ruler", "king", "state", "govern", "magistrat")):
        lines.append("\n> 💡 **Cross-Testament Cluster Guide (Civil Governance & Taxation):** Balance terms across canonical divisions: (1) Torah judicial equity & kingly limits (`H4941` mishpat, `Deut 17:16-17`); (2) Historical royal conscription & tribute (`H3947` laqach, `H4522` mas); (3) Gospels civic dues & supreme allegiance (`G2778` kēnsos, `Matt 22:21`); (4) Epistles magistracy & tribute (`G1849` exousia, `G5411` phoros, `G3011` leitourgos). Include anchors from each division in your Step 2 dispersion cluster.")

    lines.append("\n#### Detailed Lexical & Idiomatic Notes (Top Matches)")
    for item in results_out[:5]:
        r = item["row"]
        notes = (r["idiomatic_notes"] or "")[:450]
        lines.append(f"- **`{r['lemma_id']}` ({r['original_word']} / *{r['transliteration']}*)**: {notes}")

    conn.close()
    return "\n".join(lines)


def shorten_morph(md: str) -> str:
    """Scholarly concise morphology encoding to ensure batch interlinears fit inline (<8KB)."""
    if not md:
        return "-"
    s = md
    s = s.replace("Conjunction + ", "+").replace("Preposition + ", "+")
    s = s.replace("Particle Definite Article + ", "+Art+").replace("Particle Direct Object Marker (et)", "et")
    s = s.replace(" + Suffix Pronominal Suffix ", "+Sfx-")
    s = re.sub(r"Verb\s+([A-Za-z]+)\s+(?:Sequential\s+)?(Perf|Impf|Imperative|Infinitive|Participle)\s*(?:\([A-Za-z]+\))?", r"V-\1-\2", s)
    s = s.replace("1st Person", "1").replace("2nd Person", "2").replace("3rd Person", "3")
    s = s.replace("Masculine", "m").replace("Feminine", "f").replace("Both", "c").replace("Common", "c")
    s = s.replace("Singular", "s").replace("Plural", "p").replace("Dual", "d")
    s = s.replace("Absolute", "Abs").replace("Construct", "Cst")
    s = s.replace("Noun Common", "N-c").replace("Noun Proper", "N-pr").replace("Adjective Adjective", "Adj")
    s = s.replace("Pronoun Personal", "Pron-pers").replace("Particle Negative", "Neg")
    return re.sub(r"\s+", " ", s).strip()


def _query_single_interlinear(conn: sqlite3.Connection, book: str, ch: int, v_start: int, v_end: int, testament: str = "all", compact: bool = False) -> str:
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
               cw.pos, cw.morph_code, cw.morph_decoded, cw.english_gloss,
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
        return f"No words found for `{book} {ch}:{v_start}-{v_end}`."

    out = [f"### Interlinear & Morphological Breakdown: `{book} {ch}:{v_start}`" + (f"-`{v_end}`" if v_end != v_start and v_end < 900 else "")]
    grouped = {}
    for r in rows:
        key = (r["testament"], r["book"], r["chapter"], r["verse"])
        grouped.setdefault(key, []).append(r)

    total_verses = len({(b, c, v) for (_, b, c, v) in grouped.keys()})
    use_compact = compact or total_verses > 3

    for (test, b, c, v), w_rows in grouped.items():
        full_surface = " ".join(r["surface_text"] for r in w_rows)
        # In batch mode, skip redundant LXX parallel on OT verses to prevent runner truncation spills
        if use_compact and test == "LXX" and (not testament or testament.lower() in ("all", "ot")):
            continue

        header_ref = f"{b} {c}:{v}"
        if test == "OT":
            eng_v = mt_to_eng_ref(b, c, v)
            if eng_v:
                header_ref += f" (English Bibles: {b} {eng_v[0]}:{eng_v[1]})"
        out.append(f"\n#### [{test}] {header_ref}")
        out.append(f"> **Original:** {full_surface}")
        if use_compact:
            tokens_fmt = []
            for r in w_rows:
                pos_clean = (r["pos"] or "").rstrip("-")
                is_func = pos_clean in ("P", "RA", "C", "PREP", "CONJ", "PRT", "RP", "RD", "RI", "RR", "R", "D", "X") or r["root_lemma"] in ("ὁ", "καί", "ἐν", "εἰς", "δέ", "γάρ", "αὐτός", "οὗτος", "ὅτι", "οὐ", "μή", "ἐκ", "ἀπό", "πρός", "σύν", "τά", "σύ", "ἐγώ", "ὅς", "εἰμί", "H853", "H3588", "H834", "H3651", "H5921", "H413")
                if is_func:
                    continue
                gloss = (r["english_gloss"] or (r["primary_glosses"].split(",")[0] if r["primary_glosses"] else "-")).split(",")[0][:18]
                sid = r["strongs_id"] if r["strongs_id"] and r["strongs_id"] != r["root_lemma"] else ""
                lemma_tag = f"{r['root_lemma']}" + (f"/{sid}" if sid else "")
                md = shorten_morph(r["morph_decoded"])
                tokens_fmt.append(
                    f"**{r['surface_text']}**(`{lemma_tag}` [{md}]:\"{gloss}\")"
                )
            out.append(" · ".join(tokens_fmt))
        else:
            out.append("| # | Surface | Transliteration | Root Lemma | Strong's | Morph Code | Decoded Grammar | Mechanical Gloss |")
            out.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
            for r in w_rows:
                gloss = r["english_gloss"] or (r["primary_glosses"].split(",")[0] if r["primary_glosses"] else "-")
                out.append(
                    f"| {r['word_index']} | **{r['surface_text']}** | *{r['transliteration'] or '-'}* | `{r['root_lemma']}` | `{r['strongs_id'] or '-'}` | `{r['morph_code']}` | {r['morph_decoded'] or '-'} | {gloss} |"
                )

    return "\n".join(out)


def query_interlinear(conn: sqlite3.Connection, reference: str, testament: str = "all") -> str:
    spans = parse_references(reference)
    compact = len(spans) > 1 or sum(max(1, min(20, v_e - v_s + 1)) for _, _, v_s, v_e in spans) > 3
    sections = []
    for book, ch, v_start, v_end in spans:
        sections.append(_query_single_interlinear(conn, book, ch, v_start, v_end, testament, compact=compact))
    return "\n\n---\n\n".join(sections)


def query_lemma_concordance(conn: sqlite3.Connection, lemma_id: str, testament: str = "all", limit: int = 25) -> str:
    lemmas = [l.strip() for l in re.split(r"[;,]+", lemma_id.strip()) if l.strip()]
    if len(lemmas) > 1:
        per_limit = max(8, limit // len(lemmas))
        return "\n\n---\n\n".join(_query_single_lemma_concordance(conn, l, testament, per_limit) for l in lemmas)
    return _query_single_lemma_concordance(conn, lemma_id, testament, limit)


def _query_single_lemma_concordance(conn: sqlite3.Connection, lemma_id: str, testament: str = "all", limit: int = 25) -> str:
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
            out.append(f"- **Core Gloss (Strong's):** {core_gloss(lr['primary_glosses'])}  *(BDB half suppressed: alignment unreliable in this DB)*")
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
    # Stratified round-robin sampling: every book containing the lemma gets a sample before any book gets a second,
    # so long books (Psalms, Jeremiah, Luke-Acts) cannot crowd out minority canonical voices.
    by_book = {}
    for o in all_occ:
        by_book.setdefault((o["testament"], o["book"]), []).append(o)
    sampled, depth = [], 0
    while len(sampled) < limit and any(len(v) > depth for v in by_book.values()):
        for v in by_book.values():
            if len(v) > depth and len(sampled) < limit:
                sampled.append(v[depth])
        depth += 1

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
        elif m == "dispersion":
            return genre_dispersion(conn, [l for l in re.split(r"[;,]+", lemma_id) if l.strip()])
        elif m == "verify":
            return verify_claims(conn, sql_query or reference)
        else:
            return f"Unknown mode '{mode}'. Valid modes: 'interlinear', 'lemma', 'lxx_bridge', 'custom_sql', 'dispersion', 'verify'."
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
    p_sql.add_argument("--mode", type=str, required=True, choices=["interlinear", "lemma", "lxx_bridge", "custom_sql", "dispersion", "verify"])
    p_sql.add_argument("--ref", type=str, default="")
    p_sql.add_argument("--lemma", type=str, default="")
    p_sql.add_argument("--query", type=str, default="")
    p_sql.add_argument("--claims", type=str, default="", help="For --mode verify: 'Luke 12:33=G4453; 2Cor 8:13=ἰσότης'")
    p_sql.add_argument("--testament", type=str, default="all")
    p_sql.add_argument("--limit", type=int, default=25)

    args = parser.parse_args()
    if args.cmd == "vector":
        print(vector_concept_lookup(args.query, args.lang, args.n))
    elif args.cmd == "sql":
        print(sql_concordance_query(args.mode, args.ref, args.lemma, args.claims or args.query, args.testament, args.limit))
    else:
        parser.print_help()
